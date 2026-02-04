import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
import sys
import os

# Add project cocotb directory to path
sys.path.insert(0, os.path.join(r"{PROJECT_ROOT}", "tb", "cocotb"))
from qspi_memory_utils import load_bin_file, read_word_from_memory, test_spi_memory

bin_file = r"{BIN_FILE}"
begin_addr = {BEGIN_ADDR}
end_addr = {END_ADDR}
begin_byte_addr = {BEGIN_BYTE_ADDR}
end_byte_addr = {END_BYTE_ADDR}
tohost_byte_addr = {TOHOST_BYTE_ADDR}
sig_file = r"{SIG_FILE}"

@cocotb.test()
async def test_riscof_signature(dut):
    """RISCOF test to extract signature from memory"""
    
    # Load bin file into memory
    memory = load_bin_file(bin_file)
    
    max_cycles = 2000000
    cycles_after_completion = 0
    found_completion = False
    tohost_initial_value = None
    
    # Get initial tohost value if address is known
    if tohost_byte_addr is not None:
        tohost_initial_value = read_word_from_memory(memory, tohost_byte_addr)
        print(f"Initial tohost value: 0x{{tohost_initial_value:08x}} at address 0x{{tohost_byte_addr:08x}}")
    else:
        tohost_initial_value = None
        print("Tohost address not available, will use ECALL detection as fallback")
    
    def callback(dut, memory):
        nonlocal cycles_after_completion, found_completion, tohost_initial_value

        if tohost_byte_addr is not None and tohost_initial_value is not None:
            current_tohost = read_word_from_memory(memory, tohost_byte_addr)
            if current_tohost != tohost_initial_value and current_tohost != 0:
                if not found_completion:
                    found_completion = True
                    cycles_after_completion = 1000  # Wait some cycles after tohost write
                    print(f"Found write to tohost: 0x{{current_tohost:08x}} at address 0x{{tohost_byte_addr:08x}}")
                    # print(f"PC: 0x{{int(dut.soc_inst.cpu_core.o_instr_addr.value):08x}}")

        if found_completion:
            cycles_after_completion -= 1
            if cycles_after_completion <= 0:
                # Extract signature from memory
                print(f"Extracting signature from 0x{{begin_addr:08x}} to 0x{{end_addr:08x}} (byte addr: 0x{{begin_byte_addr:08x}} to 0x{{end_byte_addr:08x}})")
                
                # Read signature from memory (memory is updated during simulation via test_spi_memory)
                signature = []
                addr = begin_byte_addr
                while addr < end_byte_addr:
                    # Read from memory array (which tracks writes during simulation)
                    word = read_word_from_memory(memory, addr)
                    signature.append(word)
                    addr += 4
                
                # Write signature file in RISCOF format (big-endian format for RISCOF)
                # RISCOF expects big-endian: bytes in memory should be written as MSB first
                # Memory stores little-endian, so we need to swap bytes
                with open(sig_file, 'w') as sigf:
                    for word in signature:
                        # Convert from little-endian (as stored in memory) to big-endian (RISCOF format)
                        # Swap bytes: 0x09a35c6f -> 0x6f5ca309
                        big_endian_word = ((word & 0xFF) << 24) | ((word & 0xFF00) << 8) | ((word & 0xFF0000) >> 8) | ((word & 0xFF000000) >> 24)
                        sigf.write(f"{{big_endian_word:08x}}" + chr(10))
                
                print(f"Signature written to {{sig_file}}")
                print(f"Signature size: {{len(signature)}} words")
                return True
        
        return False
    
    # Use test_spi_memory which tracks memory writes
    await test_spi_memory(dut, memory, max_cycles, callback)
    
    # If we didn't find completion signal, still try to extract signature
    if not found_completion:
        print(f"Warning: ECALL not found, extracting signature anyway from 0x{{begin_byte_addr:08x}} to 0x{{end_byte_addr:08x}}")
        signature = []
        addr = begin_byte_addr
        while addr < end_byte_addr:
            word = read_word_from_memory(memory, addr)
            signature.append(word)
            addr += 4
        
        with open(sig_file, 'w') as sigf:
            for word in signature:
                # Convert from little-endian to big-endian for RISCOF format
                big_endian_word = ((word & 0xFF) << 24) | ((word & 0xFF00) << 8) | ((word & 0xFF0000) >> 8) | ((word & 0xFF000000) >> 24)
                sigf.write(f"{{big_endian_word:08x}}" + chr(10))
        
        print(f"Signature written to {{sig_file}}")


import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
import random
import os
from test_utils import NOP_INSTR

FSM_IDLE = 0;
FSM_SEND_CMD_ADDR = 1;
FSM_DATA_TRANSFER = 2;
FSM_DONE_STATE = 3;

def load_hex_file(hex_file_path):
    """Load hex file and return byte-addressed memory array"""
    # Create byte-addressed memory (like RTL unified_mem)
    memory = bytearray(16 * 1024 * 1024)  # 16MB memory space
    
    if hex_file_path and os.path.exists(hex_file_path):
        with open(hex_file_path, 'r') as f:
            addr = 0x00000000
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        instr = int(line, 16)
                        # Store as little-endian bytes (matching RTL behavior)
                        memory[addr] = instr & 0xFF
                        memory[addr + 1] = (instr >> 8) & 0xFF
                        memory[addr + 2] = (instr >> 16) & 0xFF
                        memory[addr + 3] = (instr >> 24) & 0xFF
                        addr += 4
                    except ValueError:
                        print(f"Warning: Invalid hex line: {line}")
                        continue
        print(f"Loaded {(addr)//4} instructions from {hex_file_path}")
    else:
        print(f"Warning: Hex file not found or not specified: {hex_file_path}")
        # Fill with default NOP instructions
        for i in range(0, 16, 4):
            nop = NOP_INSTR
            memory[i] = nop & 0xFF
            memory[i + 1] = (nop >> 8) & 0xFF
            memory[i + 2] = (nop >> 16) & 0xFF
            memory[i + 3] = (nop >> 24) & 0xFF
    
    return memory

def read_word_from_memory(memory, addr):
    """Read a 32-bit word from byte-addressed memory (little-endian)"""
    return (memory[addr] | 
            (memory[addr + 1] << 8) | 
            (memory[addr + 2] << 16) | 
            (memory[addr + 3] << 24))

def write_word_to_memory(memory, addr, data):
    """Write a 32-bit word to byte-addressed memory (little-endian)"""
    memory[addr] = data & 0xFF
    memory[addr + 1] = (data >> 8) & 0xFF
    memory[addr + 2] = (data >> 16) & 0xFF
    memory[addr + 3] = (data >> 24) & 0xFF

def read_halfword_from_memory(memory, addr):
    """Read a 16-bit halfword from byte-addressed memory (little-endian)"""
    return memory[addr] | (memory[addr + 1] << 8)

def write_halfword_to_memory(memory, addr, data):
    """Write a 16-bit halfword to byte-addressed memory (little-endian)"""
    memory[addr] = data & 0xFF
    memory[addr + 1] = (data >> 8) & 0xFF

def read_byte_from_memory(memory, addr):
    """Read a 8-bit byte from byte-addressed memory"""
    return memory[addr]

def write_byte_to_memory(memory, addr, data):
    """Write a 8-bit byte to byte-addressed memory"""
    memory[addr] = data & 0xFF

async def test_spi_memory(dut, memory, max_cycles, callback):
    """Test the SPI memory"""

    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await Timer(15, units="ns")
    dut.rst_n.value = 1

    is_instr = False;
    command = 0x00;
    fsm_state = FSM_IDLE;
    bit_counter = 0
    addr = 0x00000000
    data = 0x00000000

    cycles = 0;

    dut.soc_inst.spi_miso.value = 0

    for _ in range(max_cycles):
        if fsm_state == FSM_IDLE:
            await FallingEdge(dut.clk)
            if dut.soc_inst.flash_cs_n.value == 0:
                is_instr = True;
                fsm_state = FSM_SEND_CMD_ADDR;
                bit_counter = 0;
                dut.soc_inst.spi_miso.value = 0
                addr = 0;
                data = 0;
            if dut.soc_inst.ram_cs_n.value == 0:
                is_instr = False;
                fsm_state = FSM_SEND_CMD_ADDR;
                bit_counter = 0;
                dut.soc_inst.spi_miso.value = 0
                addr = 0;
                data = 0;
        else:
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            if (is_instr == True and dut.soc_inst.flash_cs_n.value == 1) or (is_instr == False and dut.soc_inst.ram_cs_n.value == 1):
                # print(f"SPI1: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, addr=0x{addr:08x}, data=0x{data:08x}")
                if not is_instr and command == 0x02:
                    if bit_counter > 0:
                        mask = (1 << bit_counter) - 1
                        # valid_data = int.from_bytes(data.to_bytes(4, 'little'), 'big')
                        # valid_data = valid_data >> (32 - bit_counter)
                        valid_data = data & mask # Keep only bit_counter bits
                        print(f"Writing {bit_counter} bits to memory: addr=0x{addr:08x}, data=0x{valid_data:08x} (raw_data=0x{data:08x})")
                        
                        # Get existing data from memory
                        mem_addr = addr & 0x00FFFFFF
                        existing_data = read_word_from_memory(memory, mem_addr)
                        print(f"original data: 0x{existing_data:08x}")
                        
                        cleared_data = existing_data & (~mask)  # Clear the upper bit_counter bits
                        combined_data = cleared_data | valid_data  # Set the new bits at MSB
                        write_word_to_memory(memory, mem_addr, combined_data);
                        print(f"new data: 0x{combined_data:08x} (mask: 0x{mask:08x}, cleared: 0x{cleared_data:08x}, new bits: 0x{valid_data:08x})")
                # assert False, "SPI CSN is not active"
                fsm_state = FSM_IDLE;
                
            if fsm_state == FSM_SEND_CMD_ADDR:
                # await RisingEdge(dut.soc_inst.spi_sclk)
                if dut.soc_inst.spi_sclk.value == 1:
                    # print(f"SPI1: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.soc_inst.spi_sclk.value}, spi_miso={dut.soc_inst.spi_miso.value}, addr=0x{addr:08x}")
                    if dut.soc_inst.spi_sclk.value == 1:
                        addr = (addr << 1) | dut.soc_inst.spi_mosi.value;
                        bit_counter += 1;
                        if bit_counter == 32:
                            fsm_state = FSM_DATA_TRANSFER;
                            bit_counter = 0;
                            if is_instr:
                                print(f"Reading from instr memory: addr=0x{addr:08x}")
                                data = read_word_from_memory(memory, addr & 0x00FFFFFF);
                            else:
                                command = (addr >> 24) & 0xFF
                                if command == 0x03:
                                    print(f"Reading from data memory: addr=0x{addr:08x}")
                                    data = read_word_from_memory(memory, addr & 0x00FFFFFF);
                                    # Reverse the byte order
                                    data = int.from_bytes(data.to_bytes(4, 'little'), 'big')
                                    print(f"data: 0x{data:08x}")
                                else:
                                    print(f"Writing to data memory: addr=0x{addr:08x}")
                                    data = 0;
            else:
                if is_instr or (not is_instr and command == 0x03):
                    # await FallingEdge(dut.soc_inst.spi_sclk)
                    if dut.soc_inst.spi_sclk.value == 0:
                        # print(f"SPI2: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.soc_inst.spi_sclk.value}, spi_miso={dut.soc_inst.spi_miso.value}, addr=0x{addr:08x}")
                        if fsm_state == FSM_DATA_TRANSFER:
                            if dut.soc_inst.spi_sclk.value == 0:
                                # print(f"SPI MISO: bit_counter={bit_counter}, spi_miso={data & 1}, instr_data=0x{data:08x}")
                                dut.soc_inst.spi_miso.value = ((data & 0xFFFFFFFF) >> (31 - bit_counter)) & 1
                                bit_counter += 1;
                                if bit_counter == 32:
                                    fsm_state = FSM_DONE_STATE;
                        elif fsm_state == FSM_DONE_STATE:
                            fsm_state = FSM_IDLE;
                            if is_instr:
                                await RisingEdge(dut.soc_inst.flash_cs_n)
                            else:
                                await RisingEdge(dut.soc_inst.ram_cs_n)
                else:
                    # await RisingEdge(dut.soc_inst.spi_sclk)
                    if dut.soc_inst.spi_sclk.value == 0:
                        # print(f"SPI3: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.soc_inst.spi_sclk.value}, spi_miso={dut.soc_inst.spi_miso.value}, addr=0x{addr:08x}")
                        if fsm_state == FSM_DATA_TRANSFER:
                            data = (data << 1) | dut.soc_inst.spi_mosi.value;
                            bit_counter += 1;
                            if bit_counter == 32:
                                print(f"Write data: addr=0x{addr:08x}, data=0x{data:08x}")
                                write_word_to_memory(memory, addr & 0x00FFFFFF, data);
                                fsm_state = FSM_DONE_STATE;
                        elif fsm_state == FSM_DONE_STATE:
                            fsm_state = FSM_IDLE;

        if callback(dut, memory):
            return

    assert False, "Failed"

@cocotb.test()
async def test_spi_instr(dut):
    """Test the SPI instruction fetch"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1
        0x00000008: 0x00210113, # ADDI x2, x2, 2
        0x0000000C: 0x001101B3, # ADD x3, x2, x1
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
    }

    max_cycles = 10000;

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000030:
            registers = dut.soc_inst.cpu_core.register_file.registers
            assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_spi_data(dut):
    """Test the SPI data memory"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000093, # ADDI x1, x0, 0x300
        0x00000008: 0x12300113, # ADDI x2, x0, 0x123
        0x0000000C: 0x0220A023, # SW x2, 0x20(x1)
        0x00000010: 0x0200a183, # LW x3, 0x20(x1)
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
    }

    max_cycles = 4000;

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000030:
            registers = dut.soc_inst.cpu_core.register_file.registers
            assert registers[3].value == 0x123, f"Register x3 should be 0x123, got 0x{registers[3].value.integer:08x}"
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)



@cocotb.test()
async def test_sh(dut):
    """Test the SPI data memory"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000093, # ADDI x1, x0, 0x300
        0x00000008: 0x12300113, # ADDI x2, x0, 0x123
        0x0000000C: 0x00C11113, # SLLI x2, x2, 12
        0x00000010: 0x45610113, # ADDI x2, x2 0x456
        0x00000014: 0x02209023, # SH x2, 0x20(x1)
        0x00000018: 0x02009183, # LH x3, 0x20(x1)
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        
        0x00000320: 0x77778888,
    }

    max_cycles = 3000;

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000030:
            assert memory[0x00000320] == 0x77773456, f"Memory[0x00000320] should be 0x77773456, got 0x{memory[0x00000320]:08x}"
            registers = dut.soc_inst.cpu_core.register_file.registers
            assert registers[3].value == 0x3456, f"Register x3 should be 0x3456, got 0x{registers[3].value.integer:08x}"
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

@cocotb.test()
async def test_spi_hex_file(dut):
    """Test the SPI data memory using hex file"""

    # Get the hex file path from environment variable 
    # The makefile passes this via PLUSARGS which cocotb makes available as environment variable
    hex_file_path = os.environ.get('HEX_FILE', None)
    
    # Load memory from hex file
    memory = load_hex_file(hex_file_path)

    cycles = 0;

    max_cycles = 400000;

    def callback(dut, memory):
        nonlocal cycles
        if dut.soc_inst.cpu_core.instr_data == 0x00000073:
            cycles = 5 * 64;
            print(f"Intruction: 0x{int(dut.soc_inst.cpu_core.instr_data.value):08x}, PC: 0x{int(dut.soc_inst.cpu_core.instr_addr.value):08x}")
            print("Found ECALL instruction")
        if cycles > 0:
            cycles -= 1;
            if cycles == 0:
                print("Test finished, checking results")
                registers = dut.soc_inst.cpu_core.register_file.registers
                assert registers[10].value == 0, f"Register x10 should be 0, got 0x{registers[10].value.integer:08x}"
                return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

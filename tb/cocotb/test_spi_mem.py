import cocotb
import os
from test_utils import NOP_INSTR
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
    read_word_from_memory,
    load_bin_file,
)


@cocotb.test()
async def test_spi_instr(dut):
    """Test the SPI instruction fetch"""

    hex_memory = {
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
    memory = convert_hex_memory_to_byte_memory(hex_memory)

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

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x010000b7, # LUI x1, 0x1000
        0x00000008: 0x30008093, # ADDI x1, x1, 0x300
        0x0000000C: 0x12300113, # ADDI x2, x0, 0x123
        0x00000010: 0x0220A023, # SW x2, 0x20(x1)
        0x00000014: 0x0200a183, # LW x3, 0x20(x1)
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
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000;

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

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x010000b7, # LUI x1, 0x1000
        0x00000008: 0x30008093, # ADDI x1, x1, 0x300
        0x0000000C: 0x12300113, # ADDI x2, x0, 0x123
        0x00000010: 0x00C11113, # SLLI x2, x2, 12
        0x00000014: 0x45610113, # ADDI x2, x2 0x456
        0x00000018: 0x02209023, # SH x2, 0x20(x1)
        0x0000001C: 0x02009183, # LH x3, 0x20(x1)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        
        0x01000320: 0x77778888,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000;

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000030:
            mem_value = read_word_from_memory(memory, 0x01000320)
            assert mem_value == 0x56347777, f"Memory[0x01000320] should be 0x56347777, got 0x{mem_value:08x}"
            registers = dut.soc_inst.cpu_core.register_file.registers
            assert registers[3].value == 0x3456, f"Register x3 should be 0x3456, got 0x{registers[3].value.integer:08x}"
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

@cocotb.test()
async def test_spi_bin_file(dut):
    """Test the SPI data memory using bin file"""

    # Get the bin file path from environment variable 
    # The makefile passes this via PLUSARGS which cocotb makes available as environment variable
    bin_file_path = os.environ.get('BIN_FILE', None)
    
    # Load memory from bin file
    memory = load_bin_file(bin_file_path)

    cycles = 0;

    max_cycles = 4000000;

    def callback(dut, memory):
        nonlocal cycles
        if dut.soc_inst.cpu_core.instr_data.value == 0x00000073:
            cycles = 5 * 18;
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

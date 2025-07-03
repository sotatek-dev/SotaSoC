import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock
import random

# Constants
CYCLES_PER_INSTRUCTION = 8
NOP_INSTR = 0x00000013

async def do_test(dut, memory, cycles, mem_data=0x00000000):
    """Do test"""

    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    dut.instr_data.value = memory[0x80000000]
    dut.mem_data.value = mem_data

    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Execute for several cycles
    for _ in range(cycles):
        await RisingEdge(dut.clk)
        dut.instr_data.value = memory[dut.instr_addr.value.integer]
        # print(f"Cycle {_}: PC={dut.instr_addr.value.integer:08x}, Instr={memory[dut.instr_addr.value.integer]:08x}")

@cocotb.test()
async def test_jal(dut):
    """Test JAL (Jump and Link)"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x002080E3, # BEQ x1, x2, 0x1000 => Jump to 0x80001004
        0x80000008: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x8000000C: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000014: ADDI_INSTR,
        0x80000018: ADDI_INSTR,
        0x8000001C: ADDI_INSTR,
        0x80000800: ADDI_INSTR,
        0x80001004: 0x00210113, # ADDI x2, x2, 2 => it should be executed
        0x80001008: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x8000100C: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80001010: NOP_INSTR,
        0x80001014: NOP_INSTR,
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0, f"Register x1 should still be 0, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"


@cocotb.test()
async def test_beq_1(dut):
    """Test BEQ (Branch if Equal): jump"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x002080E3, # BEQ x1, x2, 0x800 => Jump to 0x80001004 = 0x80000004 + 0x800 * 2
        0x80000008: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x8000000C: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000014: ADDI_INSTR,
        0x80000018: ADDI_INSTR,
        0x8000001C: ADDI_INSTR,
        0x80001004: 0x00210113, # ADDI x2, x2, 2 => it should be executed
        0x80001008: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x8000100C: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80001010: NOP_INSTR,
        0x80001014: NOP_INSTR,
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0, f"Register x1 should still be 0, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_beq_2(dut):
    """Test BEQ (Branch if Equal): no jump"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00508093, # ADDI x1, x1, 5
        0x80000008: 0x002080E3, # BEQ x1, x2, 0x800 => Jump to 0x80001004 = 0x80000004 + 0x800 * 2
        0x8000000C: 0x00108093, # ADDI x1, x1, 0x01 => it should be executed
        0x80000010: 0x00208093, # ADDI x1, x1, 0x02
        0x80000014: 0x00408093, # ADDI x1, x1, 0x04
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80001004: NOP_INSTR,
        0x80001008: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x8000100C: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80001010: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80001014: NOP_INSTR,
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
    }
    await do_test(dut, memory, 15)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0xC, f"Register x1 should be 0xC, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 0, f"Register x2 should be 0, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_bne_1(dut):
    """Test BNE (Branch if Not Equal)"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00508093, # ADDI x1, x1, 5
        0x80000008: 0x002090E3, # BEQ x1, x2, 0x800 => Jump to 0x80001004 = 0x80000004 + 0x800 * 2
        0x8000000C: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR,
        0x8000001C: ADDI_INSTR,
        0x80001004: ADDI_INSTR,
        0x80001008: 0x00210113, # ADDI x2, x2, 2 => it should be executed
        0x8000100C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80001010: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80001014: NOP_INSTR,
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
    }
    await do_test(dut, memory, 15)

    registers = dut.core.register_file.registers
    assert registers[1].value == 5, f"Register x1 should be 5, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_bne_2(dut):
    """Test BNE (Branch if Not Equal)"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: NOP_INSTR,
        0x80000008: 0x002090E3, # BEQ x1, x2, 0x800 => Jump to 0x80001004 = 0x80000004 + 0x800 * 2
        0x8000000C: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR,
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x8000002C: ADDI_INSTR,
        0x80001004: ADDI_INSTR,
        0x80001008: 0x00210113, # ADDI x2, x2, 2 => it should be executed
        0x8000100C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80001010: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80001014: NOP_INSTR,
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
    }
    await do_test(dut, memory, 15)

    registers = dut.core.register_file.registers
    assert registers[1].value == 3, f"Register x1 should be 3, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 0, f"Register x2 should be 0, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_blt_1(dut):
    """Test BLT (Branch if Less Than, signed): jump when rs1 < rs2"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0xFFF08093, # ADDI x1, x1, -1 (signed)
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020C0E3, # BLT x1, x2, 0x800 => Jump to 0x80001004 (since -1 < 2)
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR, # ADDI x1, x1, 1
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x8000002C: ADDI_INSTR,
        0x80001008: NOP_INSTR,
        0x8000100C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80001010: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80001014: 0x00528293, # ADDI x5, x5, 5 => it should be executed
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
        0x80001030: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0xFFFFFFFF, f"Register x1 should be -1, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 5, f"Register x5 should be 5, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_blt_2(dut):
    """Test BLT (Branch if Less Than, signed): no jump when rs1 >= rs2"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00508093, # ADDI x1, x1, 5
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020C0E3, # BLT x1, x2, 0x800 => Should not jump (since 5 >= 2)
        0x80000010: 0x00108093, # ADDI x1, x1, 1 => it should be executed
        0x80000014: 0x00208093, # ADDI x1, x1, 2
        0x80000018: 0x00408093, # ADDI x1, x1, 4
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80001008: NOP_INSTR,
        0x8000100C: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x80001010: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80001014: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR, # NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0xC, f"Register x1 should be 0xC, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 0, f"Register x5 should be 0, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_bge_1(dut):
    """Test BGE (Branch if Greater or Equal, signed): jump when rs1 >= rs2"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00508093, # ADDI x1, x1, 5
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020D0E3, # BGE x1, x2, 0x800 => Jump to 0x80001004 (since 5 >= 2)
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR, # ADDI x1, x1, 1
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x8000002C: ADDI_INSTR,
        0x80001008: NOP_INSTR,
        0x8000100C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80001010: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80001014: 0x00528293, # ADDI x5, x5, 5 => it should be executed
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
        0x80001030: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 5, f"Register x1 should be 5, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 5, f"Register x5 should be 5, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_bge_2(dut):
    """Test BGE (Branch if Greater or Equal, signed): no jump when rs1 < rs2"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0xFFF08093, # ADDI x1, x1, -1 (signed)
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020D0E3, # BGE x1, x2, 0x800 => Should not jump (since -1 < 2)
        0x80000010: 0x00108093, # ADDI x1, x1, 1 => it should be executed
        0x80000014: 0x00208093, # ADDI x1, x1, 2
        0x80000018: 0x00408093, # ADDI x1, x1, 4
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80001008: NOP_INSTR,
        0x8000100C: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x80001010: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80001014: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
        0x80001030: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 6, f"Register x1 should be 6, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 0, f"Register x5 should be 0, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_bltu_1(dut):
    """Test BLTU (Branch if Less Than, unsigned): jump when rs1 < rs2"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020E0E3, # BLTU x1, x2, 0x800 => Jump to 0x80001004 (since 1 < 2)
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR, # ADDI x1, x1, 1
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x80001008: NOP_INSTR,
        0x8000100C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80001010: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80001014: 0x00528293, # ADDI x5, x5, 5 => it should be executed
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
        0x80001030: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 1, f"Register x1 should be 1, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 5, f"Register x5 should be 5, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_bltu_2(dut):
    """Test BLTU (Branch if Less Than, unsigned): no jump when rs1 >= rs2"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00508093, # ADDI x1, x1, 5
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020E0E3, # BLTU x1, x2, 0x800 => Should not jump (since 5 >= 2)
        0x80000010: 0x00108093, # ADDI x1, x1, 1 => it should be executed
        0x80000014: 0x00208093, # ADDI x1, x1, 2
        0x80000018: 0x00408093, # ADDI x1, x1, 4
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80001004: NOP_INSTR,
        0x8000100C: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x80001010: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80001014: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
        0x80001030: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0xC, f"Register x1 should be 0xC, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 0, f"Register x5 should be 0, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_bgeu_1(dut):
    """Test BGEU (Branch if Greater or Equal, unsigned): jump when rs1 >= rs2"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00508093, # ADDI x1, x1, 5
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020F0E3, # BGEU x1, x2, 0x800 => Jump to 0x80001004 (since 5 >= 2)
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR, # ADDI x1, x1, 1
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x80001008: NOP_INSTR,
        0x8000100C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80001010: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80001014: 0x00528293, # ADDI x5, x5, 5 => it should be executed
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
        0x80001030: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 5, f"Register x1 should be 5, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 5, f"Register x5 should be 5, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_bgeu_2(dut):
    """Test BGEU (Branch if Greater or Equal, unsigned): no jump when rs1 < rs2"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020F0E3, # BGEU x1, x2, 0x800 => Should not jump (since 1 < 2)
        0x80000010: 0x00108093, # ADDI x1, x1, 1 => it should be executed
        0x80000014: 0x00208093, # ADDI x1, x1, 2
        0x80000018: 0x00408093, # ADDI x1, x1, 4
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80001008: NOP_INSTR,
        0x8000100C: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x80001010: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80001014: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80001018: NOP_INSTR,
        0x8000101C: NOP_INSTR,
        0x80001020: NOP_INSTR,
        0x80001024: NOP_INSTR,
        0x80001028: NOP_INSTR,
        0x8000102C: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 8, f"Register x1 should be 8, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 0, f"Register x5 should be 0, got 0x{registers[5].value.integer:08x}"

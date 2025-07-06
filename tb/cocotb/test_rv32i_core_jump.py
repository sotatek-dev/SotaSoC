import cocotb
from test_utils import do_test, NOP_INSTR

@cocotb.test()
async def test_beq_1(dut):
    """Test BEQ (Branch if Equal): jump"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x002080E3, # BEQ x1, x2, 0x800 => Jump to 0x80000804 = 0x80000004 + 0x800
        0x80000008: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x8000000C: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000014: ADDI_INSTR,
        0x80000018: ADDI_INSTR,
        0x8000001C: ADDI_INSTR,
        0x80000800: ADDI_INSTR,
        0x80000804: 0x00210113, # ADDI x2, x2, 2 => it should be executed
        0x80000808: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x8000080C: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80000810: NOP_INSTR,
        0x80000814: NOP_INSTR,
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
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
        0x80000008: 0x002080E3, # BEQ x1, x2, 0x800 => Jump to 0x80000804 = 0x80000004 + 0x800
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
        0x80000804: NOP_INSTR,
        0x80000808: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x8000080C: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80000810: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80000814: NOP_INSTR,
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
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
        0x80000008: 0x002090E3, # BEQ x1, x2, 0x800 => Jump to 0x80000804 = 0x80000004 + 0x800
        0x8000000C: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR,
        0x8000001C: ADDI_INSTR,
        0x80000804: ADDI_INSTR,
        0x80000808: 0x00210113, # ADDI x2, x2, 2 => it should be executed
        0x8000080C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80000810: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80000814: NOP_INSTR,
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
        0x80000830: NOP_INSTR,
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
        0x80000008: 0x002090E3, # BEQ x1, x2, 0x800 => Jump to 0x80000804 = 0x80000004 + 0x800
        0x8000000C: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000804: ADDI_INSTR,
        0x80000808: 0x00210113, # ADDI x2, x2, 2 => it should be executed
        0x8000080C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80000810: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80000814: NOP_INSTR,
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
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
        0x8000000C: 0x0020C0E3, # BLT x1, x2, 0x800 => Jump to 0x80000804 (since -1 < 2)
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR, # ADDI x1, x1, 1
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x8000002C: ADDI_INSTR,
        0x80000808: NOP_INSTR,
        0x8000080C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80000810: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80000814: 0x00528293, # ADDI x5, x5, 5 => it should be executed
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
        0x80000830: NOP_INSTR,
        0x80000834: NOP_INSTR,
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
        0x80000038: NOP_INSTR,
        0x80000808: NOP_INSTR,
        0x8000080C: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x80000810: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80000814: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR, # NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
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
        0x8000000C: 0x0020D0E3, # BGE x1, x2, 0x800 => Jump to 0x80000804 (since 5 >= 2)
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR, # ADDI x1, x1, 1
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x8000002C: ADDI_INSTR,
        0x80000808: NOP_INSTR,
        0x8000080C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80000810: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80000814: 0x00528293, # ADDI x5, x5, 5 => it should be executed
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
        0x80000830: NOP_INSTR,
        0x80000834: NOP_INSTR,
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
        0x80000038: NOP_INSTR,
        0x80000808: NOP_INSTR,
        0x8000080C: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x80000810: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80000814: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
        0x80000830: NOP_INSTR,
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
        0x8000000C: 0x0020E0E3, # BLTU x1, x2, 0x800 => Jump to 0x80000804 (since 1 < 2)
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR, # ADDI x1, x1, 1
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x80000808: NOP_INSTR,
        0x8000080C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80000810: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80000814: 0x00528293, # ADDI x5, x5, 5 => it should be executed
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
        0x80000830: NOP_INSTR,
        0x80000834: NOP_INSTR,
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
        0x80000038: NOP_INSTR,
        0x80000804: NOP_INSTR,
        0x8000080C: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x80000810: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80000814: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
        0x80000830: NOP_INSTR,
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
        0x8000000C: 0x0020F0E3, # BGEU x1, x2, 0x800 => Jump to 0x80000804 (since 5 >= 2)
        0x80000010: ADDI_INSTR, # ADDI x1, x1, 1 => it should not be executed
        0x80000014: ADDI_INSTR, # ADDI x1, x1, 1
        0x80000018: ADDI_INSTR, # ADDI x1, x1, 1
        0x8000001C: ADDI_INSTR,
        0x80000020: ADDI_INSTR,
        0x80000024: ADDI_INSTR,
        0x80000028: ADDI_INSTR,
        0x80000808: NOP_INSTR,
        0x8000080C: 0x00318193, # ADDI x3, x3, 3 => it should be executed
        0x80000810: 0x00420213, # ADDI x4, x4, 4 => it should be executed
        0x80000814: 0x00528293, # ADDI x5, x5, 5 => it should be executed
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
        0x80000830: NOP_INSTR,
        0x80000834: NOP_INSTR,
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
        0x80000038: NOP_INSTR,
        0x80000808: NOP_INSTR,
        0x8000080C: 0x00210113, # ADDI x2, x2, 2 => it should not be executed
        0x80000810: 0x00318193, # ADDI x3, x3, 3 => it should not be executed
        0x80000814: 0x00420213, # ADDI x4, x4, 4 => it should not be executed
        0x80000818: NOP_INSTR,
        0x8000081C: NOP_INSTR,
        0x80000820: NOP_INSTR,
        0x80000824: NOP_INSTR,
        0x80000828: NOP_INSTR,
        0x8000082C: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 8, f"Register x1 should be 8, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 0, f"Register x5 should be 0, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_jal_1(dut):
    """Test JAL (Jump and Link): basic jump with return address"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x008000EF, # JAL x1, 0x008 => Jump to 0x80000004 + 0x008 = 0x8000000C, x1 = 0x80000008
        0x80000008: 0x00108093, # ADDI x1, x1, 1 => Should not be executed
        0x8000000C: 0x00210113, # ADDI x2, x2, 2 => Should be executed
        0x80000010: 0x00318193, # ADDI x3, x3, 3 => Should be executed
        0x80000014: 0x00420213, # ADDI x4, x4, 4 => Should be executed
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0x80000008, f"Register x1 should be 0x80000008 (return address), got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_jal_2(dut):
    """Test JAL (Jump and Link): negative offset jump"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x00318193, # ADDI x3, x3, 3
        0x80000010: 0xFF9FF0EF, # JAL x1, -8 => Jump to 0x80000010 + (-8) = 0x80000008, x1 = 0x80000014
        0x80000014: 0x00420213, # ADDI x4, x4, 4 => Should not be executed initially
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0x80000014, f"Register x1 should be 0x80000014 (return address), got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 4, f"Register x2 should be 4 (executed twice), got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 6, f"Register x3 should be 6 (executed twice), got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0 (not executed), got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_jal_3(dut):
    """Test JAL (Jump and Link): jump to x0 (discard return address)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x0080006F, # JAL x0, 0x008 => Jump to 0x80000004 + 0x008 = 0x8000000C, x0 remains 0
        0x80000008: 0x00108093, # ADDI x1, x1, 1 => Should not be executed
        0x8000000C: 0x00210113, # ADDI x2, x2, 2 => Should be executed
        0x80000010: 0x00318193, # ADDI x3, x3, 3 => Should be executed
        0x80000014: 0x00420213, # ADDI x4, x4, 4 => Should be executed
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[0].value == 0, f"Register x0 should always be 0, got 0x{registers[0].value.integer:08x}"
    assert registers[1].value == 0, f"Register x1 should be 0, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_jalr_1(dut):
    """Test JALR (Jump and Link Register): with offset"""

    memory = {
        0x80000000: 0x40000137, # LUI x2, 0x40000 => x2 = 0x40000000
        0x80000004: 0x00111113, # # SLLI x2, x2, 1 => x2 = 0x80000000
        0x80000008: NOP_INSTR,
        0x8000000C: 0x008100E7, # JALR x1, x2, 8 => Jump to (x2 + 8) & ~1 = 0x80000008, x1 = 0x80000010
        0x80000010: 0x00318193, # ADDI x3, x3, 3 => Should not be executed initially
        0x80000014: 0x00420213, # ADDI x4, x4, 4 => Should not be executed
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0x80000010, f"Register x1 should be 0x80000010 (return address), got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 0x80000000, f"Register x2 should be 0x80000000, got 0x{registers[2].value.integer:08x}"
    # The processor will keep executing from 0x80000008 onwards in a loop
    assert registers[3].value == 0, f"Register x3 should be 0 (not executed), got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0 (not executed), got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_jalr_2(dut):
    """Test JALR (Jump and Link Register): LSB clearing (address alignment)"""

    memory = {
        0x80000000: 0x40000137, # LUI x2, 0x40000 => x2 = 0x40000000
        0x80000004: 0x00111113, # SLLI x2, x2, 1 => x2 = 0x80000000
        0x80000008: 0x00110113, # ADDI x2, x2, 1 => x2 = 0x80000001 (odd address)
        0x8000000C: NOP_INSTR,
        0x80000010: 0x00C100E7, # JALR x1, x2, 12 => Jump to (x2 + 12) & ~1 = (0x80000001 + 12) & ~1 = 0x8000000C
        0x80000014: 0x00318193, # ADDI x3, x3, 3 => Should not be executed
        0x80000018: 0x00420213, # ADDI x4, x4, 4 => Should not be executed
        0x8000001C: 0x00528293, # ADDI x5, x5, 5 => Should not be executed
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0x80000014, f"Register x1 should be 0x80000014 (return address), got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 0x80000001, f"Register x2 should be 0x80000001, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 0, f"Register x5 should be 0, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_jalr_3(dut):
    """Test JALR (Jump and Link Register): return from subroutine simulation"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x001000EF, # JAL x1, 0x800 => Jump to 0x80000004 + 0x800, x1 = 0x80000008
        0x80000008: 0x00210113, # ADDI x2, x2, 2 => Should be executed after return
        0x8000000C: 0x00318193, # ADDI x3, x3, 3 => Should be executed after return
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000804: 0x00420213, # ADDI x4, x4, 4 => Should be executed (in subroutine)
        0x80000808: 0x00528293, # ADDI x5, x5, 5 => Should be executed (in subroutine)
        0x8000080C: 0x000080E7, # JALR x1, x1, 0 => Return to address in x1 (0x80000008)
        0x80000810: 0x00630313, # ADDI x6, x6, 6 => Should not be executed
        0x80000814: NOP_INSTR,
        0x80000018: NOP_INSTR,
    }
    await do_test(dut, memory, 16)

    registers = dut.core.register_file.registers
    assert registers[1].value == 0x80000810, f"Register x1 should be 0x8000810 (return address from JALR), got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 5, f"Register x5 should be 5, got 0x{registers[5].value.integer:08x}"
    assert registers[6].value == 0, f"Register x6 should be 0 (not executed), got 0x{registers[6].value.integer:08x}"

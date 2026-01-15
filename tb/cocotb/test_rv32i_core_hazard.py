import cocotb
from test_utils import do_test, NOP_INSTR


@cocotb.test()
async def test_load_use_hazard_0(dut):
    """Test load-use hazard: no hazard"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000093, # ADDI x1, x0, 768
        0x00000008: 0x0200a183, # LW x3, 0x20(x1)
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: 0x00218113, # ADDI x2, x3, 2
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
    }
    await do_test(dut, memory, 14, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_1(dut):
    """Test load-use hazard: stall 1 cycle"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000093, # ADDI x1, x0, 0x300
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: 0x0200a183, # LW x3, 0x20(x1)
        0x00000020: 0x00218113, # ADDI x2, x3, 2
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_2(dut):
    """Test load-use hazard"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000093, # ADDI x1, x0, 0x300
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: 0x0200a183, # LW x3, 0x20(x1)
        0x00000020: NOP_INSTR,
        0x00000024: 0x00218113, # ADDI x2, x3, 2
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_3(dut):
    """Test load-use hazard:"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000093, # ADDI x1, x0, 0x300
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: 0x0200a183, # LW x3, 0x20(x1)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: 0x00218113, # ADDI x2, x3, 2
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_4(dut):
    """Test load-use hazard:"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000093, # ADDI x1, x0, 0x300
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: 0x0200a183, # LW x3, 0x20(x1)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: 0x00218113, # ADDI x2, x3, 2
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_5(dut):
    """Test load-use hazard:"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000093, # ADDI x1, x0, 0x300
        0x00000008: 0x0200a183, # LW x3, 0x20(x1)
        0x0000000C: 0x00218113, # ADDI x2, x3, 2
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
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"


@cocotb.test()
async def test_data_hazard_rs1_1(dut):
    """Test data hazard: forward rs1 from EX stage"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1
        0x00000008: 0x00208093, # ADDI x1, x1, 2
        0x0000000C: 0x00308093, # ADDI x1, x1, 3
        0x00000010: 0x00408093, # ADDI x1, x1, 4
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
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 10, f"Register x1 should be 10, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_1b(dut):
    """Test data hazard: forward rs1 from EX stage"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1
        0x00000008: 0x00208093, # ADDI x1, x1, 2
        0x0000000C: 0x00308113, # ADDI x2, x1, 3
        0x00000010: 0x00410113, # ADDI x2, x2, 4
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
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"
    assert registers[2].value == 10, f"Register x2 should be 10, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_2(dut):
    """Test data hazard: forward rs1 from MEM stage"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1
        0x00000008: NOP_INSTR,
        0x0000000C: 0x00208093, # ADDI x1, x1, 2
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
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_3(dut):
    """Test data hazard: forward rs1 from WB stage"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: 0x00208093, # ADDI x1, x1, 2
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
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_4(dut):
    """Test data hazard: no hazard"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: 0x00208093, # ADDI x1, x1, 2
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
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_5(dut):
    """Test data hazard"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1
        0x00000008: 0x00208093, # ADDI x1, x1, 2
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: 0x00308093, # ADDI x1, x1, 3
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
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 6, f"Register x1 should be 6, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs2_1(dut):
    """Test data hazard: forward rs2 from EX stage"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: 0x001080B3, # ADD x1, x1, x1 => x1 = 2
        0x0000001C: 0x001080B3, # ADD x1, x1, x1 => x1 = 4
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 4, f"Register x1 should be 4, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs2_2(dut):
    """Test data hazard: forward rs2 from MEM stage"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: 0x001080B3, # ADD x1, x1, x1 => x1 = 2
        0x0000001C: NOP_INSTR,
        0x00000020: 0x001080B3, # ADD x1, x1, x1 => x1 = 4
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    await do_test(dut, memory, 20)

    registers = dut.core.register_file.registers
    assert registers[1].value == 4, f"Register x1 should be 4, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs2_3(dut):
    """Test data hazard: forward rs2 from WB stage"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: 0x001080B3, # ADD x1, x1, x1 => x1 = 2
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: 0x001080B3, # ADD x1, x1, x1 => x1 = 4
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    await do_test(dut, memory, 20)

    registers = dut.core.register_file.registers
    assert registers[1].value == 4, f"Register x1 should be 4, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs2_4(dut):
    """Test data hazard: no hazard"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: 0x001080B3, # ADD x1, x1, x1 => x1 = 2
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: 0x001080B3, # ADD x1, x1, x1 => x1 = 4
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    await do_test(dut, memory, 20)

    registers = dut.core.register_file.registers
    assert registers[1].value == 4, f"Register x1 should be 4, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_hazard_rs2_5(dut):
    """Test hazard: forward from EX stage"""

    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: 0x00108133, # ADD x2, x1, x1 => x2 = 2
        0x0000001C: 0x002080B3, # ADD x1, x1, x2 => x1 = 3
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"
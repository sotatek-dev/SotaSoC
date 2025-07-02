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
async def test_reset(dut):
    """Test that the core resets properly"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the core
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Check that PC starts at reset address
    await RisingEdge(dut.clk)
    assert dut.instr_addr.value == 0x80000000, f"PC should be 0x80000000, got {dut.instr_addr.value.integer:08x}"

@cocotb.test()
async def test_nop_instruction(dut):
    """Test NOP instruction execution"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Provide NOP instruction
    dut.instr_data.value = 0x00000013  # NOP: addi x0, x0, 0
    dut.mem_data.value = 0x00000000
    
    # Let it execute for a few cycles
    for _ in range(10):
        await RisingEdge(dut.clk)
        # PC should increment by 4 each cycle
        expected_pc = 0x80000000 + (_ * 4)
        assert dut.instr_addr.value == expected_pc, f"PC should be {expected_pc:08x}, got {dut.instr_addr.value.integer:08x}"

@cocotb.test()
async def test_addi_instruction(dut):
    """Test ADDI instruction"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    
    # ADDI x1, x0, 5 (addi x1, x0, 5)
    dut.instr_data.value = 0x00500093
    dut.mem_data.value = 0x00000000
    
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Execute for several cycles to see the pipeline
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)

    assert dut.core.register_file.registers[1].value == 5, f"Register x1 should be 5, got {dut.core.register_file.registers[1].value.integer:08x}"
    # print("All register values:")
    # for i in range(16):  # RV32E has 16 registers (x0-x15)
    #     reg_value = dut.core.register_file.registers[i].value.integer
    #     print(f"  x{i}: 0x{reg_value:08x} ({reg_value})")

@cocotb.test()
async def test_add_instruction(dut):
    """Test ADD instruction"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # First, set up values for x1 and x2 using ADDI
    # ADDI x1, x0, 5 (addi x1, x0, 5)
    dut.instr_data.value = 0x00500093
    dut.mem_data.value = 0x00000000
    
    # Execute for several cycles to complete the ADDI
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)

    # ADDI x2, x0, 10 (addi x2, x0, 10)
    dut.instr_data.value = 0x00a00113
    dut.mem_data.value = 0x00000000
    
    # Execute for several cycles to complete the ADDI
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)

    # Now test ADD x3, x1, x2 (add x3, x1, x2)
    dut.instr_data.value = 0x002081B3
    dut.mem_data.value = 0x00000000
    
    # Execute for several cycles to complete the ADD
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)

    # Validate that x3 contains the correct result (5 + 10 = 15)
    assert dut.core.register_file.registers[3].value == 15, f"Register x3 should be 15, got {dut.core.register_file.registers[3].value.integer:08x}"
    
    # Also verify x1 and x2 still have their original values
    assert dut.core.register_file.registers[1].value == 5, f"Register x1 should be 5, got {dut.core.register_file.registers[1].value.integer:08x}"
    assert dut.core.register_file.registers[2].value == 10, f"Register x2 should be 10, got {dut.core.register_file.registers[2].value.integer:08x}"



@cocotb.test()
async def test_load_instruction(dut):
    """Test load instruction"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1

    # Set up base address in x1
    # ADDI x1, x0, 0x300 (ADDI x1, x0, 768)
    dut.instr_data.value = 0x30000093
    dut.mem_data.value = 0x00000000
    
    # Execute ADDI
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)
    
    # Verify x1 contains the base address
    assert dut.core.register_file.registers[1].value == 0x300, f"Register x1 should be 0x300, got {dut.core.register_file.registers[1].value.integer:08x}"
    

    # Load a value from memory using LW
    # LW x3, 0x20(x1) (load word from address x1 + 0x20 into x3)
    dut.instr_data.value = 0x0200a183
    dut.mem_data.value = 0xABCD  # Data to be loaded
    
    # Execute load
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)
        print(f"Load cycle {_}: PC={dut.instr_addr.value.integer:08x}, Mem_RE={dut.mem_re.value}, Mem_Addr={dut.mem_addr.value.integer:08x}")
    
    assert dut.core.mem_addr.value == 0x320, f"Mem_Addr should be 0x320, got {dut.core.mem_addr.value.integer:08x}"

    # Validate that x3 contains the loaded data
    assert dut.core.register_file.registers[3].value == 0xABCD, f"Register x3 should be 0xABCD, got {dut.core.register_file.registers[3].value.integer:08x}"

@cocotb.test()
async def test_store_instruction(dut):
    """Test store operations"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Set up base address in x1
    # ADDI x1, x0, 0x300 (addi x1, x0, 768)
    dut.instr_data.value = 0x30000093
    dut.mem_data.value = 0x00000000
    
    # Execute ADDI
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)
    
    # Verify x1 contains the base address
    assert dut.core.register_file.registers[1].value == 0x300, f"Register x1 should be 0x300, got {dut.core.register_file.registers[1].value.integer:08x}"
    
    # Load a value into x2 to store
    # ADDI x2, x0, 0x6DE (addi x2, x0, 0x6DE)
    dut.instr_data.value = 0x6DE00113
    dut.mem_data.value = 0x00000000
    
    # Execute ADDI
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)
    
    # Verify x2 contains the value to store
    assert dut.core.register_file.registers[2].value == 0x6DE, f"Register x2 should be 0x6DE, got {dut.core.register_file.registers[2].value.integer:08x}"
    
    # Store the value to memory using SW
    # SW x2, 0(x1) (store word from x2 to address x1 + 0)
    dut.instr_data.value = 0x0220A023
    dut.mem_data.value = 0x00000000
    
    # Execute store
    for _ in range(CYCLES_PER_INSTRUCTION):
        await RisingEdge(dut.clk)

    assert dut.core.mem_addr.value == 0x320, f"Mem_Addr should be 0x320, got {dut.core.mem_addr.value.integer:08x}"
    assert dut.core.mem_wdata.value == 0x6DE, f"Mem_wdata should be 0x6DE, got {dut.core.mem_wdata.value.integer:08x}"
    
    # Verify that x2 still contains the original value after store
    assert dut.core.register_file.registers[2].value == 0x6DE, f"Register x2 should still be 0x6DE, got {dut.core.register_file.registers[2].value.integer:08x}" 


@cocotb.test()
async def test_add(dut):
    """Test ADD"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x001101B3, # ADD x3, x2, x1
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 3, f"Register x3 should be 3, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_sub(dut):
    """Test SUB"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00508093, # ADDI x1, x1, 5
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x402081B3, # SUB x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 3, f"Register x3 should be 3, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_sll(dut):
    """Test SLL (Shift Left Logical)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x002091B3, # SLL x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 4, f"Register x3 should be 4, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_slt(dut):
    """Test SLT (Set if Less Than, signed)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0xFFF08093, # ADDI x1, x1, -1 (signed)
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020A1B3, # SLT x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 1, f"Register x3 should be 1, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_sltu(dut):
    """Test SLTU (Set if Less Than, unsigned)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020B1B3, # SLTU x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 1, f"Register x3 should be 1, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_xor(dut):
    """Test XOR"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00F08093, # ADDI x1, x1, 15 (0x0F)
        0x80000008: 0x0F010113, # ADDI x2, x2, 240 (0xF0)
        0x8000000C: 0x0020C1B3, # XOR x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 0xFF, f"Register x3 should be 0xFF, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_srl(dut):
    """Test SRL (Shift Right Logical)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00808093, # ADDI x1, x1, 8
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x0020D1B3, # SRL x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 2, f"Register x3 should be 2, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_sra(dut):
    """Test SRA (Shift Right Arithmetic)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0xFFF08093, # ADDI x1, x1, -1 (0xFFFFFFFF)
        0x80000008: 0x00210113, # ADDI x2, x2, 2
        0x8000000C: 0x4020D1B3, # SRA x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    expected = 0xFFFFFFFF  # -1 >> 2 = 0xFFFFFFFF
    assert registers[3].value == expected, f"Register x3 should be {expected:08x}, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_or(dut):
    """Test OR"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00A08093, # ADDI x1, x1, 10 (0x0A)
        0x80000008: 0x00510113, # ADDI x2, x2, 5 (0x05)
        0x8000000C: 0x0020E1B3, # OR x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 0x0F, f"Register x3 should be 0x0F, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_and(dut):
    """Test AND"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00F08093, # ADDI x1, x1, 15 (0x0F)
        0x80000008: 0x0F010113, # ADDI x2, x2, 240 (0xF0)
        0x8000000C: 0x0020F1B3, # AND x3, x1, x2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[3].value == 0x00, f"Register x3 should be 0x00, got {registers[3].value.integer:08x}"

@cocotb.test()
async def test_addi(dut):
    """Test ADDI"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[1].value == 1, f"Register x1 should be 1, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_slti(dut):
    """Test SLTI (Set if Less Than Immediate, signed)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0xFFF08093, # ADDI x1, x1, -1 (signed)
        0x80000008: 0x0020A113, # SLTI x2, x1, 2 (should be 1 since -1 < 2)
        0x8000000C: 0x0050A193, # SLTI x3, x1, 5 (should be 1 since -1 < 5)
        0x80000010: 0xFFF0A213, # SLTI x4, x1, -1 (should be 0 since -1 == -1)
        0x80000014: 0xFFE0A293, # SLTI x5, x1, -2 (should be 0 since -1 > -2)
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[2].value == 1, f"Register x2 should be 1, got {registers[2].value.integer:08x}"
    assert registers[3].value == 1, f"Register x3 should be 1, got {registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got {registers[4].value.integer:08x}"
    assert registers[5].value == 0, f"Register x5 should be 0, got {registers[5].value.integer:08x}"

@cocotb.test()
async def test_sltiu(dut):
    """Test SLTIU (Set if Less Than Immediate, unsigned)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x0020B113, # SLTIU x2, x1, 2 (should be 1 since 1 < 2)
        0x8000000C: 0x0050B193, # SLTIU x3, x1, 5 (should be 1 since 1 < 5)
        0x80000010: 0x0010B213, # SLTIU x4, x1, 1 (should be 0 since 1 == 1)
        0x80000014: 0x0000B293, # SLTIU x5, x1, 0 (should be 0 since 1 > 0)
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)

    registers = dut.core.register_file.registers
    assert registers[2].value == 1, f"Register x2 should be 1, got {registers[2].value.integer:08x}"
    assert registers[3].value == 1, f"Register x3 should be 1, got {registers[3].value.integer:08x}"
    assert registers[4].value == 0, f"Register x4 should be 0, got {registers[4].value.integer:08x}"
    assert registers[5].value == 0, f"Register x5 should be 0, got {registers[5].value.integer:08x}"

@cocotb.test()
async def test_xori(dut):
    """Test XORI (XOR Immediate)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00F08093, # ADDI x1, x1, 15 (0x0F)
        0x80000008: 0x0F00C113, # XORI x2, x1, 240 (0xF0) => 0x0F ^ 0xF0 = 0xFF
        0x8000000C: 0x00F0C193, # XORI x3, x1, 15 (0x0F) => 0x0F ^ 0x0F = 0x00
        0x80000010: 0x0000C213, # XORI x4, x1, 0 => 0x0F ^ 0x00 = 0x0F
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
    }
    await do_test(dut, memory, 11)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xFF, f"Register x2 should be 0xFF, got {registers[2].value.integer:08x}"
    assert registers[3].value == 0x00, f"Register x3 should be 0x00, got {registers[3].value.integer:08x}"
    assert registers[4].value == 0x0F, f"Register x4 should be 0x0F, got {registers[4].value.integer:08x}"

@cocotb.test()
async def test_ori(dut):
    """Test ORI (OR Immediate)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00A08093, # ADDI x1, x1, 10 (0x0A)
        0x80000008: 0x0050E113, # ORI x2, x1, 5 (0x05) => 0x0A | 0x05 = 0x0F
        0x8000000C: 0x0F00E193, # ORI x3, x1, 240 (0xF0) => 0x0A | 0xF0 = 0xFA
        0x80000010: 0x0000E213, # ORI x4, x1, 0 => 0x0A | 0x00 = 0x0A
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
    }
    await do_test(dut, memory, 11)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0x0F, f"Register x2 should be 0x0F, got {registers[2].value.integer:08x}"
    assert registers[3].value == 0xFA, f"Register x3 should be 0xFA, got {registers[3].value.integer:08x}"
    assert registers[4].value == 0x0A, f"Register x4 should be 0x0A, got {registers[4].value.integer:08x}"

@cocotb.test()
async def test_andi(dut):
    """Test ANDI (AND Immediate)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00F08093, # ADDI x1, x1, 15 (0x0F)
        0x80000008: 0x0F00F113, # ANDI x2, x1, 240 (0xF0) => 0x0F & 0xF0 = 0x00
        0x8000000C: 0x00F0F193, # ANDI x3, x1, 15 (0x0F) => 0x0F & 0x0F = 0x0F
        0x80000010: 0x0030F213, # ANDI x4, x1, 3 (0x03) => 0x0F & 0x03 = 0x03
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
    }
    await do_test(dut, memory, 11)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0x00, f"Register x2 should be 0x00, got {registers[2].value.integer:08x}"
    assert registers[3].value == 0x0F, f"Register x3 should be 0x0F, got {registers[3].value.integer:08x}"
    assert registers[4].value == 0x03, f"Register x4 should be 0x03, got {registers[4].value.integer:08x}"

@cocotb.test()
async def test_slli(dut):
    """Test SLLI (Shift Left Logical Immediate)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00209113, # SLLI x2, x1, 2 => 1 << 2 = 4
        0x8000000C: 0x00309193, # SLLI x3, x1, 3 => 1 << 3 = 8
        0x80000010: 0x00409213, # SLLI x4, x1, 4 => 1 << 4 = 16
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
    }
    await do_test(dut, memory, 11)

    registers = dut.core.register_file.registers
    assert registers[2].value == 4, f"Register x2 should be 4, got {registers[2].value.integer:08x}"
    assert registers[3].value == 8, f"Register x3 should be 8, got {registers[3].value.integer:08x}"
    assert registers[4].value == 16, f"Register x4 should be 16, got {registers[4].value.integer:08x}"

@cocotb.test()
async def test_srli(dut):
    """Test SRLI (Shift Right Logical Immediate)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00808093, # ADDI x1, x1, 8
        0x80000008: 0x0020D113, # SRLI x2, x1, 2 => 8 >> 2 = 2
        0x8000000C: 0x0030D193, # SRLI x3, x1, 3 => 8 >> 3 = 1
        0x80000010: 0x0010D213, # SRLI x4, x1, 1 => 8 >> 1 = 4
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
    }
    await do_test(dut, memory, 11)

    registers = dut.core.register_file.registers
    assert registers[2].value == 2, f"Register x2 should be 2, got {registers[2].value.integer:08x}"
    assert registers[3].value == 1, f"Register x3 should be 1, got {registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got {registers[4].value.integer:08x}"

@cocotb.test()
async def test_srai(dut):
    """Test SRAI (Shift Right Arithmetic Immediate)"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0xFFF08093, # ADDI x1, x1, -1 (0xFFFFFFFF)
        0x80000008: 0x4020D113, # SRAI x2, x1, 2 => -1 >> 2 = 0xFFFFFFFF
        0x8000000C: 0x4030d193, # SRAI x3, x1, 3 => -1 >> 3 = 0xFFFFFFFF
        0x80000010: 0x4010D213, # SRAI x4, x1, 1 => -1 >> 1 = 0xFFFFFFFF
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
    }
    await do_test(dut, memory, 11)

    registers = dut.core.register_file.registers
    expected = 0xFFFFFFFF  # -1 >> n = 0xFFFFFFFF for any n
    assert registers[2].value == expected, f"Register x2 should be {expected:08x}, got {registers[2].value.integer:08x}"
    assert registers[3].value == expected, f"Register x3 should be {expected:08x}, got {registers[3].value.integer:08x}"
    assert registers[4].value == expected, f"Register x4 should be {expected:08x}, got {registers[4].value.integer:08x}"

@cocotb.test()
async def test_branch_instruction(dut):
    """Test branch instruction"""

    ADDI_INSTR = 0x00108093

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x002080E3, # BEQ x1, x2, 0x800 => Jump to 0x80001004
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
    assert registers[1].value == 0, f"Register x1 should still be 0, got {registers[1].value.integer:08x}"
    assert registers[2].value == 2, f"Register x2 should be 2, got {registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got {registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got {registers[4].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_0(dut):
    """Test load-use hazard: no hazard"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x30000093, # ADDI x1, x0, 768
        0x80000008: 0x0200a183, # LW x3, 0x20(x1)
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: 0x00218113, # ADDI x2, x3, 2
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
    }
    await do_test(dut, memory, 14, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_1(dut):
    """Test load-use hazard: stall 1 cycle"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x30000093, # ADDI x1, x0, 0x300
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: 0x0200a183, # LW x3, 0x20(x1)
        0x80000020: 0x00218113, # ADDI x2, x3, 2
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000038: NOP_INSTR,
        0x8000003C: NOP_INSTR,
        0x80000040: NOP_INSTR,
        0x80000044: NOP_INSTR,
        0x80000048: NOP_INSTR,
        0x8000004C: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_2(dut):
    """Test load-use hazard"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x30000093, # ADDI x1, x0, 0x300
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: 0x0200a183, # LW x3, 0x20(x1)
        0x80000020: NOP_INSTR,
        0x80000024: 0x00218113, # ADDI x2, x3, 2
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000038: NOP_INSTR,
        0x8000003C: NOP_INSTR,
        0x80000040: NOP_INSTR,
        0x80000044: NOP_INSTR,
        0x80000048: NOP_INSTR,
        0x8000004C: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_3(dut):
    """Test load-use hazard:"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x30000093, # ADDI x1, x0, 0x300
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: 0x0200a183, # LW x3, 0x20(x1)
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: 0x00218113, # ADDI x2, x3, 2
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000038: NOP_INSTR,
        0x8000003C: NOP_INSTR,
        0x80000040: NOP_INSTR,
        0x80000044: NOP_INSTR,
        0x80000048: NOP_INSTR,
        0x8000004C: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_4(dut):
    """Test load-use hazard:"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x30000093, # ADDI x1, x0, 0x300
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: 0x0200a183, # LW x3, 0x20(x1)
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: 0x00218113, # ADDI x2, x3, 2
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000038: NOP_INSTR,
        0x8000003C: NOP_INSTR,
        0x80000040: NOP_INSTR,
        0x80000044: NOP_INSTR,
        0x80000048: NOP_INSTR,
        0x8000004C: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"

@cocotb.test()
async def test_load_use_hazard_5(dut):
    """Test load-use hazard:"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x30000093, # ADDI x1, x0, 0x300
        0x80000008: 0x0200a183, # LW x3, 0x20(x1)
        0x8000000C: 0x00218113, # ADDI x2, x3, 2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: NOP_INSTR,
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000038: NOP_INSTR,
        0x8000003C: NOP_INSTR,
        0x80000040: NOP_INSTR,
        0x80000044: NOP_INSTR,
        0x80000048: NOP_INSTR,
        0x8000004C: NOP_INSTR,
    }
    await do_test(dut, memory, 20, 0xABCD)

    registers = dut.core.register_file.registers
    assert registers[2].value == 0xABCF, f"Register x2 should be 0xABCF, got {registers[2].value.integer:08x}"


@cocotb.test()
async def test_data_hazard_rs1_1(dut):
    """Test data hazard: forward rs1 from EX stage"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00208093, # ADDI x1, x1, 2
        0x8000000C: 0x00308093, # ADDI x1, x1, 3
        0x80000010: 0x00408093, # ADDI x1, x1, 4
        0x80000014: NOP_INSTR,
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
    assert registers[1].value == 10, f"Register x1 should be 10, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_2(dut):
    """Test data hazard: forward rs1 from MEM stage"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: NOP_INSTR,
        0x8000000C: 0x00208093, # ADDI x1, x1, 2
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
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
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_3(dut):
    """Test data hazard: forward rs1 from WB stage"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: 0x00208093, # ADDI x1, x1, 2
        0x80000014: NOP_INSTR,
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
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_4(dut):
    """Test data hazard: no hazard"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: 0x00208093, # ADDI x1, x1, 2
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
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs1_5(dut):
    """Test data hazard"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1
        0x80000008: 0x00208093, # ADDI x1, x1, 2
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: 0x00308093, # ADDI x1, x1, 3
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
    assert registers[1].value == 6, f"Register x1 should be 6, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs2_1(dut):
    """Test data hazard: forward rs2 from EX stage"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: 0x001080B3, # ADD x1, x1, x1 => x1 = 2
        0x8000001C: 0x001080B3, # ADD x1, x1, x1 => x1 = 4
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 4, f"Register x1 should be 4, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs2_2(dut):
    """Test data hazard: forward rs2 from MEM stage"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: 0x001080B3, # ADD x1, x1, x1 => x1 = 2
        0x8000001C: NOP_INSTR,
        0x80000020: 0x001080B3, # ADD x1, x1, x1 => x1 = 4
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000038: NOP_INSTR,
        0x8000003C: NOP_INSTR,
        0x80000040: NOP_INSTR,
        0x80000044: NOP_INSTR,
        0x80000048: NOP_INSTR,
        0x8000004C: NOP_INSTR,
    }
    await do_test(dut, memory, 20)

    registers = dut.core.register_file.registers
    assert registers[1].value == 4, f"Register x1 should be 4, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs2_3(dut):
    """Test data hazard: forward rs2 from WB stage"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: 0x001080B3, # ADD x1, x1, x1 => x1 = 2
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: 0x001080B3, # ADD x1, x1, x1 => x1 = 4
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000038: NOP_INSTR,
        0x8000003C: NOP_INSTR,
        0x80000040: NOP_INSTR,
        0x80000044: NOP_INSTR,
        0x80000048: NOP_INSTR,
        0x8000004C: NOP_INSTR,
    }
    await do_test(dut, memory, 20)

    registers = dut.core.register_file.registers
    assert registers[1].value == 4, f"Register x1 should be 4, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_data_hazard_rs2_4(dut):
    """Test data hazard: no hazard"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: 0x001080B3, # ADD x1, x1, x1 => x1 = 2
        0x8000001C: NOP_INSTR,
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: 0x001080B3, # ADD x1, x1, x1 => x1 = 4
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
        0x80000038: NOP_INSTR,
        0x8000003C: NOP_INSTR,
        0x80000040: NOP_INSTR,
        0x80000044: NOP_INSTR,
        0x80000048: NOP_INSTR,
        0x8000004C: NOP_INSTR,
    }
    await do_test(dut, memory, 20)

    registers = dut.core.register_file.registers
    assert registers[1].value == 4, f"Register x1 should be 4, got {registers[1].value.integer:08x}"

@cocotb.test()
async def test_hazard_rs2_5(dut):
    """Test hazard: forward from EX stage"""

    memory = {
        0x80000000: NOP_INSTR,
        0x80000004: 0x00108093, # ADDI x1, x1, 1 => x1 = 1
        0x80000008: NOP_INSTR,
        0x8000000C: NOP_INSTR,
        0x80000010: NOP_INSTR,
        0x80000014: NOP_INSTR,
        0x80000018: 0x00108133, # ADD x2, x1, x1 => x2 = 2
        0x8000001C: 0x002080B3, # ADD x1, x1, x2 => x1 = 3
        0x80000020: NOP_INSTR,
        0x80000024: NOP_INSTR,
        0x80000028: NOP_INSTR,
        0x8000002C: NOP_INSTR,
        0x80000030: NOP_INSTR,
        0x80000034: NOP_INSTR,
    }
    await do_test(dut, memory, 14)

    registers = dut.core.register_file.registers
    assert registers[1].value == 3, f"Register x1 should be 3, got {registers[1].value.integer:08x}"
import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock
import random

# Constants
CYCLES_PER_INSTRUCTION = 8

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
    # ADDI x1, x0, 0x300 (addi x1, x0, 768)
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
async def test_branch_instruction(dut):
    """Test branch instruction"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # BEQ x1, x2, 8 (branch if x1 == x2, offset 8)
    dut.instr_data.value = 0x00208263
    dut.mem_data.value = 0x00000000
    
    # Execute for several cycles
    for _ in range(15):
        await RisingEdge(dut.clk)
        print(f"Cycle {_}: PC={dut.instr_addr.value.integer:08x}")

@cocotb.test()
async def test_pipeline_behavior(dut):
    """Test pipeline behavior with multiple instructions"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Simulate a simple program sequence
    instructions = [
        0x00500093,  # ADDI x1, x0, 5
        0x00a00113,  # ADDI x2, x0, 10
        0x00208133,  # ADD x3, x1, x2
        0x0000a203,  # LW x4, 0(x1)
        0x0040a223   # SW x4, 4(x1)
    ]
    
    # Execute instructions
    for i, instr in enumerate(instructions):
        dut.instr_data.value = instr
        dut.mem_data.value = 0x12345678
        
        # Execute for a few cycles per instruction
        for _ in range(5):
            await RisingEdge(dut.clk)
            print(f"Instr {i}, Cycle {_}: PC={dut.instr_addr.value.integer:08x}, "
                  f"Mem_WE={dut.mem_we.value}, Mem_RE={dut.mem_re.value}")

@cocotb.test()
async def test_register_file_access(dut):
    """Test register file read/write operations"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Write to registers using ADDI
    write_instructions = [
        0x00500093,  # ADDI x1, x0, 5
        0x00a00113,  # ADDI x2, x0, 10
        0x01500193,  # ADDI x3, x0, 21
    ]
    
    for instr in write_instructions:
        dut.instr_data.value = instr
        dut.mem_data.value = 0x00000000
        
        # Execute for several cycles
        for _ in range(8):
            await RisingEdge(dut.clk)
            print(f"Write cycle: PC={dut.instr_addr.value.integer:08x}")

@cocotb.test()
async def test_alu_operations(dut):
    """Test various ALU operations"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Test different ALU operations
    alu_instructions = [
        0x00500093,  # ADDI x1, x0, 5
        0x00a00113,  # ADDI x2, x0, 10
        0x00208133,  # ADD x3, x1, x2
        0x40208133,  # SUB x3, x1, x2
        0x0020f133,  # AND x3, x1, x2
        0x0020e133,  # OR x3, x1, x2
        0x0020c133,  # XOR x3, x1, x2
    ]
    
    for i, instr in enumerate(alu_instructions):
        dut.instr_data.value = instr
        dut.mem_data.value = 0x00000000
        
        # Execute for several cycles
        for _ in range(6):
            await RisingEdge(dut.clk)
            print(f"ALU op {i}, cycle {_}: PC={dut.instr_addr.value.integer:08x}")

@cocotb.test()
async def test_memory_interface(dut):
    """Test memory interface signals"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Test memory operations
    memory_instructions = [
        0x00500093,  # ADDI x1, x0, 5 (set up address)
        0x0000a203,  # LW x4, 0(x1) (load)
        0x0040a223,  # SW x4, 4(x1) (store)
    ]
    
    for i, instr in enumerate(memory_instructions):
        dut.instr_data.value = instr
        dut.mem_data.value = 0x12345678
        
        # Execute for several cycles
        for _ in range(8):
            await RisingEdge(dut.clk)
            print(f"Memory op {i}, cycle {_}: PC={dut.instr_addr.value.integer:08x}, "
                  f"Mem_Addr={dut.mem_addr.value.integer:08x}, "
                  f"Mem_WE={dut.mem_we.value}, Mem_RE={dut.mem_re.value}")
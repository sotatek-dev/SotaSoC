import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock
import random

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
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # ADDI x1, x0, 5 (addi x1, x0, 5)
    dut.instr_data.value = 0x00500093
    dut.mem_data.value = 0x00000000
    
    # Execute for several cycles to see the pipeline
    for _ in range(15):
        await RisingEdge(dut.clk)
        print(f"Cycle {_}: PC={dut.instr_addr.value.integer:08x}, Mem_WE={dut.mem_we.value}, Mem_RE={dut.mem_re.value}")

@cocotb.test()
async def test_add_instruction(dut):
    """Test ADD instruction"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # ADD x3, x1, x2 (add x3, x1, x2)
    dut.instr_data.value = 0x00208133
    dut.mem_data.value = 0x00000000
    
    # Execute for several cycles
    for _ in range(15):
        await RisingEdge(dut.clk)
        print(f"Cycle {_}: PC={dut.instr_addr.value.integer:08x}")

@cocotb.test()
async def test_load_store_instruction(dut):
    """Test load and store instructions"""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # LW x4, 0(x1) (load word from address in x1 + 0)
    dut.instr_data.value = 0x0000a203
    dut.mem_data.value = 0x12345678  # Data to be loaded
    
    # Execute for several cycles
    for _ in range(15):
        await RisingEdge(dut.clk)
        print(f"Cycle {_}: PC={dut.instr_addr.value.integer:08x}, Mem_RE={dut.mem_re.value}, Mem_Addr={dut.mem_addr.value.integer:08x}")

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
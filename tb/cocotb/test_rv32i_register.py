#!/usr/bin/env python3
"""
Python test for RV32I Register File using cocotb
"""

import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
import random

# Register addresses for RV32I (32 registers: x0-x31)
REG_X0 = 0x0
REG_X1 = 0x1
REG_X2 = 0x2
REG_X3 = 0x3
REG_X4 = 0x4
REG_X5 = 0x5
REG_X6 = 0x6
REG_X7 = 0x7
REG_X8 = 0x8
REG_X9 = 0x9
REG_X10 = 0xA
REG_X11 = 0xB
REG_X12 = 0xC
REG_X13 = 0xD
REG_X14 = 0xE
REG_X15 = 0xF
REG_X16 = 0x10
REG_X17 = 0x11
REG_X18 = 0x12
REG_X19 = 0x13
REG_X20 = 0x14
REG_X21 = 0x15
REG_X22 = 0x16
REG_X23 = 0x17
REG_X24 = 0x18
REG_X25 = 0x19
REG_X26 = 0x1A
REG_X27 = 0x1B
REG_X28 = 0x1C
REG_X29 = 0x1D
REG_X30 = 0x1E
REG_X31 = 0x1F

@cocotb.test()
async def test_register_reset(dut):
    """Test register file reset functionality"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the register file
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Check that all registers are zero after reset
    for reg_addr in range(32):
        dut.rs1_addr.value = reg_addr
        await Timer(1, unit='ns')
        assert dut.rs1_data.value == 0, f"Register {reg_addr} not zero after reset, got {dut.rs1_data.value}"

@cocotb.test()
async def test_register_write_read(dut):
    """Test basic write and read operations"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Test writing to registers 1-15
    test_data = [0x12345678, 0x87654321, 0xDEADBEEF, 0xCAFEBABE, 0x12345678,
                 0x87654321, 0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0x87654321,
                 0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0x87654321, 0xDEADBEEF]
    
    for i in range(1, 16):
        # Write to register
        dut.rd_addr.value = i
        dut.rd_data.value = test_data[i-1]
        dut.rd_we.value = 1
        await RisingEdge(dut.clk)
        dut.rd_we.value = 0
        
        # Read back and verify
        dut.rs1_addr.value = i
        await Timer(1, unit='ns')
        assert dut.rs1_data.value == test_data[i-1], f"Register {i} read/write failed: expected {test_data[i-1]}, got {dut.rs1_data.value}"

@cocotb.test()
async def test_register_x0_always_zero(dut):
    """Test that register x0 always reads as zero"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Try to write to x0
    dut.rd_addr.value = REG_X0
    dut.rd_data.value = 0xDEADBEEF
    dut.rd_we.value = 1
    await RisingEdge(dut.clk)
    dut.rd_we.value = 0
    
    # Read from x0 - should still be zero
    dut.rs1_addr.value = REG_X0
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0, f"Register x0 should always be zero, got {dut.rs1_data.value}"
    
    # Test multiple reads from x0
    for _ in range(5):
        dut.rs1_addr.value = REG_X0
        await Timer(1, unit='ns')
        assert dut.rs1_data.value == 0, f"Register x0 should always be zero, got {dut.rs1_data.value}"

@cocotb.test()
async def test_dual_read_ports(dut):
    """Test dual read port functionality"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Write different values to registers
    test_values = {
        1: 0x11111111,
        2: 0x22222222,
        3: 0x33333333,
        4: 0x44444444,
        5: 0x55555555
    }
    
    for addr, value in test_values.items():
        dut.rd_addr.value = addr
        dut.rd_data.value = value
        dut.rd_we.value = 1
        await RisingEdge(dut.clk)
        dut.rd_we.value = 0
    
    # Test simultaneous reads from different registers
    dut.rs1_addr.value = 1
    dut.rs2_addr.value = 2
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0x11111111, f"rs1_data expected 0x11111111, got {dut.rs1_data.value}"
    assert dut.rs2_data.value == 0x22222222, f"rs2_data expected 0x22222222, got {dut.rs2_data.value}"
    
    # Test reading from same register on both ports
    dut.rs1_addr.value = 3
    dut.rs2_addr.value = 3
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0x33333333, f"rs1_data expected 0x33333333, got {dut.rs1_data.value}"
    assert dut.rs2_data.value == 0x33333333, f"rs2_data expected 0x33333333, got {dut.rs2_data.value}"

@cocotb.test()
async def test_register_update(dut):
    """Test updating existing register values"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Write initial value
    dut.rd_addr.value = 7
    dut.rd_data.value = 0x12345678
    dut.rd_we.value = 1
    await RisingEdge(dut.clk)
    dut.rd_we.value = 0
    
    # Verify initial value
    dut.rs1_addr.value = 7
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0x12345678, f"Initial write failed: expected 0x12345678, got {dut.rs1_data.value}"
    
    # Update the register
    dut.rd_addr.value = 7
    dut.rd_data.value = 0x87654321
    dut.rd_we.value = 1
    await RisingEdge(dut.clk)
    dut.rd_we.value = 0
    
    # Verify updated value
    dut.rs1_addr.value = 7
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0x87654321, f"Register update failed: expected 0x87654321, got {dut.rs1_data.value}"

@cocotb.test()
async def test_register_write_disable(dut):
    """Test that writes are ignored when write enable is low"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Write initial value
    dut.rd_addr.value = 10
    dut.rd_data.value = 0x12345678
    dut.rd_we.value = 1
    await RisingEdge(dut.clk)
    dut.rd_we.value = 0
    
    # Verify initial value
    dut.rs1_addr.value = 10
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0x12345678, f"Initial write failed: expected 0x12345678, got {dut.rs1_data.value}"
    
    # Try to write with write enable low (should be ignored)
    dut.rd_addr.value = 10
    dut.rd_data.value = 0x87654321
    dut.rd_we.value = 0  # Write disabled
    await RisingEdge(dut.clk)
    
    # Verify value hasn't changed
    dut.rs1_addr.value = 10
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0x12345678, f"Register should not change when write enable is low: expected 0x12345678, got {dut.rs1_data.value}"

@cocotb.test()
async def test_all_registers(dut):
    """Test all 32 registers"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Write unique values to all registers
    for i in range(32):
        dut.rd_addr.value = i
        dut.rd_data.value = 0x1000 + i
        dut.rd_we.value = 1
        await RisingEdge(dut.clk)
        dut.rd_we.value = 0
    
    # Read back all registers
    for i in range(32):
        dut.rs1_addr.value = i
        await Timer(1, unit='ns')
        if i == 0:
            # x0 should always be zero
            assert dut.rs1_data.value == 0, f"Register x0 should always be zero, got {dut.rs1_data.value}"
        else:
            # Other registers should have their written values
            expected = 0x1000 + i
            assert dut.rs1_data.value == expected, f"Register {i} expected {expected}, got {dut.rs1_data.value}"

@cocotb.test()
async def test_random_access(dut):
    """Test random access patterns"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Random seed for reproducible tests
    random.seed(42)
    
    # Perform random write operations
    written_values = {}
    for _ in range(20):
        addr = random.randint(1, 15)  # Don't write to x0
        value = random.randint(0, 0xFFFFFFFF)
        written_values[addr] = value
        
        dut.rd_addr.value = addr
        dut.rd_data.value = value
        dut.rd_we.value = 1
        await RisingEdge(dut.clk)
        dut.rd_we.value = 0
    
    # Verify all written values
    for addr, expected_value in written_values.items():
        dut.rs1_addr.value = addr
        await Timer(1, unit='ns')
        assert dut.rs1_data.value == expected_value, f"Register {addr} expected {expected_value}, got {dut.rs1_data.value}"

@cocotb.test()
async def test_edge_cases(dut):
    """Test edge cases and boundary conditions"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Test writing maximum values
    dut.rd_addr.value = 15
    dut.rd_data.value = 0xFFFFFFFF
    dut.rd_we.value = 1
    await RisingEdge(dut.clk)
    dut.rd_we.value = 0
    
    dut.rs1_addr.value = 15
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0xFFFFFFFF, f"Register 15 expected 0xFFFFFFFF, got {dut.rs1_data.value}"
    
    # Test writing zero
    dut.rd_addr.value = 8
    dut.rd_data.value = 0
    dut.rd_we.value = 1
    await RisingEdge(dut.clk)
    dut.rd_we.value = 0
    
    dut.rs1_addr.value = 8
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0, f"Register 8 expected 0, got {dut.rs1_data.value}"
    
    # Test reading from x0 multiple times
    for _ in range(10):
        dut.rs1_addr.value = 0
        dut.rs2_addr.value = 0
        await Timer(1, unit='ns')
        assert dut.rs1_data.value == 0, f"Register x0 should always be zero"
        assert dut.rs2_data.value == 0, f"Register x0 should always be zero"

@cocotb.test()
async def test_concurrent_read_write(dut):
    """Test concurrent read and write operations"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit='ns')
    dut.rst_n.value = 1
    await Timer(10, unit='ns')
    
    # Write initial value
    dut.rd_addr.value = 5
    dut.rd_data.value = 0x12345678
    dut.rd_we.value = 1
    await RisingEdge(dut.clk)
    dut.rd_we.value = 0
    
    # Read while writing to a different register
    dut.rs1_addr.value = 5  # Read from register 5
    dut.rd_addr.value = 6   # Write to register 6
    dut.rd_data.value = 0x87654321
    dut.rd_we.value = 1
    await Timer(1, unit='ns')
    
    # Should read the old value (before write)
    assert dut.rs1_data.value == 0x12345678, f"Concurrent read should get old value: expected 0x12345678, got {dut.rs1_data.value}"
    
    await RisingEdge(dut.clk)
    dut.rd_we.value = 0
    
    # Now read the updated value
    dut.rs1_addr.value = 6
    await Timer(1, unit='ns')
    assert dut.rs1_data.value == 0x87654321, f"Register 6 should have new value: expected 0x87654321, got {dut.rs1_data.value}" 
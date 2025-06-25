#!/usr/bin/env python3
"""
Python test for simple ALU using cocotb
"""

import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue

# ALU operation codes
ALU_ADD = 0x0
ALU_SUB = 0x1
ALU_AND = 0x2
ALU_OR  = 0x3
ALU_XOR = 0x4

@cocotb.test()
async def test_alu_addition(dut):
    """Test ALU addition operation"""
    # Set inputs
    dut.op.value = ALU_ADD
    dut.a.value = 10
    dut.b.value = 20
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result
    assert dut.result.value == 30, f"Addition failed: {dut.result.value} != 30"

@cocotb.test()
async def test_alu_subtraction(dut):
    """Test ALU subtraction operation"""
    # Set inputs
    dut.op.value = ALU_SUB
    dut.a.value = 30
    dut.b.value = 10
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result
    assert dut.result.value == 20, f"Subtraction failed: {dut.result.value} != 20"

@cocotb.test()
async def test_alu_and(dut):
    """Test ALU AND operation"""
    # Set inputs
    dut.op.value = ALU_AND
    dut.a.value = 0x0F0F0F0F
    dut.b.value = 0x00FF00FF
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result
    assert dut.result.value == 0x000F000F, f"AND failed: {dut.result.value} != 0x000F000F"

@cocotb.test()
async def test_alu_or(dut):
    """Test ALU OR operation"""
    # Set inputs
    dut.op.value = ALU_OR
    dut.a.value = 0x0F0F0F0F
    dut.b.value = 0x00FF00FF
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result
    assert dut.result.value == 0x0FFF0FFF, f"OR failed: {dut.result.value} != 0x0FFF0FFF"

@cocotb.test()
async def test_alu_xor(dut):
    """Test ALU XOR operation"""
    # Set inputs
    dut.op.value = ALU_XOR
    dut.a.value = 0x0F0F0F0F
    dut.b.value = 0x00FF00FF
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result
    assert dut.result.value == 0x0FF00FF0, f"XOR failed: {dut.result.value} != 0x0FF00FF0"

@cocotb.test()
async def test_alu_zero_result(dut):
    """Test ALU with zero result"""
    # Set inputs for subtraction that results in zero
    dut.op.value = ALU_SUB
    dut.a.value = 15
    dut.b.value = 15
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result
    assert dut.result.value == 0, f"Zero result failed: {dut.result.value} != 0"

@cocotb.test()
async def test_alu_negative_result(dut):
    """Test ALU with negative result"""
    # Set inputs for subtraction that results in negative
    dut.op.value = ALU_SUB
    dut.a.value = 10
    dut.b.value = 20
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result (should be -10, which is 0xFFFFFFF6 in 2's complement)
    expected = BinaryValue("11111111111111111111111111110110", 32, bigEndian=False)
    assert dut.result.value == expected, f"Negative result failed: {dut.result.value} != {expected}"

@cocotb.test()
async def test_alu_default_operation(dut):
    """Test ALU with invalid operation (should default to 0)"""
    # Set inputs with invalid operation code
    dut.op.value = 0xF  # Invalid operation
    dut.a.value = 10
    dut.b.value = 20
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result should be 0 (default case)
    assert dut.result.value == 0, f"Default operation failed: {dut.result.value} != 0" 
#!/usr/bin/env python3
"""
Python test for RV32I ALU using cocotb
"""

import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue

# ALU operation codes
ALU_ADD  = 0b0000  # Addition
ALU_SUB  = 0b0001  # Subtraction
ALU_AND  = 0b0010  # Bitwise AND
ALU_OR   = 0b0011  # Bitwise OR
ALU_XOR  = 0b0100  # Bitwise XOR
ALU_SLL  = 0b0101  # Logical left shift
ALU_SRL  = 0b0110  # Logical right shift
ALU_SRA  = 0b0111  # Arithmetic right shift
ALU_SLT  = 0b1000  # Set if less than (signed)
ALU_SLTU = 0b1001  # Set if less than (unsigned)
ALU_SEQ  = 0b1010  # Set if equal
ALU_SNE  = 0b1011  # Set if not equal
ALU_SGE  = 0b1100  # Set if greater than or equal (signed)
ALU_SGEU = 0b1101  # Set if greater than or equal (unsigned)
ALU_SGT  = 0b1110  # Set if greater than (signed)
ALU_SGTU = 0b1111  # Set if greater than (unsigned)

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
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 0, f"Negative flag should be 0 for positive result"
    assert dut.overflow_flag.value == 0, f"Overflow flag should be 0 for normal addition"

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
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 0, f"Negative flag should be 0 for positive result"
    assert dut.overflow_flag.value == 0, f"Overflow flag should be 0 for normal subtraction"

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
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 0, f"Negative flag should be 0 for positive result"

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
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 0, f"Negative flag should be 0 for positive result"

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
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 0, f"Negative flag should be 0 for positive result"

@cocotb.test()
async def test_alu_sll(dut):
    """Test ALU logical left shift operation"""
    # Set inputs
    dut.op.value = ALU_SLL
    dut.a.value = 0x0000000F
    dut.b.value = 4  # Shift by 4 bits
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result
    assert dut.result.value == 0x000000F0, f"SLL failed: {dut.result.value} != 0x000000F0"
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 0, f"Negative flag should be 0 for positive result"

@cocotb.test()
async def test_alu_srl(dut):
    """Test ALU logical right shift operation"""
    # Set inputs
    dut.op.value = ALU_SRL
    dut.a.value = 0x000000F0
    dut.b.value = 4  # Shift by 4 bits
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result
    assert dut.result.value == 0x0000000F, f"SRL failed: {dut.result.value} != 0x0000000F"
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 0, f"Negative flag should be 0 for positive result"

@cocotb.test()
async def test_alu_sra(dut):
    """Test ALU arithmetic right shift operation"""
    # Set inputs
    dut.op.value = ALU_SRA
    dut.a.value = 0x8000000F  # Negative number
    dut.b.value = 4  # Shift by 4 bits
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result (should preserve sign bit)
    assert dut.result.value == 0xF8000000, f"SRA failed: {dut.result.value} != 0xF8000000"
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 1, f"Negative flag should be 1 for negative result"

@cocotb.test()
async def test_alu_slt_signed(dut):
    """Test ALU signed less than operation"""
    # Test positive < positive
    dut.op.value = ALU_SLT
    dut.a.value = 10
    dut.b.value = 20
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SLT failed: 10 < 20 should be 1, got {dut.result.value}"
    
    # Test negative < positive
    dut.a.value = -10
    dut.b.value = 20
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SLT failed: -10 < 20 should be 1, got {dut.result.value}"
    
    # Test positive < negative
    dut.a.value = 10
    dut.b.value = -20
    
    await Timer(1, units='ns')
    assert dut.result.value == 0, f"SLT failed: 10 < -20 should be 0, got {dut.result.value}"

@cocotb.test()
async def test_alu_sltu_unsigned(dut):
    """Test ALU unsigned less than operation"""
    # Test small < large
    dut.op.value = ALU_SLTU
    dut.a.value = 10
    dut.b.value = 20
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SLTU failed: 10 < 20 should be 1, got {dut.result.value}"
    
    # Test large unsigned < small unsigned (negative number treated as large positive)
    dut.a.value = 0x80000000  # Large unsigned
    dut.b.value = 10
    
    await Timer(1, units='ns')
    assert dut.result.value == 0, f"SLTU failed: 0x80000000 < 10 should be 0, got {dut.result.value}"

@cocotb.test()
async def test_alu_seq_equal(dut):
    """Test ALU set if equal operation"""
    # Test equal values
    dut.op.value = ALU_SEQ
    dut.a.value = 42
    dut.b.value = 42
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SEQ failed: 42 == 42 should be 1, got {dut.result.value}"
    
    # Test unequal values
    dut.a.value = 42
    dut.b.value = 43
    
    await Timer(1, units='ns')
    assert dut.result.value == 0, f"SEQ failed: 42 == 43 should be 0, got {dut.result.value}"

@cocotb.test()
async def test_alu_sne_not_equal(dut):
    """Test ALU set if not equal operation"""
    # Test unequal values
    dut.op.value = ALU_SNE
    dut.a.value = 42
    dut.b.value = 43
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SNE failed: 42 != 43 should be 1, got {dut.result.value}"
    
    # Test equal values
    dut.a.value = 42
    dut.b.value = 42
    
    await Timer(1, units='ns')
    assert dut.result.value == 0, f"SNE failed: 42 != 42 should be 0, got {dut.result.value}"

@cocotb.test()
async def test_alu_sge_signed(dut):
    """Test ALU signed greater than or equal operation"""
    # Test equal values
    dut.op.value = ALU_SGE
    dut.a.value = 42
    dut.b.value = 42
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SGE failed: 42 >= 42 should be 1, got {dut.result.value}"
    
    # Test greater than
    dut.a.value = 50
    dut.b.value = 30
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SGE failed: 50 >= 30 should be 1, got {dut.result.value}"
    
    # Test less than
    dut.a.value = 10
    dut.b.value = 30
    
    await Timer(1, units='ns')
    assert dut.result.value == 0, f"SGE failed: 10 >= 30 should be 0, got {dut.result.value}"

@cocotb.test()
async def test_alu_sgeu_unsigned(dut):
    """Test ALU unsigned greater than or equal operation"""
    # Test equal values
    dut.op.value = ALU_SGEU
    dut.a.value = 42
    dut.b.value = 42
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SGEU failed: 42 >= 42 should be 1, got {dut.result.value}"
    
    # Test large unsigned >= small unsigned
    dut.a.value = 0x80000000  # Large unsigned
    dut.b.value = 10
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SGEU failed: 0x80000000 >= 10 should be 1, got {dut.result.value}"

@cocotb.test()
async def test_alu_sgt_signed(dut):
    """Test ALU signed greater than operation"""
    # Test greater than
    dut.op.value = ALU_SGT
    dut.a.value = 50
    dut.b.value = 30
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SGT failed: 50 > 30 should be 1, got {dut.result.value}"
    
    # Test equal values
    dut.a.value = 42
    dut.b.value = 42
    
    await Timer(1, units='ns')
    assert dut.result.value == 0, f"SGT failed: 42 > 42 should be 0, got {dut.result.value}"
    
    # Test less than
    dut.a.value = 10
    dut.b.value = 30
    
    await Timer(1, units='ns')
    assert dut.result.value == 0, f"SGT failed: 10 > 30 should be 0, got {dut.result.value}"

@cocotb.test()
async def test_alu_sgtu_unsigned(dut):
    """Test ALU unsigned greater than operation"""
    # Test greater than
    dut.op.value = ALU_SGTU
    dut.a.value = 50
    dut.b.value = 30
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SGTU failed: 50 > 30 should be 1, got {dut.result.value}"
    
    # Test large unsigned > small unsigned
    dut.a.value = 0x80000000  # Large unsigned
    dut.b.value = 10
    
    await Timer(1, units='ns')
    assert dut.result.value == 1, f"SGTU failed: 0x80000000 > 10 should be 1, got {dut.result.value}"

@cocotb.test()
async def test_alu_zero_result(dut):
    """Test ALU with zero result"""
    # Set inputs for subtraction that results in zero
    dut.op.value = ALU_SUB
    dut.a.value = 15
    dut.b.value = 15
    
    # Wait for combinational logic
    await Timer(1, units='ns')
    
    # Check result and flags
    assert dut.result.value == 0, f"Zero result failed: {dut.result.value} != 0"
    assert dut.zero_flag.value == 1, f"Zero flag should be 1 for zero result"
    assert dut.negative_flag.value == 0, f"Negative flag should be 0 for zero result"

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
    assert dut.zero_flag.value == 0, f"Zero flag should be 0 for non-zero result"
    assert dut.negative_flag.value == 1, f"Negative flag should be 1 for negative result"

@cocotb.test()
async def test_alu_overflow_addition(dut):
    """Test ALU overflow detection for addition"""
    # Test positive overflow
    dut.op.value = ALU_ADD
    dut.a.value = 0x7FFFFFFF  # Max positive 32-bit signed
    dut.b.value = 1
    
    await Timer(1, units='ns')
    assert dut.overflow_flag.value == 1, f"Overflow flag should be 1 for positive overflow"
    
    # Test negative overflow
    dut.a.value = 0x80000000  # Max negative 32-bit signed
    dut.b.value = 0x80000000
    
    await Timer(1, units='ns')
    assert dut.overflow_flag.value == 1, f"Overflow flag should be 1 for negative overflow"

@cocotb.test()
async def test_alu_overflow_subtraction(dut):
    """Test ALU overflow detection for subtraction"""
    # Test positive overflow
    dut.op.value = ALU_SUB
    dut.a.value = 0x7FFFFFFF  # Max positive 32-bit signed
    dut.b.value = 0x80000000  # Max negative 32-bit signed
    
    await Timer(1, units='ns')
    assert dut.overflow_flag.value == 1, f"Overflow flag should be 1 for subtraction overflow"
    
    # Test negative overflow
    dut.a.value = 0x80000000  # Max negative 32-bit signed
    dut.b.value = 0x7FFFFFFF  # Max positive 32-bit signed
    
    await Timer(1, units='ns')
    assert dut.overflow_flag.value == 1, f"Overflow flag should be 1 for subtraction overflow"

@cocotb.test()
async def test_alu_shift_amount_truncation(dut):
    """Test ALU shift operations with large shift amounts"""
    # Test SLL with shift amount > 31 (should use only lower 5 bits)
    dut.op.value = ALU_SLL
    dut.a.value = 0x00000001
    dut.b.value = 33  # Should be truncated to 1 (33 % 32 = 1)
    
    await Timer(1, units='ns')
    assert dut.result.value == 0x00000002, f"SLL with large shift amount failed: {dut.result.value} != 0x00000002"
    
    # Test SRL with shift amount > 31
    dut.op.value = ALU_SRL
    dut.a.value = 0x80000000
    dut.b.value = 33  # Should be truncated to 1
    
    await Timer(1, units='ns')
    assert dut.result.value == 0x40000000, f"SRL with large shift amount failed: {dut.result.value} != 0x40000000"

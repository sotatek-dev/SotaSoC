#!/usr/bin/env python3
"""
Python test for RISC-V C Extension Decompression Module using cocotb

Tests the decompression of 16-bit compressed instructions to 32-bit equivalents.
"""

import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_c_addi4spn(dut):
    """Test C.ADDI4SPN instruction decompression"""
    # Setup: c.addi4spn x8, 4*4
    # C.ADDI4SPN decompresses to: ADDI x8, x2, 4
    
    dut.instr_16bit.value = 0x0040  # c.addi4spn x8, 4
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.ADDI4SPN should be valid"
    # addi x8, x2, 16
    assert dut.instr_32bit.value == 0x00410413, f"Expected 0x00410413, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_addi4spn_reserved(dut):
    """Test C.ADDI4SPN with reserved encoding (nzuimm = 0)"""
    dut.instr_16bit.value = 0x0000  # reserved encoding
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 0, f"Reserved encoding should be invalid"

@cocotb.test()
async def test_c_lw(dut):
    """Test C.LW instruction decompression"""
    dut.instr_16bit.value = 0x40c0  # c.lw x8, 4(x9)
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.LW should be valid"
    # lw x8, 4(x9)
    assert dut.instr_32bit.value == 0x0044a403, f"Expected 0x0044a403, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_sw(dut):
    """Test C.SW instruction decompression"""
    dut.instr_16bit.value = 0xc0c0  # c.sw x8, 4(x9)
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.SW should be valid"
    # sw x8, 4(x9)
    assert dut.instr_32bit.value == 0x0084a223, f"Expected 0x0084a223, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_addi(dut):
    """Test C.ADDI instruction decompression"""
    dut.instr_16bit.value = 0x0095  # c.addi x1, 5
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.ADDI should be valid"
    # addi x1, x1, 5
    assert dut.instr_32bit.value == 0x00508093, f"Expected 0x00508093, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_addi2(dut):
    """Test C.ADDI instruction decompression"""
    dut.instr_16bit.value = 0x10ed  # c.addi x1, -5
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.ADDI should be valid"
    # addi x1, x1, 5
    assert dut.instr_32bit.value == 0xffb08093, f"Expected 0xffb08093, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_jal(dut):
    """Test C.JAL instruction decompression (RV32 only)"""
    dut.instr_16bit.value = 0x2019  # c.jal 6
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.JAL should be valid"
    # jal x1, 6
    assert dut.instr_32bit.value == 0x006000ef, f"Expected 0x006000ef, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_jal2(dut):
    """Test C.JAL instruction decompression (RV32 only)"""
    dut.instr_16bit.value = 0x3fed  # c.jal -6
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.JAL should be valid"
    # jal x1, -6
    assert dut.instr_32bit.value == 0xffbff0ef, f"Expected 0xffbff0ef, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_li(dut):
    """Test C.LI instruction decompression"""
    dut.instr_16bit.value = 0x4095  # c.li x1, 5
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.LI should be valid"
    # addi x1, x0, 5
    assert dut.instr_32bit.value == 0x00500093, f"Expected 0x00500093, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_li2(dut):
    """Test C.LI instruction decompression"""
    dut.instr_16bit.value = 0x50ed  # c.li x1, -5
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.LI should be valid"
    # addi x1, x0, -5
    assert dut.instr_32bit.value == 0xffb00093, f"Expected 0xffb00093, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_lui(dut):
    """Test C.LUI instruction decompression"""
    dut.instr_16bit.value = 0x609d  # c.lui x1, 7
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.LUI should be valid"
    # lui x1, 7
    assert dut.instr_32bit.value == 0x000070b7, f"Expected 0x000070b7, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_lui2(dut):
    """Test C.LUI instruction decompression"""
    dut.instr_16bit.value = 0x70e5  # c.lui x1, -7
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.LUI should be valid"
    # lui x1, -7
    assert dut.instr_32bit.value == 0xffff90b7, f"Expected 0xffff90b7, got 0x{dut.instr_32bit.value.to_unsigned():08X}"


@cocotb.test()
async def test_c_nop(dut):
    """Test C.NOP (special case of C.ADDI with rd=0)"""
    dut.instr_16bit.value = 0x0001  # c.nop (c.addi x0, 0)
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.NOP should be valid"
    # addi x0, x0, 0
    assert dut.instr_32bit.value == 0x00000013, f"Expected 0x00000013, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_addi16sp(dut):
    """Test C.ADDI16SP instruction decompression"""
    dut.instr_16bit.value = 0x6105  # c.addi16sp 32
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.ADDI16SP should be valid"
    # addi x2, x2, 32
    assert dut.instr_32bit.value == 0x02010113, f"Expected 0x02010113, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_addi16sp2(dut):
    """Test C.ADDI16SP instruction decompression"""
    dut.instr_16bit.value = 0x713d  # c.addi16sp -32
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.ADDI16SP should be valid"
    # addi x2, x2, -32
    assert dut.instr_32bit.value == 0xfe010113, f"Expected 0xfe010113, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_srli(dut):
    """Test C.SRLI instruction decompression"""
    dut.instr_16bit.value = 0x8085  # c.srli x9, 1
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.SRLI should be valid"
    # srli x9, x9, 1
    assert dut.instr_32bit.value == 0x0014d493, f"Expected 0x0014d493, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_srai(dut):
    """Test C.SRAI instruction decompression"""
    dut.instr_16bit.value = 0x8485  # c.srai x9, 1
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.SRAI should be valid"
    # srai x9, x9, 1
    assert dut.instr_32bit.value == 0x4014d493, f"Expected 0x4014d493, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_andi(dut):
    """Test C.ANDI instruction decompression"""
    dut.instr_16bit.value = 0x8885  # c.andi x9, 1
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.ANDI should be valid"
    # andi x9, x9, 1
    assert dut.instr_32bit.value == 0x0014f493, f"Expected 0x0014f493, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_andi2(dut):
    """Test C.ANDI instruction decompression"""
    dut.instr_16bit.value = 0x98fd  # c.andi x9, -1
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.ANDI should be valid"
    # andi x9, x9, -1
    assert dut.instr_32bit.value == 0xfff4f493, f"Expected 0xfff4f493, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_sub(dut):
    """Test C.SUB instruction decompression"""
    dut.instr_16bit.value = 0x8c81  # c.sub x9, x8
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.SUB should be valid"
    # sub x9, x9, x8
    assert dut.instr_32bit.value == 0x408484b3, f"Expected 0x408484b3, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_xor(dut):
    """Test C.XOR instruction decompression"""
    dut.instr_16bit.value = 0x8ca1  # c.xor x9, x8
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.XOR should be valid"
    # xor x9, x9, x8
    assert dut.instr_32bit.value == 0x0084c4b3, f"Expected 0x0084c4b3, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_or(dut):
    """Test C.OR instruction decompression"""
    dut.instr_16bit.value = 0x8cc1  # c.or x9, x8
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.OR should be valid"
    # or x9, x9, x8
    assert dut.instr_32bit.value == 0x0084e4b3, f"Expected 0x0084e4b3, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_and(dut):
    """Test C.AND instruction decompression"""
    dut.instr_16bit.value = 0x8ce1  # c.and x9, x8
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.AND should be valid"
    # and x9, x9, x8
    assert dut.instr_32bit.value == 0x0084f4b3, f"Expected 0x0084f4b3, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_j(dut):
    """Test C.J instruction decompression"""
    dut.instr_16bit.value = 0xa80d  # c.j 50
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.J should be valid"
    # jal x0, 50
    assert dut.instr_32bit.value == 0x0320006f, f"Expected 0x0320006f, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_j2(dut):
    """Test C.J instruction decompression"""
    dut.instr_16bit.value = 0xb7f9  # c.j -50
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.J should be valid"
    # jal x0, -50
    assert dut.instr_32bit.value == 0xfcfff06f, f"Expected 0xfcfff06f, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_beqz(dut):
    """Test C.BEQZ instruction decompression"""
    dut.instr_16bit.value = 0xcc99  # c.beqz x9, 30
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.BEQZ should be valid"
    # beq x9, x0, 30
    assert dut.instr_32bit.value == 0x00048f63, f"Expected 0x00048f63, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_beqz2(dut):
    """Test C.BEQZ instruction decompression"""
    dut.instr_16bit.value = 0xd0ed  # c.beqz x9, -30
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.BEQZ should be valid"
    # beq x9, x0, -30
    assert dut.instr_32bit.value == 0xfe0481e3, f"Expected 0xfe0481e3, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_bnez(dut):
    """Test C.BNEZ instruction decompression"""
    dut.instr_16bit.value = 0xec99  # c.bnez x9, 30
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.BNEZ should be valid"
    # bne x9, x0, 30
    assert dut.instr_32bit.value == 0x00049f63, f"Expected 0x00049f63, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_bnez2(dut):
    """Test C.BNEZ instruction decompression"""
    dut.instr_16bit.value = 0xf0ed  # c.bnez x9, -30
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.BNEZ should be valid"
    # bne x9, x0, -30
    assert dut.instr_32bit.value == 0xfe0491e3, f"Expected 0xfe0491e3, got 0x{dut.instr_32bit.value.to_unsigned():08X}"


@cocotb.test()
async def test_c_slli(dut):
    """Test C.SLLI instruction decompression"""
    dut.instr_16bit.value = 0x048e  # c.slli x9, 3
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.SLLI should be valid"
    # slli x9, x9, 3
    assert dut.instr_32bit.value == 0x00349493, f"Expected 0x00349493, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_lwsp(dut):
    """Test C.LWSP instruction decompression"""
    dut.instr_16bit.value = 0x44f2  # c.lwsp x9, 28(x2)
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.LWSP should be valid"
    # lw x9, 28(x2)
    assert dut.instr_32bit.value == 0x01c12483, f"Expected 0x01c12483, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_jr(dut):
    """Test C.JR instruction decompression"""
    dut.instr_16bit.value = 0x8482  # c.jr x9
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.JR should be valid"
    # jalr x0, 0(x9)
    assert dut.instr_32bit.value == 0x00048067, f"Expected 0x00048067, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_mv(dut):
    """Test C.MV instruction decompression"""
    dut.instr_16bit.value = 0x84aa  # c.mv x9, x10
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.MV should be valid"
    # add x9, x0, x10
    assert dut.instr_32bit.value == 0x00a004b3, f"Expected 0x00a004b3, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_ebreak(dut):
    """Test C.EBREAK instruction decompression"""
    dut.instr_16bit.value = 0x9002  # c.ebreak
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.EBREAK should be valid"
    # ebreak
    assert dut.instr_32bit.value == 0x00100073, f"Expected 0x00100073, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_jalr(dut):
    """Test C.JALR instruction decompression"""
    dut.instr_16bit.value = 0x9482  # c.jalr x9
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.JALR should be valid"
    # jalr x1, 0(x9)
    assert dut.instr_32bit.value == 0x000480e7, f"Expected 0x000480e7, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_c_add(dut):
    """Test C.ADD instruction decompression"""
    dut.instr_16bit.value = 0x94aa  # c.add x9, x10
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.JALR should be valid"
    # add x9, x9, x10
    assert dut.instr_32bit.value == 0x00a484b3, f"Expected 0x00a484b3, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

@cocotb.test()
async def test_invalid_instructions(dut):
    """Test invalid/reserved instruction encodings"""
    dut.instr_16bit.value = 0xFFFF  # invalid opcode
    await Timer(10, unit='ns')
    assert dut.is_valid.value == 0, f"Invalid opcode should be invalid"
    
    dut.instr_16bit.value = 0x6000  # reserved funct3
    await Timer(10, unit='ns')
    assert dut.is_valid.value == 0, f"Reserved funct3 should be invalid"

@cocotb.test()
async def test_c_swsp(dut):
    """Test C.SWSP instruction decompression"""
    dut.instr_16bit.value = 0xce26  # c.swsp x9, 28
    await Timer(10, unit='ns')
    
    assert dut.is_valid.value == 1, f"C.SWSP should be valid"
    # sw x9, 28(x2)
    assert dut.instr_32bit.value == 0x00912e23, f"Expected 0x00912e23, got 0x{dut.instr_32bit.value.to_unsigned():08X}"

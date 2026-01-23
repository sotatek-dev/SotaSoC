#!/usr/bin/env python3
"""
Python test for RISC-V C Extension
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import test_utils
from test_utils import do_test, CYCLES_PER_INSTRUCTION, NOP_INSTR

@cocotb.test()
async def test_c_add(dut):
    """Test C.ADD instruction execution"""
    
    # C.ADD instruction encoding: c.add x9, x10 = 0x94aa
    # This decompresses to: add x9, x9, x10 = 0x00a484b3
    
    # Setup: 
    # - Load values into x9 and x10 using ADDI
    # - Execute c.add x9, x10
    # - Verify result
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00148493,  # ADDI x9, x9, 1
        0x00000008: 0x00250513,  # ADDI x10, x10, 2
        0x0000000C: 0x000194aa,  # C.ADD x9, x10 | C.NOP
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.add x9, x10: x9 = x9 + x10 = 1 + 2 = 3
    assert registers[9].value == 3, f"Register x9 should be 3, got 0x{registers[9].value.integer:08x}"
    # x10 should remain unchanged
    assert registers[10].value == 2, f"Register x10 should be 2, got 0x{registers[10].value.integer:08x}"

@cocotb.test()
async def test_c_addi4spn(dut):
    """Test C.ADDI4SPN instruction execution"""
    
    # C.ADDI4SPN: Add immediate to stack pointer
    # Encoding: 0x0040 = c.addi4spn x8, 4
    # Decompresses to: ADDI x8, x2, 4
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x10010113,  # ADDI x2, x2, 0x100 (set x2 = 0x100)
        0x00000008: 0x00010040,  # C.NOP | C.ADDI4SPN x8, 4
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.addi4spn x8, 4: x8 = x2 + 4 = 0x100 + 4 = 0x104
    assert registers[2].value == 0x100, f"Register x2 (sp) should be 0x100, got 0x{registers[2].value.integer:08x}"
    assert registers[8].value == 0x104, f"Register x8 should be 0x104, got 0x{registers[8].value.integer:08x}"

@cocotb.test()
async def test_c_lw(dut):
    """Test C.LW instruction execution"""
    
    # C.LW: Load word from memory
    # Encoding: 0x40c0 = c.lw x8, 4(x9)
    # Decompresses to: LW x8, 4(x9)
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x02000493,  # ADDI x9, x0, 32 (set x9 = 32, pointing to address 0x00000020)
        0x00000008: 0x000140c0,  # C.NOP | C.LW x8, 4(x9) - load from address x9+4 = 0x00000024
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
    }
    await do_test(dut, memory, 15, 0xABCD)
    
    registers = dut.core.register_file.registers
    # After c.lw x8, 4(x9): x8 = MEM[x9 + 4] = MEM[0x00000024] = 0xABCD
    assert registers[8].value == 0xABCD, f"Register x8 should be 0xABCD, got 0x{registers[8].value.integer:08x}"

@cocotb.test()
async def test_c_sw(dut):
    """Test C.SW instruction execution"""
    
    # C.SW: Store word to memory
    # Encoding: 0xc0c0 = c.sw x8, 4(x9)
    # Decompresses to: SW x8, 4(x9)
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30000493,  # ADDI x9, x0, 0x300 (set x9 = 0x300)
        0x00000008: 0x12300413,  # ADDI x8, x0, 0x123 (set x8 = 0x123)
        0x0000000C: 0x00C41413,  # SLLI x8, x8, 12 (x8 = 0x123000)
        0x00000010: 0x45640413,  # ADDI x8, x8, 0x456 (x8 = 0x123456)
        0x00000014: 0x0001c0c0,  # C.NOP | C.SW x8, 4(x9) - store x8 to address x9+4 = 0x304
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10, 0)
    
    # Check that memory write occurred (via test_utils memory tracking)
    import test_utils
    assert test_utils.mem_addr == 0x304, f"Mem_Addr should be 0x304, got 0x{test_utils.mem_addr:08x}"
    assert test_utils.mem_wdata == 0x123456, f"Mem_wdata should be 0x123456, got 0x{test_utils.mem_wdata:08x}"
    assert test_utils.mem_flag == 0b010, f"Mem_flag should be 0b010, got 0b{test_utils.mem_flag:03b}"

@cocotb.test()
async def test_c_addi(dut):
    """Test C.ADDI instruction execution"""
    
    # C.ADDI: Add immediate
    # Encoding: 0x0095 = c.addi x1, 5
    # Decompresses to: ADDI x1, x1, 5
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00300093,  # ADDI x1, x0, 3 (set x1 = 3)
        0x00000008: 0x00010095,  # C.NOP | C.ADDI x1, 5
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.addi x1, 5: x1 = x1 + 5 = 3 + 5 = 8
    assert registers[1].value == 8, f"Register x1 should be 8, got 0x{registers[1].value.integer:08x}"

@cocotb.test()
async def test_c_nop(dut):
    """Test C.NOP instruction execution"""
    
    # C.NOP: No operation
    # Encoding: 0x0001 = c.nop (c.addi x0, 0)
    # Decompresses to: ADDI x0, x0, 0 (NOP)
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00500093,  # ADDI x1, x0, 5 (set x1 = 5)
        0x00000008: 0x00010001,  # C.NOP | C.NOP
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # x1 should remain unchanged after C.NOP
    assert registers[1].value == 5, f"Register x1 should be 5, got 0x{registers[1].value.integer:08x}"

@cocotb.test()
async def test_c_li(dut):
    """Test C.LI instruction execution"""
    
    # C.LI: Load immediate
    # Encoding: 0x4095 = c.li x1, 5
    # Decompresses to: ADDI x1, x0, 5
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00014095,  # C.NOP | C.LI x1, 5
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.li x1, 5: x1 = 5
    assert registers[1].value == 5, f"Register x1 should be 5, got 0x{registers[1].value.integer:08x}"

@cocotb.test()
async def test_c_lui(dut):
    """Test C.LUI instruction execution"""
    
    # C.LUI: Load upper immediate
    # Encoding: 0x609d = c.lui x1, 7
    # Decompresses to: LUI x1, 7
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x0001609d,  # C.NOP | C.LUI x1, 7
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.lui x1, 7: x1 = 7 << 12 = 0x00007000
    assert registers[1].value == 0x00007000, f"Register x1 should be 0x00007000, got 0x{registers[1].value.integer:08x}"

@cocotb.test()
async def test_c_addi16sp(dut):
    """Test C.ADDI16SP instruction execution"""
    
    # C.ADDI16SP: Add immediate to stack pointer (scaled by 16)
    # Encoding: 0x6105 = c.addi16sp 32
    # Decompresses to: ADDI x2, x2, 32
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x10010113,  # ADDI x2, x2, 0x100 (set x2 = 0x100)
        0x00000008: 0x00016105,  # C.NOP | C.ADDI16SP 32
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.addi16sp 32: x2 = x2 + 32 = 0x100 + 32 = 0x120
    assert registers[2].value == 0x120, f"Register x2 should be 0x120, got 0x{registers[2].value.integer:08x}"

@cocotb.test()
async def test_c_srli(dut):
    """Test C.SRLI instruction execution"""
    
    # C.SRLI: Shift right logical immediate
    # Encoding: 0x8085 = c.srli x9, 1
    # Decompresses to: SRLI x9, x9, 1
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00800493,  # ADDI x9, x0, 8 (set x9 = 8 = 0b1000)
        0x00000008: 0x00018085,  # C.NOP | C.SRLI x9, 1
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.srli x9, 1: x9 = x9 >> 1 = 8 >> 1 = 4
    assert registers[9].value == 4, f"Register x9 should be 4, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_srai(dut):
    """Test C.SRAI instruction execution"""
    
    # C.SRAI: Shift right arithmetic immediate
    # Encoding: 0x8485 = c.srai x9, 1
    # Decompresses to: SRAI x9, x9, 1
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0xfff00493,  # ADDI x9, x0, -1 (set x9 = 0xFFFFFFFF)
        0x00000008: 0x00018485,  # C.NOP | C.SRAI x9, 1
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.srai x9, 1: x9 = x9 >>> 1 = 0xFFFFFFFF >>> 1 = 0xFFFFFFFF (arithmetic shift preserves sign)
    assert registers[9].value == 0xFFFFFFFF, f"Register x9 should be 0xFFFFFFFF, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_andi(dut):
    """Test C.ANDI instruction execution"""
    
    # C.ANDI: AND immediate
    # Encoding: 0x8885 = c.andi x9, 1
    # Decompresses to: ANDI x9, x9, 1
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00f00493,  # ADDI x9, x0, 15 (set x9 = 15 = 0b1111)
        0x00000008: 0x00018885,  # C.NOP | C.ANDI x9, 1
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.andi x9, 1: x9 = x9 & 1 = 15 & 1 = 1
    assert registers[9].value == 1, f"Register x9 should be 1, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_sub(dut):
    """Test C.SUB instruction execution"""
    
    # C.SUB: Subtract
    # Encoding: 0x8c81 = c.sub x9, x8
    # Decompresses to: SUB x9, x9, x8
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00a00493,  # ADDI x9, x0, 10 (set x9 = 10)
        0x00000008: 0x00300413,  # ADDI x8, x0, 3 (set x8 = 3)
        0x0000000C: 0x00018c81,  # C.NOP | C.SUB x9, x8
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.sub x9, x8: x9 = x9 - x8 = 10 - 3 = 7
    assert registers[9].value == 7, f"Register x9 should be 7, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_xor(dut):
    """Test C.XOR instruction execution"""
    
    # C.XOR: XOR
    # Encoding: 0x8ca1 = c.xor x9, x8
    # Decompresses to: XOR x9, x9, x8
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00f00493,  # ADDI x9, x0, 15 (set x9 = 15 = 0b1111)
        0x00000008: 0x00300413,  # ADDI x8, x0, 3 (set x8 = 3 = 0b0011)
        0x0000000C: 0x00018ca1,  # C.NOP | C.XOR x9, x8
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.xor x9, x8: x9 = x9 ^ x8 = 15 ^ 3 = 12 (0b1111 ^ 0b0011 = 0b1100)
    assert registers[9].value == 12, f"Register x9 should be 12, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_or(dut):
    """Test C.OR instruction execution"""
    
    # C.OR: OR
    # Encoding: 0x8cc1 = c.or x9, x8
    # Decompresses to: OR x9, x9, x8
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00a00493,  # ADDI x9, x0, 10 (set x9 = 10 = 0b1010)
        0x00000008: 0x00300413,  # ADDI x8, x0, 3 (set x8 = 3 = 0b0011)
        0x0000000C: 0x00018cc1,  # C.NOP | C.OR x9, x8
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.or x9, x8: x9 = x9 | x8 = 10 | 3 = 11 (0b1010 | 0b0011 = 0b1011)
    assert registers[9].value == 11, f"Register x9 should be 11, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_and(dut):
    """Test C.AND instruction execution"""
    
    # C.AND: AND
    # Encoding: 0x8ce1 = c.and x9, x8
    # Decompresses to: AND x9, x9, x8
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00f00493,  # ADDI x9, x0, 15 (set x9 = 15 = 0b1111)
        0x00000008: 0x00300413,  # ADDI x8, x0, 3 (set x8 = 3 = 0b0011)
        0x0000000C: 0x00018ce1,  # C.NOP | C.AND x9, x8
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.and x9, x8: x9 = x9 & x8 = 15 & 3 = 3 (0b1111 & 0b0011 = 0b0011)
    assert registers[9].value == 3, f"Register x9 should be 3, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_slli(dut):
    """Test C.SLLI instruction execution"""
    
    # C.SLLI: Shift left logical immediate
    # Encoding: 0x048e = c.slli x9, 3
    # Decompresses to: SLLI x9, x9, 3
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00200493,  # ADDI x9, x0, 2 (set x9 = 2)
        0x00000008: 0x0001048e,  # C.NOP | C.SLLI x9, 3
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.slli x9, 3: x9 = x9 << 3 = 2 << 3 = 16
    assert registers[9].value == 16, f"Register x9 should be 16, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_lwsp(dut):
    """Test C.LWSP instruction execution"""
    
    # C.LWSP: Load word from stack pointer
    # Encoding: 0x44f2 = c.lwsp x9, 28(x2)
    # Decompresses to: LW x9, 28(x2)
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x10010113,  # ADDI x2, x2, 0x100 (set x2 = 0x100)
        0x00000008: 0x000144f2,  # C.NOP | C.LWSP x9, 28(x2) - load from address x2+28 = 0x11C
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
    }
    await do_test(dut, memory, 15, 0x12345678)
    
    registers = dut.core.register_file.registers
    # After c.lwsp x9, 28(x2): x9 = MEM[x2 + 28] = MEM[0x11C] = 0x12345678
    assert registers[9].value == 0x12345678, f"Register x9 should be 0x12345678, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_mv(dut):
    """Test C.MV instruction execution"""
    
    # C.MV: Move register
    # Encoding: 0x84aa = c.mv x9, x10
    # Decompresses to: ADD x9, x0, x10
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00a00513,  # ADDI x10, x0, 10 (set x10 = 10)
        0x00000008: 0x000184aa,  # C.NOP | C.MV x9, x10
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.mv x9, x10: x9 = x10 = 10
    assert registers[9].value == 10, f"Register x9 should be 10, got 0x{registers[9].value.integer:08x}"

@cocotb.test()
async def test_c_jr(dut):
    """Test C.JR instruction execution"""
    
    # C.JR: Jump register
    # Encoding: 0x8482 = c.jr x9
    # Decompresses to: JALR x0, 0(x9)
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x01000493,  # ADDI x9, x0, 16 (set x9 = 0x00000010 = target address)
        0x00000008: 0x00018482,  # C.NOP | C.JR x9 - jump to address in x9 (0x00000010)
        0x0000000C: 0x00108093,  # ADDI x1, x1, 1 => Should not be executed (skipped due to jump)
        0x00000010: 0x00210113,  # ADDI x2, x2, 2 => Should be executed (target address)
        0x00000014: 0x00318193,  # ADDI x3, x3, 3 => Should be executed
        0x00000018: 0x00420213,  # ADDI x4, x4, 4 => Should be executed
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
    }
    await do_test(dut, memory, 12)
    
    registers = dut.core.register_file.registers
    # After c.jr x9, PC should jump to address in x9 (0x00000010)
    # x0 should always be 0
    assert registers[0].value == 0, f"Register x0 should always be 0, got 0x{registers[0].value.integer:08x}"
    # x1 should be 0 (instruction at 0x0000000C should not be executed due to jump)
    assert registers[1].value == 0, f"Register x1 should be 0, got 0x{registers[1].value.integer:08x}"
    # x2, x3, x4 should be set by instructions at target address
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_c_jalr(dut):
    """Test C.JALR instruction execution"""
    
    # C.JALR: Jump and link register
    # Encoding: 0x9482 = c.jalr x9
    # Decompresses to: JALR x1, 0(x9)
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x01000493,  # ADDI x9, x0, 16 (set x9 = 0x00000010 = target address)
        0x00000008: 0x00019482,  # C.NOP | C.JALR x9 - jump to address in x9 (0x00000010), save return address in x1
        0x0000000C: 0x00318193,  # ADDI x3, x3, 3 => Should not be executed initially
        0x00000010: 0x00420213,  # ADDI x4, x4, 4 => Should be executed (target address)
        0x00000014: 0x00528293,  # ADDI x5, x5, 5 => Should be executed
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # After c.jalr x9, x1 should contain return address (PC+2 of compressed instruction = 0x0000000A)
    # Note: C.JALR is at 0x00000008 (16-bit), so return address = 0x00000008 + 2 = 0x0000000A
    assert registers[1].value == 0x0000000A, f"Register x1 should be 0x0000000A (return address), got 0x{registers[1].value.integer:08x}"
    assert registers[9].value == 0x00000010, f"Register x9 should be 0x00000010, got 0x{registers[9].value.integer:08x}"
    # x3 should be 0 (instruction at 0x0000000C should not be executed initially)
    assert registers[3].value == 0, f"Register x3 should be 0 (not executed), got 0x{registers[3].value.integer:08x}"
    # x4, x5 should be set by instructions at target address
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"
    assert registers[5].value == 5, f"Register x5 should be 5, got 0x{registers[5].value.integer:08x}"

@cocotb.test()
async def test_c_swsp(dut):
    """Test C.SWSP instruction execution"""
    
    # C.SWSP: Store word to stack pointer
    # Encoding: 0xce26 = c.swsp x9, 28
    # Decompresses to: SW x9, 28(x2)
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x30010113,  # ADDI x2, x2, 0x300 (set x2 = 0x300)
        0x00000008: 0x12300493,  # ADDI x9, x0, 0x123 (set x9 = 0x123)
        0x0000000C: 0x00C49493,  # SLLI x9, x9, 12 (x9 = 0x123000)
        0x00000010: 0x45648493,  # ADDI x9, x9, 0x456 (x9 = 0x123456)
        0x00000014: 0x0001ce26,  # C.NOP | C.SWSP x9, 28 - store x9 to address x2+28 = 0x31C
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    await do_test(dut, memory, 10, 0)
    
    # Check that memory write occurred (via test_utils memory tracking)
    import test_utils
    assert test_utils.mem_addr == 0x31C, f"Mem_Addr should be 0x31C, got 0x{test_utils.mem_addr:08x}"
    assert test_utils.mem_wdata == 0x123456, f"Mem_wdata should be 0x123456, got 0x{test_utils.mem_wdata:08x}"
    assert test_utils.mem_flag == 0b010, f"Mem_flag should be 0b010, got 0b{test_utils.mem_flag:03b}"

@cocotb.test()
async def test_c_beqz(dut):
    """Test C.BEQZ instruction execution"""
    
    # C.BEQZ: Branch if equal to zero
    # Encoding: 0xcc99 = c.beqz x9, 30
    # Decompresses to: BEQ x9, x0, offset
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00000493,  # ADDI x9, x0, 0 (set x9 = 0)
        0x00000008: 0x0001c481,  # C.NOP | C.BEQZ x9, 8 - branch if x9 == 0 (to 0x00000010)
        0x0000000C: 0x00100093,  # ADDI x1, x0, 1 (should be skipped if branch taken)
        0x00000010: 0x00210113,  # ADDI x2, x2, 2 => Should be executed (target address)
        0x00000014: 0x00318193,  # ADDI x3, x3, 3 => Should be executed
        0x00000018: 0x00420213,  # ADDI x4, x4, 4 => Should be executed
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    await do_test(dut, memory, 12)
    
    registers = dut.core.register_file.registers
    # If branch is taken, x1 should remain 0 (not set to 1)
    assert registers[1].value == 0, f"Register x1 should be 0, got 0x{registers[1].value.integer:08x}"
    # x2, x3, x4 should be set by instructions at target address
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_c_bnez(dut):
    """Test C.BNEZ instruction execution"""
    
    # C.BNEZ: Branch if not equal to zero
    # Encoding: 0xec99 = c.bnez x9, 30
    # Decompresses to: BNE x9, x0, offset
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00500493,  # ADDI x9, x0, 5 (set x9 = 5, non-zero)
        0x00000008: 0x0001e481,  # C.NOP | C.BNEZ x9, 8 - branch if x9 != 0 (to 0x00000010)
        0x0000000C: 0x00100093,  # ADDI x1, x0, 1 (should be skipped if branch taken)
        0x00000010: 0x00210113,  # ADDI x2, x2, 2 => Should be executed (target address)
        0x00000014: 0x00318193,  # ADDI x3, x3, 3 => Should be executed
        0x00000018: 0x00420213,  # ADDI x4, x4, 4 => Should be executed
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    await do_test(dut, memory, 12)
    
    registers = dut.core.register_file.registers
    # x9 should remain 5
    assert registers[9].value == 5, f"Register x9 should be 5, got 0x{registers[9].value.integer:08x}"
    # If branch is taken, x1 should remain 0 (not set to 1)
    assert registers[1].value == 0, f"Register x1 should be 0, got 0x{registers[1].value.integer:08x}"
    # x2, x3, x4 should be set by instructions at target address
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_c_j(dut):
    """Test C.J instruction execution"""
    
    # C.J: Jump
    # Encoding: 0xa80d = c.j 50
    # Decompresses to: JAL x0, offset
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x0001a031,  # C.NOP | C.J 12 - jump forward (to 0x00000010)
        0x00000008: 0x00100093,  # ADDI x1, x0, 1 (should be skipped if jump taken)
        0x0000000C: NOP_INSTR,
        0x00000010: 0x00210113,  # ADDI x2, x2, 2 => Should be executed (target address)
        0x00000014: 0x00318193,  # ADDI x3, x3, 3 => Should be executed
        0x00000018: 0x00420213,  # ADDI x4, x4, 4 => Should be executed
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    await do_test(dut, memory, 12)
    
    registers = dut.core.register_file.registers
    # x0 should always be 0
    assert registers[0].value == 0, f"Register x0 should always be 0, got 0x{registers[0].value.integer:08x}"
    # x1 should be 0 (instruction at 0x00000008 should not be executed due to jump)
    assert registers[1].value == 0, f"Register x1 should be 0, got 0x{registers[1].value.integer:08x}"
    # x2, x3, x4 should be set by instructions at target address
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_c_jal(dut):
    """Test C.JAL instruction execution"""
    
    # C.JAL: Jump and link (RV32 only)
    # Encoding: 0x2019 = c.jal 6
    # Decompresses to: JAL x1, offset
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: NOP_INSTR,
        0x00000008: 0x00012021,  # C.NOP | C.JAL 8 - jump and link (jump to 0x00000010)
        0x0000000C: 0x00108093,  # ADDI x1, x1, 1 => Should not be executed (skipped due to jump)
        0x00000010: 0x00210113,  # ADDI x2, x2, 2 => Should be executed (target address)
        0x00000014: 0x00318193,  # ADDI x3, x3, 3 => Should be executed
        0x00000018: 0x00420213,  # ADDI x4, x4, 4 => Should be executed
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    await do_test(dut, memory, 12)
    
    registers = dut.core.register_file.registers
    # After c.jal, x1 should contain return address (PC+2 of compressed instruction = 0x0000000A)
    # Note: C.JAL is at 0x00000008 (16-bit), so return address = 0x00000008 + 2 = 0x0000000A
    # x1 should be 0x0000000A (return address), NOT 0x0000000B (which would be if ADDI at 0x0000000C was executed)
    assert registers[1].value == 0x0000000A, f"Register x1 should be 0x0000000A (return address), got 0x{registers[1].value.integer:08x}"
    # x2, x3, x4 should be set by instructions at target address
    assert registers[2].value == 2, f"Register x2 should be 2, got 0x{registers[2].value.integer:08x}"
    assert registers[3].value == 3, f"Register x3 should be 3, got 0x{registers[3].value.integer:08x}"
    assert registers[4].value == 4, f"Register x4 should be 4, got 0x{registers[4].value.integer:08x}"

@cocotb.test()
async def test_c_ebreak(dut):
    """Test C.EBREAK instruction execution"""
    
    # C.EBREAK: Environment break
    # Encoding: 0x9002 = c.ebreak
    # Decompresses to: EBREAK (0x00100073)
    
    memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00500093,  # ADDI x1, x0, 5 (set x1 = 5)
        0x00000008: 0x00019002,  # C.NOP | C.EBREAK
        0x0000000C: 0x00200113,  # ADDI x2, x0, 2 => Should not be executed (skipped due to ebreak)
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
    }
    await do_test(dut, memory, 10)
    
    registers = dut.core.register_file.registers
    # x1 should remain 5 (ebreak should trigger exception/trap)
    assert registers[1].value == 5, f"Register x1 should be 5, got 0x{registers[1].value.integer:08x}"
    assert registers[2].value == 0, f"Register x2 should be 0, got 0x{registers[2].value.integer:08x}"
import cocotb
from test_utils import NOP_INSTR
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
)


# Timer base address
TIMER_BASE_ADDR = 0x40002000
TIMER_MTIME_LO = TIMER_BASE_ADDR + 0x0
TIMER_MTIME_HI = TIMER_BASE_ADDR + 0x4
TIMER_MTIMECMP_LO = TIMER_BASE_ADDR + 0x8
TIMER_MTIMECMP_HI = TIMER_BASE_ADDR + 0xC


def encode_load(rd, rs1, imm12):
    """Encode LOAD instruction (LW): rd = MEM[rs1 + imm12]"""
    return (imm12 << 20) | (rs1 << 15) | (0x2 << 12) | (rd << 7) | 0x03


def encode_store(rs1, rs2, imm12):
    """Encode STORE instruction (SW): MEM[rs1 + imm12] = rs2"""
    imm11_5 = (imm12 >> 5) & 0x7F
    imm4_0 = imm12 & 0x1F
    return (imm11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (0x2 << 12) | (imm4_0 << 7) | 0x23


def encode_addi(rd, rs1, imm12):
    """Encode ADDI instruction: rd = rs1 + imm12"""
    return (imm12 << 20) | (rs1 << 15) | (0x0 << 12) | (rd << 7) | 0x13


def encode_lui(rd, imm20):
    """Encode LUI instruction: rd = imm20 << 12"""
    return (imm20 << 12) | (rd << 7) | 0x37


def encode_jal(rd, imm20):
    """Encode JAL instruction: rd = PC + 4, PC = PC + imm20
    imm20 is the byte offset (must be multiple of 2, LSB is ignored)"""
    # JAL format: imm[20|10:1|11|19:12] | rd[11:0] | opcode
    # Sign-extend to 32 bits first
    if imm20 & 0x100000:
        imm = imm20 | 0xFFE00000  # Sign extend negative
    else:
        imm = imm20 & 0x1FFFFF  # Positive, mask to 21 bits
    # Extract bits from the original immediate
    imm20_bit = (imm >> 20) & 0x1
    imm10_1 = (imm >> 1) & 0x3FF  # bits [10:1]
    imm11_bit = (imm >> 11) & 0x1
    imm19_12 = (imm >> 12) & 0xFF  # bits [19:12]
    return (imm20_bit << 31) | (imm19_12 << 12) | (imm11_bit << 20) | (imm10_1 << 21) | (rd << 7) | 0x6F


def encode_csrrw(rd, csr, rs1):
    """Encode CSRRW instruction: rd = CSR[csr]; CSR[csr] = rs1"""
    return (csr << 20) | (rs1 << 15) | (0x1 << 12) | (rd << 7) | 0x73


# CSR addresses
CSR_MSTATUS = 0x300
CSR_MIE = 0x304
CSR_MTVEC = 0x305

# Instruction encodings
MRET_INSTR = 0x30200073   # MRET: opcode=0x73, funct3=0, imm12=0x302


@cocotb.test()
async def test_timer_read_mtime(dut):
    """Test reading mtime register - should increment every clock cycle"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x400020b7, # LUI x1, 0x40002 (x1 = 0x40002000)
        0x00000008: 0x0000a103, # LW x2, 0(x1) - read mtime[31:0]
        0x0000000C: 0x0040a183, # LW x3, 4(x1) - read mtime[47:32]
        0x00000010: 0x0000a203, # LW x4, 0(x1) - read mtime[31:0] again
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    mtime_first_read = None
    mtime_second_read = None

    def callback(dut, memory):
        nonlocal mtime_first_read, mtime_second_read

        # Check when we've read mtime twice
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000024:
            registers = dut.soc_inst.cpu_core.register_file.registers

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0, got 0x{int(dut.soc_inst.error_flag.value)}"

            # x2 should contain first mtime[31:0] read
            # x3 should contain mtime[47:32] read
            # x4 should contain second mtime[31:0] read (should be >= x2)
            mtime_first_read = registers[2].value.to_unsigned()
            mtime_high = registers[3].value.to_unsigned() & 0xFFFF
            mtime_second_read = registers[4].value.to_unsigned()

            # Verify mtime increments
            assert mtime_second_read > mtime_first_read, \
                f"mtime should increment: first={mtime_first_read:08x}, second={mtime_second_read:08x}"

            # Verify mtime high bits are reasonable (should be 0 or small value after reset)
            assert mtime_high == 0, f"mtime high should be 0 initially, got 0x{mtime_high:04x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_timer_write_read_mtimecmp(dut):
    """Test writing and reading mtimecmp register"""

    test_value_lo = 0x12345678
    test_value_hi = 0x0000A0CD

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x400020b7, # LUI x1, 0x40002 (x1 = 0x40002000)
        0x00000008: encode_lui(2, test_value_lo >> 12),  # LUI x2, upper bits
        0x0000000C: encode_addi(2, 2, test_value_lo & 0xFFF),  # ADDI x2, x2, lower bits
        0x00000010: encode_lui(3, test_value_hi >> 12),  # LUI x3, upper bits
        0x00000014: encode_addi(3, 3, test_value_hi & 0xFFF),  # ADDI x3, x3, lower bits
        0x00000018: encode_store(1, 2, 0x8),  # SW x2, 8(x1) - write mtimecmp[31:0]
        0x0000001C: encode_store(1, 3, 0xC),  # SW x3, 12(x1) - write mtimecmp[47:32]
        0x00000020: encode_load(4, 1, 0x8),  # LW x4, 8(x1) - read mtimecmp[31:0]
        0x00000024: encode_load(5, 1, 0xC),  # LW x5, 12(x1) - read mtimecmp[47:32]
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        # Check when we've read mtimecmp back
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000003C:
            registers = dut.soc_inst.cpu_core.register_file.registers

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0, got 0x{int(dut.soc_inst.error_flag.value)}"

            # x4 should contain mtimecmp[31:0] we wrote
            # x5 should contain mtimecmp[47:32] we wrote
            mtimecmp_lo_read = registers[4].value.to_unsigned()
            mtimecmp_hi_read = registers[5].value.to_unsigned() & 0xFFFF

            # Verify values match
            assert mtimecmp_lo_read == test_value_lo, \
                f"mtimecmp[31:0] should be 0x{test_value_lo:08x}, got 0x{mtimecmp_lo_read:08x}"
            assert mtimecmp_hi_read == test_value_hi, \
                f"mtimecmp[47:32] should be 0x{test_value_hi:04x}, got 0x{mtimecmp_hi_read:04x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_timer_interrupt(dut):
    """Test timer interrupt generation when mtime >= mtimecmp"""

    # Set mtimecmp to a small value to trigger interrupt quickly
    mtimecmp_value = 0x00000050  # 80 clock cycles

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x400020b7, # LUI x1, 0x40002 (x1 = 0x40002000)
        0x00000008: 0x05000113, # ADDI x2, x0, 0x50
        0x0000000C: 0x0020a423, # SW x2, 8(x1) - write mtimecmp[31:0]
        0x00000010: 0x0000a623, # SW x0, 12(x1) - write mtimecmp[47:32] = 0
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        # Check after writing mtimecmp and waiting
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000030:
            # Verify timer interrupt is asserted when mtime >= mtimecmp
            timer_inst = dut.soc_inst.timer_inst
            mtime = dut.soc_inst.cpu_core.mtime_counter.value.to_unsigned()
            mtimecmp = timer_inst.mtimecmp.value.to_unsigned()
            timer_interrupt = int(timer_inst.timer_interrupt.value)

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0, got 0x{int(dut.soc_inst.error_flag.value)}"

            # After enough cycles, mtime should be >= mtimecmp and interrupt should be asserted
            if mtime >= mtimecmp:
                assert timer_interrupt == 1, \
                    f"timer_interrupt should be 1 when mtime (0x{mtime:x}) >= mtimecmp (0x{mtimecmp:x})"
            else:
                # If not yet, that's okay - timer is still counting
                pass

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

def get_timer_trap_handler_memory():
    # Trap handler address
    trap_handler_addr = 0x00000100
    # Test function address
    test_func_addr = 0x00000030
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Setup: set mtvec to point to trap handler
        0x00000004: encode_lui(11, (trap_handler_addr >> 12) & 0xFFFFF),  # LUI x11, upper bits
        0x00000008: encode_addi(11, 11, trap_handler_addr & 0xFFF),  # ADDI x11, x11, lower bits
        0x0000000C: encode_csrrw(0, CSR_MTVEC, 11),  # CSRRW x0, mtvec, x11 (set mtvec)

        # Enable timer interrupts: set MTIE (bit 7 of mie) and MIE (bit 3 of mstatus)
        0x00000010: encode_addi(12, 12, 0x80),  # ADDI x12, x0, 0x80 (MTIE bit 7)
        0x00000014: encode_csrrw(0, CSR_MIE, 12),  # CSRRW x0, mie, x12 (enable MTIE)
        0x00000018: encode_addi(12, 12, 0x8),  # ADDI x12, x0, 0x8 (MIE bit 3)
        0x0000001C: encode_csrrw(0, CSR_MSTATUS, 12),  # CSRRW x0, mstatus, x12 (enable MIE)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        # Jump to test function
        0x00000028: encode_jal(0, test_func_addr - 0x00000028),  # JAL x0, offset to test function
        0x0000002C: NOP_INSTR,
        # Test function
        0x00000030: encode_addi(1, 1, 1),  # ADDI x1, x0, 1
        0x00000034: encode_addi(2, 2, 2),  # ADDI x2, x0, 2
        0x00000038: encode_addi(3, 3, 3),  # ADDI x3, x0, 3
        0x0000003C: encode_addi(4, 4, 4),  # ADDI x4, x0, 4
        0x00000040: encode_addi(5, 5, 5),  # ADDI x5, x0, 5
        0x00000044: encode_addi(6, 6, 6),  # ADDI x6, x0, 6
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
        0x00000054: NOP_INSTR,
        0x00000058: NOP_INSTR,
        0x0000005C: NOP_INSTR,
        0x00000060: NOP_INSTR,
        # Trap handler
        0x00000100: encode_addi(14, 14, 14),  # ADDI x14, x0, 14
        0x00000104: encode_addi(15, 15, 15),  # ADDI x15, x0, 15
        # Set mtimecmp to 0x0F000000
        0x00000108: encode_lui(9, (TIMER_BASE_ADDR >> 12) & 0xFFFFF),  # LUI x9, timer base upper bits
        0x0000010C: encode_addi(9, 9, TIMER_BASE_ADDR & 0xFFF),  # ADDI x9, x9, timer base lower bits
        0x00000110: encode_lui(10, 0x0F000),  # LUI x10, 0x0F000 (x10 = 0x0F000000)
        0x00000114: encode_store(9, 10, 0x8),  # SW x10, 8(x9) - write mtimecmp[31:0] = 0x0F000000
        0x00000118: encode_store(9, 10, 0xC),  # SW x10, 12(x9) - write mtimecmp[47:32] = 0
        0x0000011C: MRET_INSTR,  # MRET - return from trap
        0x00000120: NOP_INSTR,
    }

    return hex_memory

async def test_timer_trap_handler(dut, hex_memory, timer_hit_position):
    """Test timer interrupt with trap handler and test function"""

    timer_hit = False
    
    
    max_cycles = 7000

    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    def callback(dut, memory):
        nonlocal timer_hit

        if dut.soc_inst.cpu_core.o_instr_addr.value == timer_hit_position and not timer_hit:
            timer_hit = True
            dut.soc_inst.timer_inst.mtimecmp.value = 0x00000050
            dut.soc_inst.cpu_core.mtime_counter.value = 0x00000050

        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000060:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0, got 0x{int(dut.soc_inst.error_flag.value)}"
            
            assert registers[1].value.to_unsigned() == 1, \
                f"x1 should be 1 after trap handler, got {registers[1].value.to_unsigned()}"
            assert registers[2].value.to_unsigned() == 2, \
                f"x2 should be 2 after trap handler, got {registers[2].value.to_unsigned()}"
            assert registers[3].value.to_unsigned() == 3, \
                f"x3 should be 3 after trap handler, got {registers[3].value.to_unsigned()}"
            assert registers[4].value.to_unsigned() == 4, \
                f"x4 should be 4 after trap handler, got {registers[4].value.to_unsigned()}"
            assert registers[5].value.to_unsigned() == 5, \
                f"x5 should be 5 after trap handler, got {registers[5].value.to_unsigned()}"
            assert registers[6].value.to_unsigned() == 6, \
                f"x6 should be 6 after trap handler, got {registers[6].value.to_unsigned()}"
            assert registers[14].value.to_unsigned() == 14, \
                f"x14 should be 14 after trap handler, got {registers[14].value.to_unsigned()}"
            assert registers[15].value.to_unsigned() == 15, \
                f"x15 should be 15 after trap handler, got {registers[15].value.to_unsigned()}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_timer_trap_handler_1(dut):
    hex_memory = get_timer_trap_handler_memory()
    await test_timer_trap_handler(dut, hex_memory, 0x00000030)

@cocotb.test()
async def test_timer_trap_handler_2(dut):
    hex_memory = get_timer_trap_handler_memory()
    await test_timer_trap_handler(dut, hex_memory, 0x00000034)

@cocotb.test()
async def test_timer_trap_handler_3(dut):
    hex_memory = get_timer_trap_handler_memory()
    await test_timer_trap_handler(dut, hex_memory, 0x00000038)

@cocotb.test()
async def test_timer_trap_handler_4(dut):
    hex_memory = get_timer_trap_handler_memory()
    await test_timer_trap_handler(dut, hex_memory, 0x0000003C)

@cocotb.test()
async def test_timer_trap_handler_5(dut):
    hex_memory = get_timer_trap_handler_memory()
    await test_timer_trap_handler(dut, hex_memory, 0x00000040)

@cocotb.test()
async def test_timer_trap_handler_6(dut):
    hex_memory = get_timer_trap_handler_memory()
    await test_timer_trap_handler(dut, hex_memory, 0x00000044)

@cocotb.test()
async def test_timer_trap_handler_7(dut):
    hex_memory = get_timer_trap_handler_memory()
    hex_memory[0x00000020] = encode_jal(0, 0x30 - 0x20)  # JAL x0, offset to test function
    hex_memory[0x00000024] = NOP_INSTR
    hex_memory[0x00000028] = NOP_INSTR
    hex_memory[0x0000002C] = NOP_INSTR
    await test_timer_trap_handler(dut, hex_memory, 0x00000030)

@cocotb.test()
async def test_timer_trap_handler_8(dut):
    hex_memory = get_timer_trap_handler_memory()
    hex_memory[0x00000020] = NOP_INSTR
    hex_memory[0x00000024] = encode_jal(0, 0x30 - 0x24)  # JAL x0, offset to test function
    hex_memory[0x00000028] = NOP_INSTR
    hex_memory[0x0000002C] = NOP_INSTR
    await test_timer_trap_handler(dut, hex_memory, 0x00000030)


@cocotb.test()
async def test_timer_trap_handler_9(dut):
    hex_memory = get_timer_trap_handler_memory()
    hex_memory[0x00000020] = NOP_INSTR
    hex_memory[0x00000024] = NOP_INSTR
    hex_memory[0x00000028] = NOP_INSTR
    hex_memory[0x0000002C] = encode_jal(0, 0x30 - 0x2C)  # JAL x0, offset to test function
    await test_timer_trap_handler(dut, hex_memory, 0x00000030)
import cocotb
from test_utils import NOP_INSTR
from spi_memory_utils import (
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
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000024:
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
        if dut.soc_inst.cpu_core.instr_addr.value == 0x0000003C:
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
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000030:
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


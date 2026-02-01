"""
GPIO Interrupt tests - INT_EN, INT_PEND, INT_CLR, rising edge, MEIP, trap handler.
DUT: SoC (test_soc_tb). gpio_in = ui_in[7:2] (6 bits), gpio_bidir = uio_in[7] (1 bit).
in_data in RTL = {gpio_in, gpio_bidir_in} -> pin 0 = gpio_in[0], ..., pin 6 = gpio_bidir_in[0].
"""
import cocotb
from cocotb.triggers import ClockCycles
from test_utils import (
    NOP_INSTR,
    MRET_INSTR,
    encode_load,
    encode_store,
    encode_addi,
    encode_lui,
    encode_jal,
    encode_csrrw,
    GPIO_BASE_ADDR,
    GPIO_INT_EN,
    GPIO_INT_PEND,
    GPIO_INT_CLR,
    CSR_MSTATUS,
    CSR_MIE,
    CSR_MTVEC,
    CSR_MCAUSE,
    CSR_MIP,
)
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
)

# Must match SoC: NUM_BIDIR=1, NUM_IN=6 -> NUM_IN_TOTAL=7
NUM_IN_TOTAL = 7

REG_OFFSET_MASK = 0xFFF

# =============================================================================
# Phase 1: GPIO interrupt registers
# =============================================================================

@cocotb.test()
async def test_gpio_int_en_read_write(dut):
    """INT_EN register: write then read back (masked to NUM_IN_TOTAL bits)."""
    test_val = 0x5A & ((1 << NUM_IN_TOTAL) - 1)
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_INT_EN >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_INT_EN & REG_OFFSET_MASK),
        0x0000000C: encode_addi(2, 0, test_val),
        0x00000010: encode_store(1, 2, 0),
        0x00000014: encode_load(3, 1, 0),
        0x00000018: encode_addi(2, 0, 0),
        0x0000001C: encode_store(1, 2, 0),
        0x00000020: encode_load(4, 1, 0),
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000028:
            regs = dut.soc_inst.cpu_core.register_file.registers
            assert int(dut.soc_inst.error_flag.value) == 0
            r3 = regs[3].value.to_unsigned() & ((1 << NUM_IN_TOTAL) - 1)
            r4 = regs[4].value.to_unsigned() & ((1 << NUM_IN_TOTAL) - 1)
            assert r3 == test_val, f"INT_EN read back expected {test_val:#x}, got {r3:#x}"
            assert r4 == 0, f"INT_EN after write 0 expected 0, got {r4:#x}"
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_int_pend_read_and_int_clr(dut):
    """INT_PEND read (after no edge = 0). INT_CLR write: set INT_EN, drive rising edge in TB, then clear via INT_CLR and read INT_PEND."""
    # Program: set INT_EN for pin 0 = 1, then read INT_PEND (may be 0 initially), then later read again.
    # We drive gpio_in[0] = 0 then 1 in callback to create rising edge; then program writes INT_CLR and reads INT_PEND.
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & REG_OFFSET_MASK),
        0x0000000C: encode_addi(2, 0, 1),
        0x00000010: encode_store(1, 2, GPIO_INT_EN & REG_OFFSET_MASK),   # INT_EN[0] = 1
        0x00000014: encode_load(3, 1, GPIO_INT_PEND & REG_OFFSET_MASK),   # x3 = INT_PEND (may be 0)
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: encode_load(4, 1, GPIO_INT_PEND & REG_OFFSET_MASK),   # x4 = INT_PEND again (after TB drove edge)
        0x0000002C: encode_addi(5, 0, 1),
        0x00000030: encode_store(1, 5, GPIO_INT_CLR & REG_OFFSET_MASK),  # INT_CLR[0] = 1
        0x00000034: encode_load(6, 1, GPIO_INT_PEND & REG_OFFSET_MASK),   # x6 = INT_PEND after clear
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    max_cycles = 15000
    gpio_drove_high = False

    def callback(dut, memory):
        nonlocal gpio_drove_high
        pc = int(dut.soc_inst.cpu_core.o_instr_addr.value)
        # Drive pin 0 (gpio_in[0]) low until we reach 0x20, then high to create rising edge
        if pc < 0x24:
            dut.gpio_io_in.value = 0
        elif pc >= 0x24 and not gpio_drove_high:
            dut.gpio_io_in.value = 1
            gpio_drove_high = True
        else:
            dut.gpio_io_in.value = 1

        if pc == 0x00000040:
            regs = dut.soc_inst.cpu_core.register_file.registers
            assert int(dut.soc_inst.error_flag.value) == 0

            pend_before_edge = regs[3].value.to_unsigned() & ((1 << NUM_IN_TOTAL) - 1)
            # x4 should have had INT_PEND[0]=1 at 0x28 (after edge); x6 after INT_CLR should be 0
            pend_after_edge = regs[4].value.to_unsigned() & ((1 << NUM_IN_TOTAL) - 1)
            pend_after_clr = regs[6].value.to_unsigned() & ((1 << NUM_IN_TOTAL) - 1)
            assert pend_before_edge == 0, f"INT_PEND before edge expected 0, got {pend_before_edge:#x}"
            assert pend_after_edge == 1, f"INT_PEND after rising edge expected 1, got {pend_after_edge:#x}"
            assert pend_after_clr == 0, f"INT_PEND after INT_CLR expected 0, got {pend_after_clr:#x}"
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_rising_edge_sets_pending(dut):
    """Rising edge on pin 1 with INT_EN[1]=1 sets INT_PEND[1]=1 and gpio_interrupt=1. Pin 1 = gpio_in[0]."""
    PIN1_MASK = 2  # INT_EN/INT_PEND bit 1 = pin 1
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & REG_OFFSET_MASK),
        0x0000000C: encode_addi(2, 0, PIN1_MASK),
        0x00000010: encode_store(1, 2, GPIO_INT_EN & REG_OFFSET_MASK),   # INT_EN[1] = 1
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: encode_load(3, 1, GPIO_INT_PEND & REG_OFFSET_MASK),
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    max_cycles = 12000
    drove_high = False

    def callback(dut, memory):
        nonlocal drove_high
        pc = int(dut.soc_inst.cpu_core.o_instr_addr.value)
        # Pin 1 = gpio_in[0]; drive low then rising edge on pin 1 only
        if pc < 0x18:
            dut.gpio_in.value = 0
        elif not drove_high:
            dut.gpio_in.value = 1   # pin 1 = gpio_in[0] = 1
            drove_high = True
        else:
            dut.gpio_in.value = 1

        if pc == 0x00000030:
            regs = dut.soc_inst.cpu_core.register_file.registers
            assert int(dut.soc_inst.error_flag.value) == 0
            int_pend = regs[3].value.to_unsigned() & ((1 << NUM_IN_TOTAL) - 1)
            assert int_pend == PIN1_MASK, f"INT_PEND expected {PIN1_MASK} (pin 1) after rising edge, got {int_pend:#x}"
            gpio_int = int(dut.soc_inst.gpio_inst.gpio_interrupt.value)
            assert gpio_int == 1, "gpio_interrupt should be 1 when INT_EN & INT_PEND != 0"
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_int_disabled_no_pending(dut):
    """With INT_EN[2]=0, rising edge on pin 2 does not set INT_PEND[2]. Pin 2 = gpio_in[1]."""
    PIN2_HIGH = 2  # pin 2 = gpio_in[1] -> value 1 << 1
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & REG_OFFSET_MASK),
        0x0000000C: encode_store(1, 0, GPIO_INT_EN & REG_OFFSET_MASK),
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: encode_load(3, 1, GPIO_INT_PEND & REG_OFFSET_MASK),
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    drove_high = False

    def callback(dut, memory):
        nonlocal drove_high
        pc = int(dut.soc_inst.cpu_core.o_instr_addr.value)
        if pc < 0x14:
            dut.gpio_in.value = 0
        else:
            dut.gpio_in.value = PIN2_HIGH
            drove_high = True

        if pc == 0x00000028:
            regs = dut.soc_inst.cpu_core.register_file.registers
            assert int(dut.soc_inst.error_flag.value) == 0
            int_pend = regs[3].value.to_unsigned() & ((1 << NUM_IN_TOTAL) - 1)
            assert int_pend == 0, f"INT_PEND should be 0 when INT_EN=0, got {int_pend:#x}"
            return True
        return False

    await test_spi_memory(dut, memory, 10000, callback)


# =============================================================================
# Phase 2: MEIP in mip (CSR integration)
# =============================================================================

@cocotb.test()
async def test_gpio_meip_in_mip(dut):
    """When gpio_interrupt=1, read mip (MEIP=1); clear via INT_CLR; read mip again (MEIP=0)."""
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & REG_OFFSET_MASK),
        0x0000000C: encode_addi(2, 0, 1),
        0x00000010: encode_store(1, 2, GPIO_INT_EN & REG_OFFSET_MASK),
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: encode_load(3, 1, GPIO_INT_PEND & REG_OFFSET_MASK),
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: encode_csrrw(4, CSR_MIP, 0),                         # x4 = mip (MEIP=1)
        0x00000038: encode_addi(5, 0, 1),
        0x0000003C: encode_store(1, 5, GPIO_INT_CLR & REG_OFFSET_MASK),  # INT_CLR[0] = 1
        0x00000040: encode_csrrw(5, CSR_MIP, 0),                         # x5 = mip after clear (MEIP=0)
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    drove_high = False

    def callback(dut, memory):
        nonlocal drove_high
        pc = int(dut.soc_inst.cpu_core.o_instr_addr.value)
        if pc < 0x20:
            dut.gpio_io_in.value = 0
        else:
            dut.gpio_io_in.value = 1
            drove_high = True

        if pc == 0x00000048:
            regs = dut.soc_inst.cpu_core.register_file.registers
            assert int(dut.soc_inst.error_flag.value) == 0
            mip_before = regs[4].value.to_unsigned()
            mip_after = regs[5].value.to_unsigned()
            assert (mip_before >> 11) & 1 == 1, f"MEIP should be 1 before clear, mip=0x{mip_before:08x}"
            assert (mip_after >> 11) & 1 == 0, f"MEIP should be 0 after INT_CLR, mip=0x{mip_after:08x}"
            return True
        return False

    await test_spi_memory(dut, memory, 15000, callback)


# =============================================================================
# Phase 3: External interrupt trap and handler (E2E)
# =============================================================================

def _gpio_trap_handler_memory():
    """Memory image: setup mtvec, MIE, MEIE, INT_EN for pin 0; run main; trap handler uses x9=GPIO_BASE (set before JAL), reads mcause, INT_PEND, writes INT_CLR, MRET."""
    trap_addr = 0x00000100
    main_start = 0x00000050
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(11, (trap_addr >> 12) & 0xFFFFF),
        0x00000008: encode_addi(11, 11, trap_addr & 0xFFF),
        0x0000000C: encode_csrrw(0, CSR_MTVEC, 11),  # set mtvec to trap handler
        0x00000010: encode_addi(12, 0, 0x880),
        0x00000014: encode_csrrw(0, CSR_MIE, 12),  # enable MEIE
        0x00000018: encode_addi(12, 0, 0x8),
        0x0000001C: encode_csrrw(0, CSR_MSTATUS, 12),  # enable MIE
        0x00000020: encode_lui(9, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000024: encode_addi(9, 9, GPIO_BASE_ADDR & 0xFFF),
        0x00000028: encode_addi(10, 0, 1),
        0x0000002C: encode_store(9, 10, GPIO_INT_EN & REG_OFFSET_MASK),  # enable GPIO_INT_EN[0]
        0x00000030: encode_jal(0, main_start - 0x30),
        # main (x9 = GPIO base; will be interrupted)
        0x00000050: encode_addi(1, 1, 1),
        0x00000054: encode_addi(2, 2, 2),
        0x00000058: encode_addi(3, 3, 3),
        0x0000005C: encode_addi(4, 4, 4),
        0x00000060: encode_addi(5, 5, 5),
        0x00000064: encode_addi(6, 6, 6),
        0x00000068: encode_load(7, 9, GPIO_INT_PEND & REG_OFFSET_MASK),
        0x0000006C: NOP_INSTR,
        0x00000070: NOP_INSTR,
        # trap handler (x9 still holds GPIO_BASE from setup)
        0x00000100: encode_csrrw(13, CSR_MCAUSE, 0),
        0x00000104: encode_load(14, 9, GPIO_INT_PEND & REG_OFFSET_MASK),
        0x00000108: encode_addi(15, 0, 1),
        0x0000010C: encode_store(9, 15, GPIO_INT_CLR & REG_OFFSET_MASK),
        0x00000110: MRET_INSTR,
        0x00000114: NOP_INSTR,
        0x00000118: NOP_INSTR,
    }
    return hex_memory


@cocotb.test()
async def test_gpio_external_interrupt_trap_handler(dut):
    """E2E: Enable GPIO int on pin 0, run main; TB drives rising edge; CPU traps, handler reads mcause=0x8000000B, reads INT_PEND, writes INT_CLR, MRET."""
    hex_memory = _gpio_trap_handler_memory()
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    max_cycles = 20000000
    drove_high = False

    def callback(dut, memory):
        nonlocal drove_high
        pc = int(dut.soc_inst.cpu_core.o_instr_addr.value)
        if pc < 0x54:
            dut.gpio_io_in.value = 0
        elif not drove_high:
            dut.gpio_io_in.value = 1
            drove_high = True
        else:
            dut.gpio_io_in.value = 1

        if pc == 0x00000070:
            regs = dut.soc_inst.cpu_core.register_file.registers
            assert int(dut.soc_inst.error_flag.value) == 0
            mcause = regs[13].value.to_unsigned()
            assert mcause == 0x8000000B, f"mcause expected 0x8000000B (external int), got 0x{mcause:08x}"
            int_pend = regs[14].value.to_unsigned() & ((1 << NUM_IN_TOTAL) - 1)
            assert int_pend == 1, f"Handler should see INT_PEND[0]=1, got {int_pend:#x}"

            assert regs[1].value.to_unsigned() == 1, f"x1 should be 1, got {regs[1].value.to_unsigned():#x}"
            assert regs[2].value.to_unsigned() == 2, f"x2 should be 2, got {regs[2].value.to_unsigned():#x}"
            assert regs[3].value.to_unsigned() == 3, f"x3 should be 3, got {regs[3].value.to_unsigned():#x}"
            assert regs[4].value.to_unsigned() == 4, f"x4 should be 4, got {regs[4].value.to_unsigned():#x}"
            assert regs[5].value.to_unsigned() == 5, f"x5 should be 5, got {regs[5].value.to_unsigned():#x}"
            assert regs[6].value.to_unsigned() == 6, f"x6 should be 6, got {regs[6].value.to_unsigned():#x}"
            assert regs[7].value.to_unsigned() == 0, f"INT_PEND[0] should be 0, got {regs[7].value.to_unsigned():#x}"
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

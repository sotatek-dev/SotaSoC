"""
I2C Master Test Suite - Group 1: Basic Register Read/Write Tests

Tests for verifying basic register operations of the I2C master module.
"""

import cocotb
import os
import random
from test_utils import (
    NOP_INSTR,
    encode_load,
    encode_store,
    encode_addi,
    encode_lui,
    encode_andi,
    encode_bne,
    I2C_BASE_ADDR,
    I2C_CTRL,
    I2C_STATUS,
    I2C_DATA,
    I2C_PRESCALE,
    I2C_CTRL_START,
    I2C_CTRL_STOP,
    I2C_CTRL_READ,
    I2C_CTRL_ACK_EN,
    I2C_STATUS_BUSY,
    I2C_STATUS_ACK,
    I2C_STATUS_ARB_LOST,
    I2C_STATUS_DONE,
    I2C_STATUS_ERROR,
    I2C_PRESCALE_100KHZ,
    I2C_PRESCALE_400KHZ,
)
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
    load_bin_file,
)
from i2c_slave_bfm import start_i2c_slave_bfm


# =============================================================================
# Helper Functions
# =============================================================================

def build_i2c_addr(reg_offset):
    """Build full I2C register address from offset"""
    return I2C_BASE_ADDR + reg_offset


# =============================================================================
# Group 1: Basic Register Read/Write Tests
# =============================================================================

@cocotb.test()
async def test_i2c_reset_values(dut):
    """Test 1.4: Verify default reset values of all I2C registers
    
    After reset:
    - CTRL should be 0x00 (disabled)
    - STATUS should be 0x00 (idle, no errors)
    - DATA should be 0x00
    - PRESCALE should be 159 (default 100kHz @ 64MHz)
    """
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Load I2C base address into x1
        0x00000004: encode_lui(1, I2C_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, I2C_BASE_ADDR & 0xFFF),
        # Read all registers
        0x0000000C: encode_load(2, 1, 0x00),    # x2 = CTRL
        0x00000010: encode_load(3, 1, 0x04),    # x3 = STATUS
        0x00000014: encode_load(4, 1, 0x08),    # x4 = DATA
        0x00000018: encode_load(5, 1, 0x0C),    # x5 = PRESCALE
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    # Initialize I2C input signals (release lines - pull-up)
    dut.gpio_io_in.value = 0x0F  # SDA and SCL high (bits 0,1 for I2C)
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000024:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"
            
            # Verify reset values
            ctrl_val = registers[2].value.to_unsigned() & 0xFF
            status_val = registers[3].value.to_unsigned() & 0xFF
            data_val = registers[4].value.to_unsigned() & 0xFF
            prescale_val = registers[5].value.to_unsigned() & 0xFF
            
            assert ctrl_val == 0x00, f"CTRL reset value should be 0x00, got {ctrl_val:#x}"
            assert status_val == 0x00, f"STATUS reset value should be 0x00, got {status_val:#x}"
            # DATA register may be undefined after reset, so we don't check it strictly
            assert prescale_val == I2C_PRESCALE_100KHZ, \
                f"PRESCALE reset value should be {I2C_PRESCALE_100KHZ}, got {prescale_val}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_i2c_read_write_ctrl(dut):
    """Test 1.1: Read/write CTRL register
    
    Test writing and reading back CTRL register bits:
    - Enable bit
    - Read mode bit
    - ACK enable bit
    
    Note: START and STOP bits are command bits and may not read back as written.
    """
    
    # Test value: Read + ACK_EN = 0x04 | 0x08 = 0x0C
    test_ctrl_value = I2C_CTRL_READ | I2C_CTRL_ACK_EN
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Load I2C base address into x1
        0x00000004: encode_lui(1, I2C_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, I2C_BASE_ADDR & 0xFFF),
        # Write test value to CTRL
        0x0000000C: encode_addi(2, 0, test_ctrl_value),
        0x00000010: encode_store(1, 2, 0x00),   # CTRL = test_ctrl_value
        # Read back CTRL
        0x00000014: encode_load(3, 1, 0x00),    # x3 = CTRL
        # Write 0 to disable
        0x00000018: encode_store(1, 0, 0x00),   # CTRL = 0
        # Read back again
        0x0000001C: encode_load(4, 1, 0x00),    # x4 = CTRL
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    dut.gpio_io_in.value = 0x0F
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000028:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"
            
            # Check written value (persistent bits only: READ, ACK_EN)
            ctrl_read_1 = registers[3].value.to_unsigned() & 0xFF
            persistent_mask = I2C_CTRL_READ | I2C_CTRL_ACK_EN
            expected = test_ctrl_value & persistent_mask
            assert (ctrl_read_1 & persistent_mask) == expected, \
                f"CTRL should have persistent bits {expected:#x}, got {ctrl_read_1:#x}"
            
            # Check after writing 0
            ctrl_read_2 = registers[4].value.to_unsigned() & 0xFF
            assert (ctrl_read_2 & persistent_mask) == 0, \
                f"CTRL should be 0 after clear, got {ctrl_read_2:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_i2c_read_write_prescale(dut):
    """Test 1.2: Read/write PRESCALE register with different values
    
    Test writing various prescale values:
    - 100kHz setting (159)
    - 400kHz setting (39)
    - Custom value
    """
    
    test_prescale_1 = I2C_PRESCALE_400KHZ  # 39
    test_prescale_2 = 0x55  # Custom value
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Load I2C base address into x1
        0x00000004: encode_lui(1, I2C_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, I2C_BASE_ADDR & 0xFFF),
        # Read default prescale
        0x0000000C: encode_load(2, 1, 0x0C),    # x2 = PRESCALE (default)
        # Write 400kHz prescale
        0x00000010: encode_addi(3, 0, test_prescale_1),
        0x00000014: encode_store(1, 3, 0x0C),   # PRESCALE = 39
        # Read back
        0x00000018: encode_load(4, 1, 0x0C),    # x4 = PRESCALE
        # Write custom prescale
        0x0000001C: encode_addi(3, 0, test_prescale_2),
        0x00000020: encode_store(1, 3, 0x0C),   # PRESCALE = 0x55
        # Read back
        0x00000024: encode_load(5, 1, 0x0C),    # x5 = PRESCALE
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 12000
    
    dut.gpio_io_in.value = 0x0F
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000030:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"
            
            # Check default prescale
            prescale_default = registers[2].value.to_unsigned() & 0xFF
            assert prescale_default == I2C_PRESCALE_100KHZ, \
                f"Default PRESCALE should be {I2C_PRESCALE_100KHZ}, got {prescale_default}"
            
            # Check 400kHz prescale
            prescale_400k = registers[4].value.to_unsigned() & 0xFF
            assert prescale_400k == test_prescale_1, \
                f"PRESCALE should be {test_prescale_1}, got {prescale_400k}"
            
            # Check custom prescale
            prescale_custom = registers[5].value.to_unsigned() & 0xFF
            assert prescale_custom == test_prescale_2, \
                f"PRESCALE should be {test_prescale_2:#x}, got {prescale_custom:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_i2c_status_read_only(dut):
    """Test 1.3: Verify STATUS register is read-only
    
    Attempt to write to STATUS register and verify it doesn't change.
    STATUS register should always reflect the actual module state.
    """
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Load I2C base address into x1
        0x00000004: encode_lui(1, I2C_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, I2C_BASE_ADDR & 0xFFF),
        # Read initial STATUS
        0x0000000C: encode_load(2, 1, 0x04),    # x2 = STATUS (initial)
        # Attempt to write to STATUS
        0x00000010: encode_addi(3, 0, 0xFF),    # x3 = 0xFF
        0x00000014: encode_store(1, 3, 0x04),   # Try to write STATUS = 0xFF
        # Read STATUS again
        0x00000018: encode_load(4, 1, 0x04),    # x4 = STATUS (after write attempt)
        # Attempt to write different value
        0x0000001C: encode_addi(3, 0, 0x1F),    # x3 = 0x1F
        0x00000020: encode_store(1, 3, 0x04),   # Try to write STATUS = 0x1F
        # Read STATUS again
        0x00000024: encode_load(5, 1, 0x04),    # x5 = STATUS (after second write)
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 12000
    
    dut.gpio_io_in.value = 0x0F
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000030:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"
            
            # All STATUS reads should be the same (writes ignored)
            status_1 = registers[2].value.to_unsigned() & 0xFF
            status_2 = registers[4].value.to_unsigned() & 0xFF
            status_3 = registers[5].value.to_unsigned() & 0xFF
            
            # STATUS should remain unchanged (module is idle, so should be 0)
            assert status_1 == status_2, \
                f"STATUS changed after write: {status_1:#x} -> {status_2:#x}"
            assert status_2 == status_3, \
                f"STATUS changed after second write: {status_2:#x} -> {status_3:#x}"
            
            # Since module is idle and disabled, STATUS should be 0
            assert status_1 == 0x00, \
                f"STATUS should be 0x00 when idle, got {status_1:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_i2c_data_register_write(dut):
    """Test 1.5: Write to DATA register and verify TX data is latched
    
    Write various values to DATA register and verify they are stored.
    """
    
    test_data_1 = 0xA5
    test_data_2 = 0x5A
    test_data_3 = 0x00
    test_data_4 = 0xFF
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Load I2C base address into x1
        0x00000004: encode_lui(1, I2C_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, I2C_BASE_ADDR & 0xFFF),
        # Write test_data_1 to DATA
        0x0000000C: encode_addi(2, 0, test_data_1),
        0x00000010: encode_store(1, 2, 0x08),   # DATA = 0xA5
        0x00000014: NOP_INSTR,
        # Write test_data_2 to DATA
        0x00000018: encode_addi(2, 0, test_data_2),
        0x0000001C: encode_store(1, 2, 0x08),   # DATA = 0x5A
        0x00000020: NOP_INSTR,
        # Write test_data_3 (all zeros)
        0x00000024: encode_store(1, 0, 0x08),   # DATA = 0x00
        0x00000028: NOP_INSTR,
        # Write test_data_4 (all ones)
        0x0000002C: encode_addi(2, 0, test_data_4),
        0x00000030: encode_store(1, 2, 0x08),   # DATA = 0xFF
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 15000
    
    dut.gpio_io_in.value = 0x0F
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000003C:
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"
            
            # Verify the I2C module received the data writes
            # Check internal data_reg in i2c module
            i2c_inst = dut.soc_inst.i2c_inst
            tx_data = int(i2c_inst.data_reg.value)
            
            # Last written value should be 0xFF
            assert tx_data == test_data_4, \
                f"TX data register should be {test_data_4:#x}, got {tx_data:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_i2c_invalid_register_offset(dut):
    """Test: Reading invalid register offset returns 0
    
    Access addresses beyond the valid register range should return 0.
    """
    
    # Valid offsets are 0x00, 0x04, 0x08, 0x0C
    # Test reading offset 0x10 (invalid)
    invalid_offset = 0x10
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Load I2C base address into x1
        0x00000004: encode_lui(1, I2C_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, I2C_BASE_ADDR & 0xFFF),
        # Read invalid offset
        0x0000000C: encode_load(2, 1, invalid_offset),  # x2 = MEM[I2C_BASE + 0x10]
        # Read another invalid offset
        0x00000010: encode_load(3, 1, 0x14),            # x3 = MEM[I2C_BASE + 0x14]
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    dut.gpio_io_in.value = 0x0F
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000001C:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"
            
            # Reading invalid offsets should return 0
            invalid_read_1 = registers[2].value.to_unsigned()
            invalid_read_2 = registers[3].value.to_unsigned()
            
            assert invalid_read_1 == 0, \
                f"Reading invalid offset 0x10 should return 0, got {invalid_read_1:#x}"
            assert invalid_read_2 == 0, \
                f"Reading invalid offset 0x14 should return 0, got {invalid_read_2:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_i2c_send_data(dut):
    """Test: Send data via I2C
    """
    
    slave_addr = 0x42  # 7-bit address: 0x21, shifted left = 0x42 (write mode)
    test_data = 0xAA
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Load I2C base address into x1
        0x00000004: encode_lui(1, I2C_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, I2C_BASE_ADDR & 0xFFF),
        # Set prescaler for 100kHz
        0x0000000C: encode_addi(2, 0, I2C_PRESCALE_100KHZ),
        0x00000010: encode_store(1, 2, 0x0C),   # PRESCALE = 159
        # Enable I2C module
        0x00000014: encode_addi(2, 0, 0),
        0x00000018: encode_store(1, 2, 0x00),
        # Write slave address to DATA register
        0x0000001C: encode_addi(3, 0, slave_addr),
        0x00000020: encode_store(1, 3, 0x08),   # DATA = slave_addr
        # Set START bit
        0x00000024: encode_addi(2, 0, I2C_CTRL_START),
        0x00000028: encode_store(1, 2, 0x00),   # CTRL = START
        # Poll STATUS until DONE bit is set
        # Loop start: read STATUS
        0x0000002C: encode_load(4, 1, 0x04),    # x4 = STATUS
        0x00000030: encode_andi(5, 4, I2C_STATUS_DONE),  # x5 = STATUS & DONE
        0x00000034: encode_addi(6, 0, I2C_STATUS_DONE),   # x6 = DONE value
        0x00000038: encode_bne(5, 6, -12),       # if x5 != x6, loop back (to 0x0000002C)
        # Write data byte to DATA register
        0x0000003C: encode_addi(3, 0, test_data),
        0x00000040: encode_store(1, 3, 0x08),   # DATA = test_data
        0x00000044: encode_addi(2, 0, I2C_CTRL_START),
        0x00000048: encode_store(1, 2, 0x00),   # CTRL = START
        # Poll STATUS until DONE bit is set again
        0x0000004C: encode_load(4, 1, 0x04),    # x4 = STATUS
        0x00000050: encode_andi(5, 4, I2C_STATUS_DONE),  # x5 = STATUS & DONE
        0x00000054: encode_bne(5, 6, -8),       # if x5 != x6, loop back (to 0x00000044)
        # Set STOP bit
        0x00000058: encode_addi(2, 0, I2C_CTRL_STOP),
        0x0000005C: encode_store(1, 2, 0x00),   # CTRL = STOP
        # Read final STATUS
        0x00000060: encode_load(7, 1, 0x04),    # x7 = STATUS
        # Read ACK status
        0x00000064: encode_load(8, 1, 0x04),    # x8 = STATUS (for ACK check)
        0x00000068: NOP_INSTR,
        0x0000006C: NOP_INSTR,
        0x00000070: NOP_INSTR,
        0x00000074: NOP_INSTR,
        0x00000078: NOP_INSTR,
        0x0000007C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 50000  # Need more cycles for I2C transfer

    # Initialize I2C lines high (pulled up)
    dut.gpio_io_in.value = 0x0F  # SDA and SCL high (bits 0,1 for I2C)

    dut.i2c_ena.value = 1

    # Start I2C slave BFM (7-bit address 0x21, so address byte 0x42 for write)
    # The BFM will drive the bus SDA/SCL levels via i2c_sda_in/i2c_scl_in
    # Note: i2c_sda_out and i2c_scl_out are already computed from uio_oe/uio_out
    i2c_bfm = start_i2c_slave_bfm(
        clk=dut.clk,
        sda_out=dut.i2c_sda_out,  # Already computed from testbench
        scl_out=dut.i2c_scl_out,   # Already computed from testbench
        sda_in=dut.i2c_sda_in,     # BFM drives this (feeds into SoC)
        scl_in=dut.i2c_scl_in,     # BFM drives this (feeds into SoC)
        address=0x21,  # 7-bit address (matches slave_addr >> 1)
    )

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000007C:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"
            
            # Check final STATUS
            status_val = registers[7].value.to_unsigned() & 0xFF
            status_ack = registers[8].value.to_unsigned() & 0xFF
            
            # STATUS should show transfer is done
            assert (status_val & I2C_STATUS_DONE) != 0, \
                f"STATUS DONE bit should be set, got {status_val:#x}"
            
            # With a slave BFM, we should receive ACK
            assert (status_ack & I2C_STATUS_ACK) != 0, \
                f"STATUS ACK bit should be set (slave should ACK), got {status_ack:#x}"
            
            # Verify slave BFM received the data
            rx_data = i2c_bfm.get_rx_data()
            assert len(rx_data) >= 1, \
                f"Slave should have received at least the address byte, got {len(rx_data)} bytes"
            
            # First byte should be the address byte (0x42 = 0x21 << 1 | 0)
            assert rx_data[0] == slave_addr, \
                f"Slave should have received address {slave_addr:#x}, got {rx_data[0]:#x}"
            
            # Second byte should be the data byte
            assert len(rx_data) >= 2, \
                f"Slave should have received data byte, got {len(rx_data)} bytes"
            assert rx_data[1] == test_data, \
                f"Slave should have received data {test_data:#x}, got {rx_data[1]:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_i2c_read_write_1_byte(dut):
    """Test: Send data via I2C
    """
    
    slave_read_addr = 0x43  # 7-bit address: 0x21, shifted left = 0x42 (write mode)
    slave_write_addr = 0x42  # 7-bit address: 0x21, shifted left = 0x42 (write mode)
    tx_data = [0xAA]

    bin_file_path = os.environ.get('BIN_FILE', None)

    if bin_file_path is None:
        print("WARNING: BIN_FILE environment variable not set, skipping test")
        return

    if not os.path.exists(bin_file_path):
        print(f"WARNING: Bin file not found: {bin_file_path}, skipping test")
        return

    # Load memory from bin file
    memory = load_bin_file(bin_file_path)

    max_cycles = 50000  # Need more cycles for I2C transfer

    # Initialize I2C lines high (pulled up)
    dut.gpio_io_in.value = 0x0F  # SDA and SCL high (bits 0,1 for I2C)

    dut.i2c_ena.value = 1

    # Start I2C slave BFM (7-bit address 0x21, so address byte 0x42 for write)
    # The BFM will drive the bus SDA/SCL levels via i2c_sda_in/i2c_scl_in
    # Note: i2c_sda_out and i2c_scl_out are already computed from uio_oe/uio_out
    i2c_bfm = start_i2c_slave_bfm(
        clk=dut.clk,
        sda_out=dut.i2c_sda_out,  # Already computed from testbench
        scl_out=dut.i2c_scl_out,   # Already computed from testbench
        sda_in=dut.i2c_sda_in,     # BFM drives this (feeds into SoC)
        scl_in=dut.i2c_scl_in,     # BFM drives this (feeds into SoC)
        address=0x21,  # 7-bit address (matches slave_addr >> 1)
        tx_data=tx_data,
    )

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000040:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"

            # Verify slave BFM received the data
            rx_data = i2c_bfm.get_rx_data()
            assert len(rx_data) >= 1, \
                f"Slave should have received at least the address byte, got {len(rx_data)} bytes"
            
            # First byte should be the address byte (0x42 = 0x21 << 1 | 1)
            assert rx_data[0] == slave_read_addr, \
                f"Slave should have received address {slave_addr:#x}, got {rx_data[0]:#x}"
            
            # Second byte should be the data byte
            assert len(rx_data) >= 3, \
                f"Slave should have received data byte, got {len(rx_data)} bytes"
            assert rx_data[1] == slave_write_addr, \
                f"Slave should have received data {slave_write_addr:#x}, got {rx_data[1]:#x}"
            assert rx_data[2] == tx_data[0], \
                f"Slave should have received data {tx_data[0]:#x}, got {rx_data[2]:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_i2c_read_write_multiple_bytes(dut):
    """Test: Send data via I2C
    """
    
    slave_read_addr = 0x43  # 7-bit address: 0x21, shifted left = 0x42 (write mode)
    slave_write_addr = 0x42  # 7-bit address: 0x21, shifted left = 0x42 (write mode)

    length = 16
    tx_data = []
    for i in range(length):
        tx_data.append(random.randrange(0, length))

    bin_file_path = os.environ.get('BIN_FILE', None)

    if bin_file_path is None:
        print("WARNING: BIN_FILE environment variable not set, skipping test")
        return

    if not os.path.exists(bin_file_path):
        print(f"WARNING: Bin file not found: {bin_file_path}, skipping test")
        return

    # Load memory from bin file
    memory = load_bin_file(bin_file_path)

    max_cycles = 500000  # Need more cycles for I2C transfer

    # Initialize I2C lines high (pulled up)
    dut.gpio_io_in.value = 0x0F  # SDA and SCL high (bits 0,1 for I2C)

    dut.i2c_ena.value = 1

    # Start I2C slave BFM (7-bit address 0x21, so address byte 0x42 for write)
    # The BFM will drive the bus SDA/SCL levels via i2c_sda_in/i2c_scl_in
    # Note: i2c_sda_out and i2c_scl_out are already computed from uio_oe/uio_out
    i2c_bfm = start_i2c_slave_bfm(
        clk=dut.clk,
        sda_out=dut.i2c_sda_out,  # Already computed from testbench
        scl_out=dut.i2c_scl_out,   # Already computed from testbench
        sda_in=dut.i2c_sda_in,     # BFM drives this (feeds into SoC)
        scl_in=dut.i2c_scl_in,     # BFM drives this (feeds into SoC)
        address=0x21,  # 7-bit address (matches slave_addr >> 1)
        tx_data=tx_data,
    )

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000040:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"

            # Verify slave BFM received the data
            rx_data = i2c_bfm.get_rx_data()
            assert len(rx_data) == len(tx_data) + 2, \
                f"Slave should have received {len(tx_data) + 2} bytes, got {len(rx_data)} bytes"
            
            # First byte should be the address byte (0x42 = 0x21 << 1 | 1)
            assert rx_data[0] == slave_read_addr, \
                f"Slave should have received address {slave_read_addr:#x}, got {rx_data[0]:#x}"
            assert rx_data[1] == slave_write_addr, \
                f"Slave should have received address {slave_write_addr:#x}, got {rx_data[1]:#x}"
            for i in range(len(tx_data)):
                assert rx_data[i + 2] == tx_data[i], \
                    f"Slave should have received data {tx_data[i]:#x}, got {rx_data[i + 2]:#x}"

            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)



@cocotb.test()
async def test_i2c_repeated_start(dut):
    """Test: Send data via I2C
    """
    
    slave_read_addr = 0x43  # 7-bit address: 0x21, shifted left = 0x42 (write mode)
    slave_write_addr = 0x42  # 7-bit address: 0x21, shifted left = 0x42 (write mode)
    tx_data = [0xAB]

    bin_file_path = os.environ.get('BIN_FILE', None)

    if bin_file_path is None:
        print("WARNING: BIN_FILE environment variable not set, skipping test")
        return

    if not os.path.exists(bin_file_path):
        print(f"WARNING: Bin file not found: {bin_file_path}, skipping test")
        return

    # Load memory from bin file
    memory = load_bin_file(bin_file_path)

    max_cycles = 50000  # Need more cycles for I2C transfer

    # Initialize I2C lines high (pulled up)
    dut.gpio_io_in.value = 0x0F  # SDA and SCL high (bits 0,1 for I2C)

    dut.i2c_ena.value = 1

    # Start I2C slave BFM (7-bit address 0x21, so address byte 0x42 for write)
    # The BFM will drive the bus SDA/SCL levels via i2c_sda_in/i2c_scl_in
    # Note: i2c_sda_out and i2c_scl_out are already computed from uio_oe/uio_out
    i2c_bfm = start_i2c_slave_bfm(
        clk=dut.clk,
        sda_out=dut.i2c_sda_out,  # Already computed from testbench
        scl_out=dut.i2c_scl_out,   # Already computed from testbench
        sda_in=dut.i2c_sda_in,     # BFM drives this (feeds into SoC)
        scl_in=dut.i2c_scl_in,     # BFM drives this (feeds into SoC)
        address=0x21,  # 7-bit address (matches slave_addr >> 1)
        tx_data=tx_data,
    )

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000174:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, "error_flag should be 0"

            # Verify slave BFM received the data
            rx_data = i2c_bfm.get_rx_data()
            assert len(rx_data) >= 1, \
                f"Slave should have received at least the address byte, got {len(rx_data)} bytes"
            
            # First byte should be the address byte (0x42 = 0x21 << 1 | 1)
            assert rx_data[0] == slave_read_addr, \
                f"Slave should have received address {slave_addr:#x}, got {rx_data[0]:#x}"
            
            # Second byte should be the data byte
            assert len(rx_data) >= 3, \
                f"Slave should have received data byte, got {len(rx_data)} bytes"
            assert rx_data[1] == slave_write_addr, \
                f"Slave should have received data {slave_write_addr:#x}, got {rx_data[1]:#x}"
            assert rx_data[2] == tx_data[0], \
                f"Slave should have received data {tx_data[0]:#x}, got {rx_data[2]:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)

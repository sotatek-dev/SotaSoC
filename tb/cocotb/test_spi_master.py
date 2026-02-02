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
    SPI_BASE_ADDR,
    SPI_EN,
    SPI_CTRL,
    SPI_STATUS,
    SPI_TX_DATA,
    SPI_RX_DATA,
    SPI_CONFIG,
    SPI_EN_BIT,
    SPI_CTRL_START,
    SPI_STATUS_BUSY,
    SPI_STATUS_DONE,
    SPI_CONFIG_DIV_MASK,
    SPI_DIV_1MHZ,
    SPI_DIV_2MHZ,
    SPI_DIV_4MHZ,
    SPI_DIV_8MHZ,
    SPI_MODE0,
    GPIO_BASE_ADDR,
    GPIO_DIR,
    GPIO_OUT,
)
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
    load_bin_file,
    write_word_to_memory,
)
from spi_slave_bfm import SPISlaveBFM, create_spi_slave_bfm, start_spi_slave_bfm


# =============================================================================
# Group 1: Basic Register Read/Write Tests
# =============================================================================

@cocotb.test()
async def test_spi_read_write_config(dut):
    """Test reading and writing SPI CONFIG register (divider only, Mode 0 only)"""
    
    # Test different configurations
    test_configs = [
        (SPI_DIV_1MHZ | SPI_MODE0, "divider=31"),
        (SPI_DIV_2MHZ | SPI_MODE0, "divider=15"),
        (SPI_DIV_4MHZ | SPI_MODE0, "divider=7"),
        (SPI_DIV_8MHZ | SPI_MODE0, "divider=3"),
    ]
    
    for test_config, desc in test_configs:
        hex_memory = {
            0x00000000: NOP_INSTR,
            0x00000004: encode_lui(1, (SPI_CONFIG >> 12) & 0xFFFFF),    # LUI x1, SPI base upper
            0x00000008: encode_addi(1, 1, SPI_CONFIG & 0xFFF),          # ADDI x1, x1, SPI_CONFIG offset
            0x0000000C: encode_lui(2, (test_config >> 12) & 0xFFFFF),   # LUI x2, config upper
            0x00000010: encode_addi(2, 2, test_config & 0xFFF),         # ADDI x2, x2, config lower
            0x00000014: encode_store(1, 2, 0),                          # SW x2, 0(x1) - write CONFIG
            0x00000018: encode_load(3, 1, 0),                           # LW x3, 0(x1) - read CONFIG
            0x0000001C: NOP_INSTR,
            0x00000020: NOP_INSTR,
            0x00000024: NOP_INSTR,
        }
        memory = convert_hex_memory_to_byte_memory(hex_memory)
        
        max_cycles = 10000
        
        def callback(dut, memory):
            if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000024:
                registers = dut.soc_inst.cpu_core.register_file.registers
                
                assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
                
                # x3 should contain CONFIG value
                config_read = registers[3].value.to_unsigned()
                # Mask to relevant bits: divider [7:0] only
                config_read_masked = config_read & 0xFF
                expected_masked = test_config & 0xFF
                assert config_read_masked == expected_masked, \
                    f"CONFIG should be 0x{expected_masked:02x} ({desc}), got 0x{config_read_masked:02x}"
                
                return True
            return False
        
        await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_spi_status_read_only(dut):
    """Test that STATUS register is read-only (writes ignored)"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (SPI_STATUS >> 12) & 0xFFFFF),   # LUI x1, SPI base upper
        0x00000008: encode_addi(1, 1, SPI_STATUS & 0xFFF),         # ADDI x1, x1, SPI_STATUS offset
        0x0000000C: encode_load(2, 1, 0),                          # LW x2, 0(x1) - read STATUS (initial)
        0x00000010: encode_addi(3, 0, 0xFF),                       # ADDI x3, x0, 0xFF
        0x00000014: encode_store(1, 3, 0),                         # SW x3, 0(x1) - try to write STATUS (should be ignored)
        0x00000018: encode_load(4, 1, 0),                          # LW x4, 0(x1) - read STATUS again
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000024:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x2 and x4 should be the same (STATUS is read-only)
            status_read_1 = registers[2].value.to_unsigned()
            status_read_2 = registers[4].value.to_unsigned()
            assert status_read_1 == status_read_2, \
                f"STATUS should be read-only: first read=0x{status_read_1:08x}, second read=0x{status_read_2:08x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_spi_ctrl_write_only(dut):
    """Test that CTRL register is write-only (reads return 0)"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (SPI_CTRL >> 12) & 0xFFFFF),     # LUI x1, SPI base upper
        0x00000008: encode_addi(1, 1, SPI_CTRL & 0xFFF),           # ADDI x1, x1, SPI_CTRL offset
        0x0000000C: encode_load(2, 1, 0),                          # LW x2, 0(x1) - read CTRL (should return 0)
        0x00000010: encode_addi(3, 0, SPI_CTRL_START),             # ADDI x3, x0, 1 (START bit)
        0x00000014: encode_store(1, 3, 0),                         # SW x3, 0(x1) - write CTRL
        0x00000018: encode_load(4, 1, 0),                          # LW x4, 0(x1) - read CTRL again (should return 0)
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000024:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x2 and x4 should be 0 (CTRL is write-only)
            ctrl_read_1 = registers[2].value.to_unsigned()
            ctrl_read_2 = registers[4].value.to_unsigned()
            assert ctrl_read_1 == 0, f"CTRL read should return 0, got 0x{ctrl_read_1:08x}"
            assert ctrl_read_2 == 0, f"CTRL read should return 0, got 0x{ctrl_read_2:08x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_spi_tx_data_write_only(dut):
    """Test that TX_DATA register is write-only (reads return 0)"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (SPI_TX_DATA >> 12) & 0xFFFFF),  # LUI x1, SPI base upper
        0x00000008: encode_addi(1, 1, SPI_TX_DATA & 0xFFF),        # ADDI x1, x1, SPI_TX_DATA offset
        0x0000000C: encode_load(2, 1, 0),                          # LW x2, 0(x1) - read TX_DATA (should return 0)
        0x00000010: encode_addi(3, 0, 0xAA),                       # ADDI x3, x0, 0xAA
        0x00000014: encode_store(1, 3, 0),                         # SW x3, 0(x1) - write TX_DATA
        0x00000018: encode_load(4, 1, 0),                          # LW x4, 0(x1) - read TX_DATA again (should return 0)
        0x0000001C: encode_addi(5, 0, 0x55),                       # ADDI x5, x0, 0x55
        0x00000020: encode_store(1, 5, 0),                         # SW x5, 0(x1) - write TX_DATA again
        0x00000024: encode_load(6, 1, 0),                          # LW x6, 0(x1) - read TX_DATA (should return 0)
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000030:
            registers = dut.soc_inst.cpu_core.register_file.registers

            tx_data = dut.soc_inst.spi_inst.tx_shift_reg.value.to_unsigned()
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x2, x4, x6: All reads should return 0 (TX_DATA is write-only)
            tx_data_read_1 = registers[2].value.to_unsigned()
            tx_data_read_2 = registers[4].value.to_unsigned()
            tx_data_read_3 = registers[6].value.to_unsigned()
            
            assert tx_data_read_1 == 0, \
                f"TX_DATA read should return 0, got 0x{tx_data_read_1:08x}"
            assert tx_data_read_2 == 0, \
                f"TX_DATA read should return 0 after write, got 0x{tx_data_read_2:08x}"
            assert tx_data_read_3 == 0, \
                f"TX_DATA read should return 0 after second write, got 0x{tx_data_read_3:08x}"

            assert tx_data == 0x55, f"TX_DATA should be 0x55, got 0x{tx_data:08x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_spi_rx_data_read_only(dut):
    """Test that RX_DATA register is read-only"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (SPI_RX_DATA >> 12) & 0xFFFFF),  # LUI x1, SPI base upper
        0x00000008: encode_addi(1, 1, SPI_RX_DATA & 0xFFF),        # ADDI x1, x1, SPI_RX_DATA offset
        0x0000000C: encode_load(2, 1, 0),                          # LW x2, 0(x1) - read RX_DATA (initial)
        0x00000010: encode_addi(3, 0, 0x55),                       # ADDI x3, x0, 0x55
        0x00000014: encode_store(1, 3, 0),                         # SW x3, 0(x1) - try to write RX_DATA (should be ignored)
        0x00000018: encode_load(4, 1, 0),                          # LW x4, 0(x1) - read RX_DATA again
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000024:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x2 and x4 should be the same (RX_DATA is read-only, write ignored)
            rx_data_read_1 = registers[2].value.to_unsigned()
            rx_data_read_2 = registers[4].value.to_unsigned()
            assert rx_data_read_1 == rx_data_read_2, \
                f"RX_DATA should be read-only: first read=0x{rx_data_read_1:08x}, second read=0x{rx_data_read_2:08x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_spi_reset_values(dut):
    """Test default reset values of all registers"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (SPI_BASE_ADDR >> 12) & 0xFFFFF), # LUI x1, SPI base upper
        0x00000008: encode_addi(1, 1, SPI_BASE_ADDR & 0xFFF),       # ADDI x1, x1, SPI base lower
        # Read all registers (new offsets: ENABLE 0x00, CTRL 0x04, STATUS 0x08, TX 0x0C, RX 0x10, CONFIG 0x14)
        0x0000000C: encode_load(2, 1, SPI_EN & 0xFFF),         # LW x2, 0x00(x1) - read ENABLE
        0x00000010: encode_load(3, 1, SPI_CTRL & 0xFFF),           # LW x3, 0x04(x1) - read CTRL
        0x00000014: encode_load(4, 1, SPI_STATUS & 0xFFF),         # LW x4, 0x08(x1) - read STATUS
        0x00000018: encode_load(5, 1, SPI_TX_DATA & 0xFFF),        # LW x5, 0x0C(x1) - read TX_DATA
        0x0000001C: encode_load(6, 1, SPI_RX_DATA & 0xFFF),       # LW x6, 0x10(x1) - read RX_DATA
        0x00000020: encode_load(7, 1, SPI_CONFIG & 0xFFF),        # LW x7, 0x14(x1) - read CONFIG
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000002C:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x2: ENABLE (should be 0 after reset)
            enable_read = registers[2].value.to_unsigned()
            assert (enable_read & SPI_EN_BIT) == 0, f"ENABLE reset value should be 0, got 0x{enable_read:08x}"
            
            # x3: CTRL (write-only, read returns 0)
            ctrl_read = registers[3].value.to_unsigned()
            assert ctrl_read == 0, f"CTRL reset value should be 0, got 0x{ctrl_read:08x}"
            
            # x4: STATUS (should be 0: BUSY=0, DONE=0)
            status_read = registers[4].value.to_unsigned()
            assert (status_read & (SPI_STATUS_BUSY | SPI_STATUS_DONE)) == 0, \
                f"STATUS reset should have BUSY=0 and DONE=0, got 0x{status_read:08x}"
            
            # x5: TX_DATA (should be 0)
            tx_data_read = registers[5].value.to_unsigned()
            assert (tx_data_read & 0xFF) == 0, \
                f"TX_DATA reset value should be 0, got 0x{tx_data_read:08x}"
            
            # x6: RX_DATA (should be 0)
            rx_data_read = registers[6].value.to_unsigned()
            assert (rx_data_read & 0xFF) == 0, \
                f"RX_DATA reset value should be 0, got 0x{rx_data_read:08x}"
            
            # x7: CONFIG (divider=31, Mode 0 only)
            config_read = registers[7].value.to_unsigned()
            expected_config = SPI_DIV_1MHZ  # divider=31
            config_masked = config_read & 0xFF  # Only divider bits [7:0] are used
            assert config_masked == expected_config, \
                f"CONFIG reset should be divider=31 (0x{expected_config:02x}), got 0x{config_masked:02x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_spi_tx(dut):
    """Test SPI TX transfer with GPIO[2] as CS control"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Setup GPIO[2] for CS control
        0x00000004: encode_lui(11, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),      # LUI x11, GPIO base upper
        0x00000008: encode_addi(11, 11, GPIO_BASE_ADDR & 0xFFF),           # ADDI x11, x11, GPIO base lower
        # Set CS high initially (GPIO_OUT[2] = 1, CS inactive)
        0x0000000C: encode_addi(12, 0, 0x04),                              # ADDI x12, x0, 0x04 (bit 2 = 1)
        0x00000010: encode_store(11, 12, GPIO_OUT & 0xFFF),                # SW x12, 0x04(x11) - set GPIO_OUT[2] = 1 (CS high)
        # Setup SPI
        0x00000014: encode_lui(1, (SPI_BASE_ADDR >> 12) & 0xFFFFF),        # LUI x1, SPI base upper
        0x00000018: encode_addi(1, 1, SPI_BASE_ADDR & 0xFFF),              # ADDI x1, x1, SPI base lower
        # Enable SPI (must be set at least 1 cycle before START)
        0x0000001C: encode_addi(2, 0, SPI_EN_BIT),                     # ADDI x2, x0, 1
        0x00000020: encode_store(1, 2, SPI_EN & 0xFFF),                 # SW x2, 0x00(x1) - write ENABLE
        # Set CONFIG to a specific value
        0x00000024: encode_addi(2, 0, SPI_DIV_2MHZ | SPI_MODE0),           # ADDI x2, x0, config value
        0x00000028: encode_store(1, 2, SPI_CONFIG & 0xFFF),                # SW x2, 0x14(x1) - write CONFIG
        # Set CS low (GPIO_OUT[2] = 0, CS active)
        0x0000002C: encode_addi(12, 0, 0x00),                              # ADDI x12, x0, 0x00 (clear bit 2)
        0x00000030: encode_store(11, 12, GPIO_OUT & 0xFFF),                # SW x12, 0x04(x11) - set GPIO_OUT[2] = 0 (CS low)
        # Write TX_DATA and START
        0x00000034: encode_addi(5, 0, 0xAA),                               # ADDI x5, x0, 0xAA
        0x00000038: encode_store(1, 5, SPI_TX_DATA & 0xFFF),               # SW x5, 0x0C(x1) - write TX_DATA
        0x0000003C: encode_addi(7, 0, SPI_CTRL_START),                     # ADDI x7, x0, 1
        0x00000040: encode_store(1, 7, SPI_CTRL & 0xFFF),                  # SW x7, 0x04(x1) - write START
        # Wait for transfer to complete
        # Loop: poll STATUS until DONE is set
        0x00000044: encode_load(9, 1, SPI_STATUS & 0xFFF),                 # LW x9, 0x08(x1) - read STATUS
        0x00000048: encode_andi(9, 9, SPI_STATUS_DONE),                    # ANDI x9, x9, SPI_STATUS_DONE bit
        0x0000004C: encode_addi(10, 0, SPI_STATUS_DONE),                   # ADDI x10, x0, SPI_STATUS_DONE
        0x00000050: encode_bne(9, 10, -12),                                # BNE x9, x10, -12 (branch back if not DONE)
        # Set CS high (GPIO_OUT[2] = 1, CS inactive)
        0x00000054: encode_addi(12, 0, 0x04),                              # ADDI x12, x0, 0x04 (bit 2 = 1)
        0x00000058: encode_store(11, 12, GPIO_OUT & 0xFFF),                # SW x12, 0x04(x11) - set GPIO_OUT[2] = 1 (CS high)
        0x0000005C: encode_load(13, 1, SPI_RX_DATA & 0xFFF),               # LW x13, 0x10(x1) - read RX_DATA
        0x00000060: NOP_INSTR,
        0x00000064: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 20000  # Need more cycles for transfer

    clk = dut.clk
    cs_n = dut.spi_cs_n
    sclk = dut.spi_sclk
    mosi = dut.spi_mosi
    miso = dut.spi_miso

    bfm = start_spi_slave_bfm(clk, cs_n, sclk, mosi, miso, tx_data=[0xBB])

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000064:
            registers = dut.soc_inst.cpu_core.register_file.registers

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"

            rx_data = bfm.get_rx_data()
            assert len(rx_data) > 0, "BFM should have received data"
            assert rx_data[0] == 0xAA, \
                f"BFM received wrong data: expected 0xAA, got 0x{rx_data[0]:02x}"

            assert registers[13].value.to_unsigned() == 0xBB, \
                f"RX_DATA register should be 0xBB, got 0x{registers[13].value.to_unsigned():02x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)
    bfm.stop()


async def test_spi_transfer(dut, test_id, length, cpol=0, cpha=0):
    """Test SPI TX transfer with GPIO[2] as CS control"""

    # Get the bin file path from environment variable 
    # The makefile passes this via PLUSARGS which cocotb makes available as environment variable
    bin_file_path = os.environ.get('BIN_FILE', None)
    
    # Check if bin file path is provided and exists
    if bin_file_path is None:
        print("WARNING: BIN_FILE environment variable not set, skipping test")
        return
    
    if not os.path.exists(bin_file_path):
        print(f"WARNING: Bin file not found: {bin_file_path}, skipping test")
        return
    
    # Load memory from bin file
    memory = load_bin_file(bin_file_path)
    # The test program will read the test id from memory[0x01400000]
    write_word_to_memory(memory, 0x01400000, test_id << 24)

    max_cycles = 2000000

    clk = dut.clk
    cs_n = dut.spi_cs_n
    sclk = dut.spi_sclk
    mosi = dut.spi_mosi
    miso = dut.spi_miso

    tx_data = []
    for i in range(length):
        tx_data.append(random.randrange(0, length))


    bfm = start_spi_slave_bfm(clk, cs_n, sclk, mosi, miso, tx_data, cpol, cpha)

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.if_instr.value == 0x00000073:
            registers = dut.soc_inst.cpu_core.register_file.registers

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"

            rx_data = bfm.get_rx_data()
            assert len(rx_data) == length * 2, f"BFM should have received {length} * 2 bytes, got {len(rx_data)}"


            # The spi master will send 256 bytes from 0 to 255, and receive 256 random bytes from bfm (tx_data)
            # Then spi master will send back 256 random bytes back to bfm

            for i in range(length):
                assert rx_data[i] == i, \
                    f"BFM received wrong data: expected 0x{i:02x}, got 0x{rx_data[i]:02x}"

            for i in range(length):
                assert rx_data[i + length] == tx_data[i], \
                    f"BFM received wrong data: expected tx_data[{i} + {length}] = 0x{tx_data[i]:02x}, got 0x{rx_data[i + length]:02x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)
    bfm.stop()


@cocotb.test()
async def test_transfer_multiple_bytes_mode0(dut):
    """Test SPI transfer multiple bytes with mode 0"""

    await test_spi_transfer(dut, 0, 256)


@cocotb.test()
async def test_transfer_multiple_bytes_mode1(dut):
    """Test SPI transfer multiple bytes with mode 1"""

    await test_spi_transfer(dut, 1, 256, cpol=0, cpha=1)

@cocotb.test()
async def test_transfer_multiple_bytes_mode2(dut):
    """Test SPI transfer multiple bytes with mode 0"""

    await test_spi_transfer(dut, 2, 256, cpol=1, cpha=0)

@cocotb.test()
async def test_transfer_multiple_bytes_mode3(dut):
    """Test SPI transfer multiple bytes with mode 3"""

    await test_spi_transfer(dut, 3, 256, cpol=1, cpha=1)

@cocotb.test()
async def test_transfer_single_byte_mode0(dut):
    """Test SPI transfer single byte with mode 0"""

    await test_spi_transfer(dut, 4, 32, cpol=0, cpha=0)

@cocotb.test()
async def test_transfer_single_byte_mode1(dut):
    """Test SPI transfer single byte with mode 1"""

    await test_spi_transfer(dut, 5, 32, cpol=0, cpha=1)

@cocotb.test()
async def test_transfer_single_byte_mode2(dut):
    """Test SPI mode 2"""

    await test_spi_transfer(dut, 6, 32, cpol=1, cpha=0)

@cocotb.test()
async def test_transfer_single_byte_mode3(dut):
    """Test SPI transfer single byte with mode 3"""

    await test_spi_transfer(dut, 7, 32, cpol=1, cpha=1)
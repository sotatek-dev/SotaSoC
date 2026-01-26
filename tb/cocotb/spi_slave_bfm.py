"""
SPI Slave Bus Functional Model (BFM)

This BFM simulates an SPI slave device to test the SPI master peripheral.
Supports SPI Mode 0 only (CPOL=0, CPHA=0).

Mode 0 Protocol:
- Clock idle state: LOW (CPOL=0)
- Data sampling: Rising edge (CPHA=0)
- Data change: Falling edge (CPHA=0)
- MSB first
"""

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer


def safe_int(value, default=0):
    """
    Safely convert a cocotb Logic value to integer.
    
    Args:
        value: Logic value from cocotb signal, or regular integer
        default: Default value to return if signal is X/Z/unresolvable
    
    Returns:
        Integer value (0 or 1) or default if unresolvable
    """
    # If already an integer, return it
    if isinstance(value, int):
        return value
    
    try:
        # Check if it's a Logic value that's not resolvable
        if hasattr(value, 'is_resolvable') and not value.is_resolvable:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


class SPISlaveBFM:
    """
    SPI Slave Bus Functional Model
    
    Simulates an SPI slave device that:
    - Monitors CS (chip select) or enable signal
    - Samples MOSI on rising clock edge (Mode 0)
    - Drives MISO on falling clock edge (Mode 0)
    - Captures received data from MOSI
    - Transmits configured data on MISO
    
    This BFM only requires SPI signals, making it reusable across different testbenches.
    """
    
    def __init__(self, clk, cs_n, sclk, mosi, miso):
        """
        Initialize SPI Slave BFM
        
        Args:
            clk: Clock signal (for synchronization)
            cs_n: Chip select / enable signal (active high for enable, active low for CS_N)
            sclk: SPI clock signal
            mosi: Master Out Slave In (data from master)
            miso: Master In Slave Out (data to master, driven by BFM)
        """
        self.clk = clk
        self.cs_n = cs_n
        self.sclk = sclk
        self.mosi = mosi
        self.miso = miso
        
        # State
        self.rx_buffer = []  # Received data from MOSI
        self.tx_buffer = []  # Data to transmit on MISO
        self.running = False
        self.current_tx_byte = 0xFF  # Default: send 0xFF if no data configured
        
        # Transfer state
        self.bit_count = 0
        self.rx_byte = 0
        self.tx_byte = 0xFF
        self.tx_byte_index = 0
        
        # Previous values for edge detection
        self.prev_sclk = 0
        self.prev_cs_n = 0
    
    def set_tx_data(self, data_list):
        """
        Set data to transmit on MISO
        
        Args:
            data_list: List of bytes to transmit (MSB first)
                      If empty, will send 0xFF for all transfers
        """
        self.tx_buffer = list(data_list)
        self.tx_byte_index = 0
    
    def get_rx_data(self):
        """
        Get received data from MOSI
        
        Returns:
            List of received bytes
        """
        return list(self.rx_buffer)
    
    def clear_rx_buffer(self):
        """Clear received data buffer"""
        self.rx_buffer = []
    
    def clear_tx_buffer(self):
        """Clear transmit data buffer"""
        self.tx_buffer = []
        self.tx_byte_index = 0

    def get_next_tx_byte(self):
        if self.tx_byte_index < len(self.tx_buffer):
            self.tx_byte = self.tx_buffer[self.tx_byte_index]
            self.tx_byte_index += 1
        else:
            # Default: send 0xFF if no more data
            self.tx_byte = 0xFF

    async def run(self):
        """
        Main BFM state machine - runs continuously
        
        Monitors SPI signals and responds as an SPI slave device.
        This should be started as a background task using cocotb.start_soon()
        """
        self.running = True
        
        # Initialize MISO to 0 (or high-Z equivalent)
        self.miso.value = 0

        self.get_next_tx_byte()

        while self.running:
            await RisingEdge(self.clk)
            
            current_cs_n = safe_int(self.cs_n.value)
            current_sclk = safe_int(self.sclk.value)
            # print(f"SPI_MASTER: Running, current_cs_n={current_cs_n}, prev_cs_n={self.prev_cs_n}")
            
            # Detect SPI enable/CS active (transfer start)
            if current_cs_n == 0 and self.prev_cs_n == 1:
                # print(f"SPI_MASTER: Transfer starting")
                # Transfer starting
                self.rx_byte = 0
                
                # Mode 0: Data must be valid before first clock edge
                # Output MSB on MISO before first rising edge
                miso_bit = (self.tx_byte >> 7) & 1
                self.miso.value = miso_bit
                self.bit_count = 1
            
            # Detect SPI disable/CS inactive (transfer end)
            elif current_cs_n == 1 and self.prev_cs_n == 0:
                # print(f"SPI_MASTER: Transfer ending bit_count={self.bit_count}")
                # Transfer ending
                # Master completes transfer after 8 bits (bit_counter == 8)
                # At this point, we should have received 8 bits
                if self.bit_count >= 8:
                    # Complete byte received
                    self.rx_buffer.append(self.rx_byte)
                
                # Reset for next transfer
                self.bit_count = 0
                self.rx_byte = 0
                self.miso.value = 0
            
            # During active transfer
            elif current_cs_n == 0:
                # print(f"SPI_MASTER: Transfer active bit_count={self.bit_count} current_sclk={current_sclk}, prev_sclk={self.prev_sclk}, rx_byte={self.rx_byte}")
                # Detect clock rising edge (sample MOSI)
                if current_sclk == 1 and self.prev_sclk == 0:
                    # Rising edge: Sample MOSI (RX)
                    # Master samples MISO on rising edge, so we sample MOSI here
                    mosi_bit = safe_int(self.mosi.value) & 1
                    self.rx_byte = (self.rx_byte << 1) | mosi_bit
                    # Note: bit_count is incremented after falling edge in master
                    if self.bit_count == 8:
                        # Byte complete - this shouldn't happen on falling edge
                        # as transfer should end when cs_n goes high
                        self.rx_buffer.append(self.rx_byte)
                        self.bit_count = 0
                        self.rx_byte = 0

                        self.get_next_tx_byte()

                # Detect clock falling edge (change MISO)
                elif current_sclk == 0 and self.prev_sclk == 1:
                    # Falling edge: Change MISO (TX)
                    # Master changes MOSI on falling edge, so we change MISO here
                    if self.bit_count < 8:
                        # Output next bit (MSB first)
                        # bit_count represents bits already transferred
                        bit_index = 7 - self.bit_count
                        miso_bit = (self.tx_byte >> bit_index) & 1
                        self.miso.value = miso_bit
                        self.bit_count += 1
                    elif self.bit_count == 8:
                        # Byte complete - this shouldn't happen on falling edge
                        # as transfer should end when cs_n goes high
                        pass
            
            # Update previous values
            self.prev_sclk = current_sclk
            self.prev_cs_n = current_cs_n
    
    def stop(self):
        """Stop the BFM"""
        self.running = False
        self.miso.value = 0
    
    async def wait_for_transfer(self, timeout_cycles=10000):
        """
        Wait for a complete transfer to finish
        
        Args:
            timeout_cycles: Maximum cycles to wait
        
        Returns:
            Received byte (8-bit) or None if timeout
        """
        initial_rx_count = len(self.rx_buffer)
        
        for _ in range(timeout_cycles):
            await RisingEdge(self.clk)
            
            # Check if new byte received
            if len(self.rx_buffer) > initial_rx_count:
                return self.rx_buffer[-1]
            
            # Check if transfer is complete (cs_n goes high)
            if safe_int(self.cs_n.value) == 1 and self.prev_cs_n == 0:
                # Transfer just ended, wait a bit for data to be stored
                await Timer(10, units="ns")
                if len(self.rx_buffer) > initial_rx_count:
                    return self.rx_buffer[-1]
        
        return None  # Timeout
    
    async def wait_for_n_transfers(self, n, timeout_cycles=100000):
        """
        Wait for N complete transfers
        
        Args:
            n: Number of transfers to wait for
            timeout_cycles: Maximum cycles to wait
        
        Returns:
            List of received bytes
        """
        initial_rx_count = len(self.rx_buffer)
        target_count = initial_rx_count + n
        
        for _ in range(timeout_cycles):
            await RisingEdge(self.clk)
            
            if len(self.rx_buffer) >= target_count:
                return self.rx_buffer[initial_rx_count:target_count]
        
        return self.rx_buffer[initial_rx_count:]  # Return what we got (timeout)


# =============================================================================
# Helper Functions
# =============================================================================

def start_spi_slave_bfm(clk, cs_n, sclk, mosi, miso, tx_data=None):
    """
    Create and start an SPI Slave BFM (non-async version)
    
    This function can be called before test_spi_memory() to start BFM
    in background without blocking. The BFM will run concurrently
    with test_spi_memory().
    
    Args:
        clk: Clock signal
        cs_n: Chip select / enable signal
        sclk: SPI clock signal
        mosi: Master Out Slave In signal
        miso: Master In Slave Out signal (driven by BFM)
        tx_data: Optional list of bytes to transmit on MISO
    
    Returns:
        SPISlaveBFM instance (already running in background)
    """
    bfm = SPISlaveBFM(clk, cs_n, sclk, mosi, miso)
    
    if tx_data is not None:
        bfm.set_tx_data(tx_data)
    
    # Start BFM in background (non-blocking)
    cocotb.start_soon(bfm.run())
    
    return bfm


async def create_spi_slave_bfm(clk, cs_n, sclk, mosi, miso, tx_data=None):
    """
    Create and start an SPI Slave BFM (async version)
    
    For compatibility, this function does the same as start_spi_slave_bfm()
    but is async. Use start_spi_slave_bfm() if you don't need await.
    
    Args:
        clk: Clock signal
        cs_n: Chip select / enable signal
        sclk: SPI clock signal
        mosi: Master Out Slave In signal
        miso: Master In Slave Out signal (driven by BFM)
        tx_data: Optional list of bytes to transmit on MISO
    
    Returns:
        SPISlaveBFM instance (already running in background)
    """
    return start_spi_slave_bfm(clk, cs_n, sclk, mosi, miso, tx_data)

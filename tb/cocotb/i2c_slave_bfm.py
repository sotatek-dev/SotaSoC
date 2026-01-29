"""
I2C Slave Bus Functional Model (BFM)

This BFM simulates an I2C slave device connected to the SoC I2C master.

Key properties:
- Standard I2C timing model (START/STOP detection, 8-bit data + ACK)
- 7-bit slave address
- Supports master write and read transactions
- Open-drain bus modelling using the SoC's GPIO-style IO pins

The BFM:
- Computes the actual bus level as wired-AND of master and slave drivers:
    sda_in = 0 if master drives low OR slave drives low, else 1
    scl_in = 0 if master drives low (no clock stretching here), else 1
- Drives sda_in/scl_in via the gpio_io_in bits.
"""

import cocotb
from cocotb.triggers import RisingEdge


def safe_int(value, default=0):
    """
    Safely convert a cocotb Logic value to integer.

    Args:
        value: Logic value from cocotb signal, or regular integer
        default: Default value to return if signal is X/Z/unresolvable

    Returns:
        Integer value (0/1) or default if unresolvable
    """
    if isinstance(value, int):
        return value

    try:
        if hasattr(value, "is_resolvable") and not value.is_resolvable:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


class I2CSlaveBFM:
    """
    I2C Slave Bus Functional Model.

    Simple 7-bit I2C slave:
    - Responds to one configured address
    - Stores bytes written by the master
    - Returns bytes from a TX buffer on read operations

    The protocol model is intentionally simple but sufficient to exercise the
    SoC I2C master:
    - START condition: SDA falls while SCL is high
    - STOP condition : SDA rises while SCL is high
    - Data/Address bits sampled on SCL rising edges, MSB first
    - ACK bit: slave pulls SDA low on 9th clock for ACK, leaves high for NACK
    """

    def __init__(
        self,
        clk,
        sda_out,
        scl_out,
        sda_in,
        scl_in,
        address=0x21,
    ):
        """
        Initialize the I2C slave BFM.

        Args:
            clk: System clock (same clock as I2C master logic)
            sda_out: I2C master SDA output value (always 0 when driving in this design)
            scl_out: I2C master SCL output value (always 0 when driving in this design)
            sda_in: Handle for bus SDA level (drives uio_in[4])
            scl_in: Handle for bus SCL level (drives uio_in[5])
            address: 7-bit slave address (default 0x21, so address byte 0x42 for write)
        """
        self.clk = clk
        self.sda_out = sda_out
        self.scl_out = scl_out
        self.sda_in = sda_in
        self.scl_in = scl_in

        self.address = address & 0x7F

        # Internal storage
        self.rx_bytes = []  # bytes written by master
        self.tx_bytes = []  # bytes to send on read transactions
        self.tx_index = 0

        # Internal state
        self.running = False

        self.prev_sda = 1
        self.prev_scl = 1

        self.state = "IDLE"
        self.bit_count = 0
        self.shift_reg = 0
        self.rw_bit = 0  # 0=write, 1=read
        self.ack_pending = False
        self.sda_in.value = 1

    def set_tx_data(self, data_list):
        """Set data bytes returned to the master on read operations."""
        self.tx_bytes = list(data_list)
        self.tx_index = 0

    def get_rx_data(self):
        """Get data bytes written by the master."""
        return list(self.rx_bytes)

    def _get_next_tx_byte(self):
        if self.tx_index < len(self.tx_bytes):
            b = self.tx_bytes[self.tx_index] & 0xFF
            self.tx_index += 1
            return b
        # Default read data if none configured
        return 0xFF

    async def run(self):
        """
        Main BFM coroutine.

        This should be started with cocotb.start_soon().
        """
        self.running = True

        # Default: lines released (pulled up externally by testbench)
        self.scl_in.value = 1
        self.sda_in.value = 1

        while self.running:
            await RisingEdge(self.clk)

            scl = safe_int(self.scl_out.value)
            sda = safe_int(self.sda_out.value)

            # Detect edges and START/STOP
            prev_scl = self.prev_scl
            prev_sda = self.prev_sda

            rising_scl = (prev_scl == 0 and scl == 1)
            falling_scl = (prev_scl == 1 and scl == 0)
            start_cond = (prev_sda == 1 and sda == 0 and scl == 1)
            stop_cond = (prev_sda == 0 and sda == 1 and scl == 1)

            # START condition always forces a new transaction
            if start_cond:
                self.state = "ADDR"
                self.bit_count = 0
                self.shift_reg = 0
                self.ack_pending = False
                self.sda_in.value = 1

            # STOP condition terminates any ongoing transaction
            if stop_cond:
                self.state = "IDLE"
                self.bit_count = 0
                self.shift_reg = 0
                self.ack_pending = False
                self.sda_in.value = 1

            # Main protocol state machine
            if self.state == "ADDR":
                # Collect 8 bits: 7-bit address + R/W bit
                if rising_scl:
                    self.shift_reg = ((self.shift_reg << 1) | sda) & 0xFF
                    self.bit_count += 1
                    if self.bit_count == 8:
                        self.rx_bytes.append(self.shift_reg)
                        addr = (self.shift_reg >> 1) & 0x7F
                        self.rw_bit = self.shift_reg & 0x1
                if falling_scl:
                    if self.bit_count == 8:
                        # ACK if address matches, otherwise NACK
                        if addr == self.address:
                            self.ack_pending = True
                            self.state = "ACK_ADDR"
                        else:
                            self.ack_pending = False
                            self.state = "IDLE"

            elif self.state == "ACK_ADDR":
                self.sda_in.value = 0  # ACK = 0

                if falling_scl and self.ack_pending:
                    self.sda_in.value = 1
                    self.bit_count = 0
                    self.shift_reg = 0
                    if self.rw_bit == 0:
                        self.state = "DATA_WRITE"
                    else:
                        # Prepare first byte for read
                        self.shift_reg = self._get_next_tx_byte()
                        self.state = "DATA_READ"

                # if falling_scl:

            elif self.state == "DATA_WRITE":
                # Master writing to slave: slave samples SDA on rising SCL,
                # then ACKs after 8 bits.
                if rising_scl:
                    self.shift_reg = ((self.shift_reg << 1) | sda) & 0xFF
                    self.bit_count += 1
                    if self.bit_count == 8:
                        # Full data byte received, ACK it
                        self.rx_bytes.append(self.shift_reg)
                        self.ack_pending = True
                if falling_scl:
                    if self.bit_count == 8:
                        self.state = "ACK_WRITE"

            elif self.state == "ACK_WRITE":
                self.sda_in.value = 0  # ACK
                if falling_scl and self.ack_pending:
                    # ACK sampled, release
                    self.sda_in.value = 1
                    self.ack_pending = False
                    self.bit_count = 0
                    self.shift_reg = 0
                    # Stay in DATA_WRITE until STOP or RESTART
                    self.state = "DATA_WRITE"

            elif self.state == "DATA_READ":
                # Master reading from slave:
                # - Slave drives data while SCL low
                # - Master samples on rising SCL
                if scl == 0 and self.bit_count < 8:
                    bit_index = 7 - self.bit_count
                    self.sda_in.value = ((self.shift_reg >> bit_index) & 0x1)

                if rising_scl:
                    self.bit_count += 1
                    if self.bit_count == 8:
                        # Byte has been shifted out; on the next ACK bit the master
                        # will send ACK/NACK (we release SDA so master can drive)
                        self.sda_in.value = 1
                        self.state = "READ_WAIT_ACK"

            elif self.state == "READ_WAIT_ACK":
                # Master drives ACK/NACK; slave only monitors.
                if rising_scl:
                    # Sample master's ACK (optional, currently ignored)
                    master_ack = (sda == 0)
                    self.bit_count = 0
                    if master_ack:
                        # Prepare next byte
                        self.shift_reg = self._get_next_tx_byte()
                        self.state = "DATA_READ"
                    else:
                        # NACK -> read transaction finished
                        self.state = "IDLE"

            # Save for next cycle
            self.prev_scl = scl
            self.prev_sda = sda

    def stop(self):
        """Stop the BFM."""
        self.running = False
        # Release lines (let them be pulled up by the testbench)
        self.sda_in.value = 1


def start_i2c_slave_bfm(
    clk,
    sda_out,
    scl_out,
    sda_in,
    scl_in,
    address=0x21,
    tx_data=None,
):
    """
    Create and start an I2C Slave BFM (non-async helper).

    This mirrors the SPI BFM helper and is convenient for use from tests.

    Args:
        clk: System clock
        sda_oe, sda_out, scl_oe, scl_out: Master-side I2C control signals
        sda_in, scl_in: Bus SDA/SCL level signals (drive into SoC inputs)
        address: 7-bit I2C slave address
        tx_data: Optional list of bytes to provide on read operations

    Returns:
        I2CSlaveBFM instance (already running in background)
    """
    bfm = I2CSlaveBFM(
        clk=clk,
        sda_out=sda_out,
        scl_out=scl_out,
        sda_in=sda_in,
        scl_in=scl_in,
        address=address,
    )

    if tx_data is not None:
        bfm.set_tx_data(tx_data)

    cocotb.start_soon(bfm.run())
    return bfm


async def create_i2c_slave_bfm(
    clk,
    sda_out,
    scl_out,
    sda_in,
    scl_in,
    address=0x21,
    tx_data=None,
):
    """
    Async wrapper for creating and starting an I2C Slave BFM.

    Returns the same as start_i2c_slave_bfm(), but is an async function
    for stylistic symmetry with the SPI BFM.
    """
    return start_i2c_slave_bfm(
        clk=clk,
        sda_out=sda_out,
        scl_out=scl_out,
        sda_in=sda_in,
        scl_in=scl_in,
        address=address,
        tx_data=tx_data,
    )


import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock

# Constants
CLK_HZ = 62_500_000
CYCLES_PER_INSTRUCTION = 8
MEMORY_CYCLES = 7
NOP_INSTR = 0x00000013
MRET_INSTR = 0x30200073

# Memory base addresses
FLASH_BASE_ADDR = 0x00000000
PSRAM_BASE_ADDR = 0x01000000

# Peripheral base addresses
GPIO_BASE_ADDR  = 0x40001000
TIMER_BASE_ADDR = 0x40002000
PWM_BASE_ADDR   = 0x40003000

# GPIO register offsets
GPIO_DIR      = GPIO_BASE_ADDR + 0x00  # Direction register (bidirectional pins)
GPIO_OUT      = GPIO_BASE_ADDR + 0x04  # Output data register
GPIO_IN       = GPIO_BASE_ADDR + 0x08  # Input data register (read-only)
GPIO_INT_EN   = GPIO_BASE_ADDR + 0x0C  # Interrupt enable (rising edge per pin)
GPIO_INT_PEND = GPIO_BASE_ADDR + 0x14  # Interrupt pending (read-only)
GPIO_INT_CLR  = GPIO_BASE_ADDR + 0x18  # Interrupt clear (write 1 to clear)

# CSR addresses (for interrupt tests)
CSR_MSTATUS = 0x300
CSR_MIE     = 0x304
CSR_MTVEC   = 0x305
CSR_MEPC    = 0x341
CSR_MCAUSE  = 0x342
CSR_MIP     = 0x344

# Timer register offsets
TIMER_MTIME_LO    = TIMER_BASE_ADDR + 0x00
TIMER_MTIME_HI    = TIMER_BASE_ADDR + 0x04
TIMER_MTIMECMP_LO = TIMER_BASE_ADDR + 0x08
TIMER_MTIMECMP_HI = TIMER_BASE_ADDR + 0x0C

# PWM register offsets per channel (16 bytes per channel)
PWM_CH0_CTRL    = PWM_BASE_ADDR + 0x00
PWM_CH0_PERIOD  = PWM_BASE_ADDR + 0x04
PWM_CH0_DUTY    = PWM_BASE_ADDR + 0x08
PWM_CH0_COUNTER = PWM_BASE_ADDR + 0x0C

PWM_CH1_CTRL    = PWM_BASE_ADDR + 0x10
PWM_CH1_PERIOD  = PWM_BASE_ADDR + 0x14
PWM_CH1_DUTY    = PWM_BASE_ADDR + 0x18
PWM_CH1_COUNTER = PWM_BASE_ADDR + 0x1C

# I2C base address and register offsets
I2C_BASE_ADDR   = 0x40004000
I2C_CTRL        = I2C_BASE_ADDR + 0x00
I2C_STATUS      = I2C_BASE_ADDR + 0x04
I2C_DATA        = I2C_BASE_ADDR + 0x08
I2C_PRESCALE    = I2C_BASE_ADDR + 0x0C

# I2C Control register bits
I2C_CTRL_START   = 0x01  # bit 0: Generate START condition
I2C_CTRL_STOP    = 0x02  # bit 1: Generate STOP condition
I2C_CTRL_READ    = 0x04  # bit 2: Read mode (1=read, 0=write)
I2C_CTRL_ACK_EN  = 0x08  # bit 3: ACK enable (1=send ACK, 0=send NACK)
I2C_CTRL_RESTART  = 0x10  # bit 4: Restart request (1=request repeated START on next START command)

# I2C Status register bits
I2C_STATUS_BUSY      = 0x01  # bit 0: Transfer in progress
I2C_STATUS_ACK       = 0x02  # bit 1: ACK received (1=ACK, 0=NACK)
I2C_STATUS_ARB_LOST  = 0x04  # bit 2: Arbitration lost
I2C_STATUS_DONE      = 0x08  # bit 3: Transfer complete
I2C_STATUS_ERROR     = 0x10  # bit 4: Bus error

# I2C Prescaler values for common frequencies @ 64MHz clock
I2C_PRESCALE_100KHZ = 159  # 64MHz / (4 * 160) = 100kHz
I2C_PRESCALE_400KHZ = 39   # 64MHz / (4 * 40) = 400kHz

# SPI base address and register offsets
SPI_BASE_ADDR   = 0x40005000
SPI_CTRL        = SPI_BASE_ADDR + 0x00
SPI_STATUS      = SPI_BASE_ADDR + 0x04
SPI_TX_DATA     = SPI_BASE_ADDR + 0x08
SPI_RX_DATA     = SPI_BASE_ADDR + 0x0C
SPI_CONFIG      = SPI_BASE_ADDR + 0x10

# SPI Control register bits
SPI_CTRL_START  = 0x01  # bit 0: Start transfer

# SPI Status register bits
SPI_STATUS_BUSY = 0x01  # bit 0: Transfer in progress
SPI_STATUS_DONE = 0x02  # bit 1: Transfer complete

# SPI Config register bits
SPI_CONFIG_DIV_MASK  = 0xFF        # bits [7:0]: Clock divider

# SPI Clock divider values for common frequencies @ 64MHz
SPI_DIV_1MHZ  = 31   # 64MHz / (2 * 32) = 1MHz
SPI_DIV_2MHZ  = 15   # 64MHz / (2 * 16) = 2MHz
SPI_DIV_4MHZ  = 7    # 64MHz / (2 * 8) = 4MHz
SPI_DIV_8MHZ  = 3    # 64MHz / (2 * 4) = 8MHz

# SPI Mode 0 (only mode supported)
SPI_MODE0 = 0x000  # CPOL=0, CPHA=0

# RISC-V Instruction Encoding Functions

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


def encode_andi(rd, rs1, imm12):
    """Encode ANDI instruction: rd = rs1 & imm12"""
    return (imm12 << 20) | (rs1 << 15) | (0x7 << 12) | (rd << 7) | 0x13


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


def encode_beq(rs1, rs2, imm13):
    """Encode BEQ instruction: if rs1 == rs2, PC = PC + imm13
    imm13 is the byte offset (must be multiple of 2, LSB is ignored)"""
    # BEQ format: imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode
    # Sign-extend to 32 bits first
    if imm13 & 0x1000:
        imm = imm13 | 0xFFFFE000  # Sign extend negative
    else:
        imm = imm13 & 0x1FFF  # Positive, mask to 13 bits
    # Extract bits from the immediate
    imm12 = (imm >> 12) & 0x1
    imm10_5 = (imm >> 5) & 0x3F  # bits [10:5]
    imm4_1 = (imm >> 1) & 0xF  # bits [4:1]
    imm11 = (imm >> 11) & 0x1
    # Assemble instruction: imm[12|10:5] | rs2 | rs1 | funct3(0) | imm[4:1|11] | opcode(0x63)
    return (imm12 << 31) | (imm10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (0x0 << 12) | (imm4_1 << 8) | (imm11 << 7) | 0x63


def encode_bne(rs1, rs2, imm13):
    """Encode BNE instruction: if rs1 != rs2, PC = PC + imm13
    imm13 is the byte offset (must be multiple of 2, LSB is ignored)"""
    # BNE format: imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode
    # Sign-extend to 32 bits first
    if imm13 & 0x1000:
        imm = imm13 | 0xFFFFE000  # Sign extend negative
    else:
        imm = imm13 & 0x1FFF  # Positive, mask to 13 bits
    # Extract bits from the immediate
    imm12 = (imm >> 12) & 0x1
    imm10_5 = (imm >> 5) & 0x3F  # bits [10:5]
    imm4_1 = (imm >> 1) & 0xF  # bits [4:1]
    imm11 = (imm >> 11) & 0x1
    # Assemble instruction: imm[12|10:5] | rs2 | rs1 | funct3(1) | imm[4:1|11] | opcode(0x63)
    return (imm12 << 31) | (imm10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (0x1 << 12) | (imm4_1 << 8) | (imm11 << 7) | 0x63


def encode_csrrw(rd, csr, rs1):
    """Encode CSRRW instruction: rd = CSR[csr]; CSR[csr] = rs1"""
    return (csr << 20) | (rs1 << 15) | (0x1 << 12) | (rd << 7) | 0x73


def encode_csrrs(rd, csr, rs1):
    """Encode CSRRS instruction: rd = CSR[csr]; CSR[csr] |= rs1"""
    return (csr << 20) | (rs1 << 15) | (0x2 << 12) | (rd << 7) | 0x73


def encode_csrrc(rd, csr, rs1):
    """Encode CSRRC instruction: rd = CSR[csr]; CSR[csr] &= ~rs1"""
    return (csr << 20) | (rs1 << 15) | (0x3 << 12) | (rd << 7) | 0x73


def encode_csrrwi(rd, csr, imm):
    """Encode CSRRWI instruction: rd = CSR[csr]; CSR[csr] = imm"""
    return (csr << 20) | (imm << 15) | (0x5 << 12) | (rd << 7) | 0x73


def encode_csrrsi(rd, csr, imm):
    """Encode CSRRSI instruction: rd = CSR[csr]; CSR[csr] |= imm"""
    return (csr << 20) | (imm << 15) | (0x6 << 12) | (rd << 7) | 0x73


def encode_csrrci(rd, csr, imm):
    """Encode CSRRCI instruction: rd = CSR[csr]; CSR[csr] &= ~imm"""
    return (csr << 20) | (imm << 15) | (0x7 << 12) | (rd << 7) | 0x73

# Global variables to track memory operations
mem_addr = 0x00000000
mem_wdata = 0x00000000
mem_flag = 0x00000000

def get_mem_vars():
    """Get the current memory variables (for testing)"""
    return mem_addr, mem_wdata, mem_flag

def convert_word_memory_to_byte_memory(word_memory):
    """Convert word-aligned memory dictionary to byte-addressed memory dictionary
    
    Args:
        word_memory: Dictionary with word-aligned addresses (keys are multiples of 4) as keys
                    and 32-bit values
        
    Returns:
        Dictionary with byte addresses as keys and byte values (0-255)
    """
    byte_memory = {}
    for word_addr, word_value in word_memory.items():
        # Ensure address is word-aligned
        if word_addr % 4 != 0:
            raise ValueError(f"Memory address 0x{word_addr:08x} is not word-aligned")
        
        # Store bytes in little-endian format
        byte_memory[word_addr] = word_value & 0xFF
        byte_memory[word_addr + 1] = (word_value >> 8) & 0xFF
        byte_memory[word_addr + 2] = (word_value >> 16) & 0xFF
        byte_memory[word_addr + 3] = (word_value >> 24) & 0xFF
    
    return byte_memory

def read_word_from_byte_memory(byte_memory, addr):
    """Read a 32-bit word from byte-addressed memory (little-endian)
    
    Args:
        byte_memory: Dictionary with byte addresses as keys
        addr: Byte address (can be any byte address, not necessarily word-aligned)
    
    Returns:
        32-bit word value
    """
    # Read 4 bytes starting from addr, defaulting to 0 if not present
    byte0 = byte_memory.get(addr, 0)
    byte1 = byte_memory.get(addr + 1, 0)
    byte2 = byte_memory.get(addr + 2, 0)
    byte3 = byte_memory.get(addr + 3, 0)
    
    # Combine in little-endian format
    return (byte3 << 24) | (byte2 << 16) | (byte1 << 8) | byte0

async def do_test(dut, memory, cycles, mem_data=0x00000000):
    """Do test"""
    global mem_addr, mem_wdata, mem_flag

    # Convert word-aligned memory to byte-addressed memory internally
    byte_memory = convert_word_memory_to_byte_memory(memory)

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Read initial instruction from byte memory
    dut.instr_data.value = read_word_from_byte_memory(byte_memory, 0x00000000)
    dut.mem_data.value = mem_data
    dut.instr_ready.value = 0
    dut.mem_ready.value = 0

    # Reset
    dut.rst_n.value = 0
    await Timer(20, unit="ns")
    dut.rst_n.value = 1

    current_pc = 0xFFFFFFFF
    current_mem_we = 0
    current_mem_re = 0
    instr_wait_cycles = 0
    mem_wait_cycles = 0
    
    # Execute for several cycles
    for _ in range(cycles * MEMORY_CYCLES):
        await FallingEdge(dut.clk)
        if mem_wait_cycles == 0 and ((dut.mem_we.value == 1 and current_mem_we == 0) or (dut.mem_re.value == 1 and current_mem_re == 0)):
            dut.mem_ready.value = 0
            mem_wait_cycles = MEMORY_CYCLES
            current_mem_we = dut.mem_we.value
            current_mem_re = dut.mem_re.value

        if mem_wait_cycles > 0:
            mem_wait_cycles -= 1
            if mem_wait_cycles == 0:
                dut.mem_ready.value = 1
                if (current_mem_we == 1):
                    mem_addr = dut.mem_addr.value.to_unsigned()
                    mem_wdata = dut.mem_wdata.value.to_unsigned()
                    mem_flag = dut.mem_flag.value.to_unsigned()
                # Reset current memory operation flags when memory operation completes
                current_mem_we = 0
                current_mem_re = 0

        if instr_wait_cycles == 0 and dut.instr_addr.value.to_unsigned() != current_pc:
            dut.instr_ready.value = 0
            instr_wait_cycles = MEMORY_CYCLES
            current_pc = dut.instr_addr.value.to_unsigned()

        # Only fetch instruction if memory is not busy
        if mem_wait_cycles == 0 and instr_wait_cycles > 0:
            instr_wait_cycles -= 1
            if instr_wait_cycles == 0:
                # Read instruction from byte-addressed memory
                instr_addr = dut.instr_addr.value.to_unsigned()
                dut.instr_data.value = read_word_from_byte_memory(byte_memory, instr_addr)
                dut.instr_ready.value = 1

        # print(f"mem_wait_cycles={mem_wait_cycles}, instr_wait_cycles={instr_wait_cycles}")
        # print(f"Cycle {_}: PC={dut.instr_addr.value.to_unsigned():08x}, Instr={read_word_from_byte_memory(byte_memory, dut.instr_addr.value.to_unsigned()):08x}")
        # print(f"Cycle {_}: mem_addr={dut.mem_addr.value.integer:08x}, mem_data={dut.mem_data.value.integer:08x}, mem_wdata={dut.mem_wdata.value.integer:08x}, mem_flag={dut.mem_flag.value.integer:08x}")
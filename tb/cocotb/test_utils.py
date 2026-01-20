import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock

# Constants
CLK_HZ = 62_500_000
CYCLES_PER_INSTRUCTION = 8
MEMORY_CYCLES = 7
NOP_INSTR = 0x00000013

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

async def do_test(dut, memory, cycles, mem_data=0x00000000):
    """Do test"""
    global mem_addr, mem_wdata, mem_flag

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    dut.instr_data.value = memory[0x00000000]
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
                dut.instr_data.value = memory[dut.instr_addr.value.to_unsigned()]
                dut.instr_ready.value = 1

        # print(f"mem_wait_cycles={mem_wait_cycles}, instr_wait_cycles={instr_wait_cycles}")
        # print(f"Cycle {_}: PC={dut.instr_addr.value.to_unsigned():08x}, Instr={memory[dut.instr_addr.value.to_unsigned()]:08x}")
        # print(f"Cycle {_}: mem_addr={dut.mem_addr.value.integer:08x}, mem_data={dut.mem_data.value.integer:08x}, mem_wdata={dut.mem_wdata.value.integer:08x}, mem_flag={dut.mem_flag.value.integer:08x}") 
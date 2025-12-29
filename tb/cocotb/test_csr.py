import cocotb
from test_utils import NOP_INSTR
from spi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
)


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


# CSR addresses
CSR_MSTATUS = 0x300
CSR_MISA = 0x301
CSR_MIE = 0x304
CSR_MTVEC = 0x305
CSR_MSCRATCH = 0x340
CSR_MEPC = 0x341
CSR_MCAUSE = 0x342
CSR_MTVAL = 0x343
CSR_MIP = 0x344
CSR_CYCLE = 0xC00
CSR_TIME = 0xC01
CSR_INSTRET = 0xC02


@cocotb.test()
async def test_csrrw1(dut):
    """Simple test for CSRRW instruction"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: 0x23410113,  # ADDI x2, x2, 0x234
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: encode_csrrw(3, CSR_MSCRATCH, 1),  # CSRRW x3, mscratch, x1,
        0x00000018: NOP_INSTR,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: encode_csrrw(4, CSR_MSCRATCH, 2),  # CSRRW x4, mscratch, x2,
        0x00000028: NOP_INSTR,
        0x0000002c: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003c: NOP_INSTR,
        0x00000040: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000040:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0x234, f"Register x2 should be 0x234, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0x0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
            assert registers[4].value == 0x123, f"Register x4 should be 0x123, got 0x{registers[4].value.integer:08x}"
            assert csr.mscratch.value == 0x234, f"CSR mscratch should be 0x234, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

@cocotb.test()
async def test_csrrw2(dut):
    """Simple test for CSRRW instruction"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: 0x23410113,  # ADDI x2, x2, 0x234
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: encode_csrrw(3, CSR_MSCRATCH, 1),  # CSRRW x3, mscratch, x1,
        0x00000018: encode_csrrw(4, CSR_MSCRATCH, 2),  # CSRRW x4, mscratch, x2,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002c: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003c: NOP_INSTR,
        0x00000040: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000040:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0x234, f"Register x2 should be 0x234, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0x0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
            assert registers[4].value == 0x123, f"Register x4 should be 0x123, got 0x{registers[4].value.integer:08x}"
            assert csr.mscratch.value == 0x234, f"CSR mscratch should be 0x234, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_csrrw3(dut):
    """Simple test for CSRRW instruction: foward id"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000020:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0, f"Register x2 should be 0, got 0x{registers[2].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_csrrw4(dut):
    """Simple test for CSRRW instruction: forward ex"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: NOP_INSTR,
        0x0000000C: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000020:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0, f"Register x2 should be 0, got 0x{registers[2].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_csrrw5(dut):
    """Simple test for CSRRW instruction: forward id csr -> add"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1,
        0x0000000C: 0x002001b3,  # ADD x3, x0, x2
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000020:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0, f"Register x2 should be 0, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_csrrw6(dut):
    """Simple test for CSRRW instruction: forward id csr -> add"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1,
        0x0000001c: 0x002001b3,  # ADD x3, x0, x2,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002c: NOP_INSTR,
        0x00000030: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000030:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0, f"Register x2 should be 0, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_csrrw7(dut):
    """Simple test for CSRRW instruction: forward id csr -> add"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: encode_csrrw(4, CSR_MSCRATCH, 1),  # CSRRW x4, mscratch, x1,
        0x00000018: NOP_INSTR,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1,
        0x0000002c: 0x002001b3,  # ADD x3, x0, x2,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003c: NOP_INSTR,
        0x00000040: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000040:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0x123, f"Register x2 should be 0x123, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0x123, f"Register x3 should be 0x123, got 0x{registers[3].value.integer:08x}"
            assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

@cocotb.test()
async def test_csrrw8(dut):
    """Simple test for CSRRW instruction: forward id csr -> add"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: encode_csrrw(4, CSR_MSCRATCH, 1),  # CSRRW x4, mscratch, x1,
        0x00000018: NOP_INSTR,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1,
        0x0000002c: NOP_INSTR,
        0x00000030: 0x002001b3,  # ADD x3, x0, x2,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003c: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004c: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000050:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0x123, f"Register x2 should be 0x123, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0x123, f"Register x3 should be 0x123, got 0x{registers[3].value.integer:08x}"
            assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_csrrw9(dut):
    """Simple test for CSRRW instruction: forward id csr -> add"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1,
        0x0000001c: 0x000101b3,  # ADD x3, x2, x0,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002c: NOP_INSTR,
        0x00000030: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000030:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0, f"Register x2 should be 0, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0, f"Register x3 should be 0, got 0x{registers[3].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_csrrw10(dut):
    """Simple test for CSRRW instruction: forward id csr -> add"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: encode_csrrw(4, CSR_MSCRATCH, 1),  # CSRRW x4, mscratch, x1,
        0x00000018: NOP_INSTR,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1,
        0x0000002c: 0x000101b3,  # ADD x3, x2, x0,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003c: NOP_INSTR,
        0x00000040: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000040:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0x123, f"Register x2 should be 0x123, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0x123, f"Register x3 should be 0x123, got 0x{registers[3].value.integer:08x}"
            assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

@cocotb.test()
async def test_csrrw11(dut):
    """Simple test for CSRRW instruction: forward id csr -> add"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x12308093,  # ADDI x1, x0, 0x123
        0x00000008: NOP_INSTR,
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: encode_csrrw(4, CSR_MSCRATCH, 1),  # CSRRW x4, mscratch, x1,
        0x00000018: NOP_INSTR,
        0x0000001c: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: encode_csrrw(2, CSR_MSCRATCH, 1),  # CSRRW x2, mscratch, x1,
        0x0000002c: NOP_INSTR,
        0x00000030: 0x002001b3,  # ADD x3, x0, x2,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        0x0000003c: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004c: NOP_INSTR,
        0x00000050: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000050:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[1].value == 0x123, f"Register x1 should be 0x123, got 0x{registers[1].value.integer:08x}"
            assert registers[2].value == 0x123, f"Register x2 should be 0x123, got 0x{registers[2].value.integer:08x}"
            assert registers[3].value == 0x123, f"Register x3 should be 0x123, got 0x{registers[3].value.integer:08x}"
            assert registers[4].value == 0, f"Register x4 should be 0, got 0x{registers[4].value.integer:08x}"
            assert csr.mscratch.value == 0x123, f"CSR mscratch should be 0x123, got 0x{csr.mscratch.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

@cocotb.test()
async def test_csrrs(dut):
    """Simple test for CSRRS instruction: rd = CSR[csr]; CSR[csr] |= rs1"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00500093,  # ADDI x1, x0, 0x5
        0x00000008: encode_csrrw(0, CSR_MSCRATCH, 1),  # CSRRW x0, mscratch, x1 (mscratch = 5)
        0x0000000C: 0x00300093,  # ADDI x1, x0, 0x3
        0x00000010: encode_csrrs(2, CSR_MSCRATCH, 1),  # CSRRS x2, mscratch, x1
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000024:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file

            assert registers[2].value == 0x5, f"Register x2 (CSRRS read) should be 0x5, got 0x{registers[2].value.integer:08x}"
            assert csr.mscratch.value == 0x7, f"CSR mscratch should be 0x7, got 0x{csr.mscratch.value.integer:08x}"
            
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_csrrc(dut):
    """Simple test for CSRRC instruction: rd = CSR[csr]; CSR[csr] &= ~rs1"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x00700093,  # ADDI x1, x0, 0x7
        0x00000008: encode_csrrw(0, CSR_MSCRATCH, 1),  # CSRRW x0, mscratch, x1 (mscratch = 7)
        0x0000000C: 0x00300093,  # ADDI x1, x0, 0x3
        0x00000010: encode_csrrc(2, CSR_MSCRATCH, 1),  # CSRRC x2, mscratch, x1
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000024:
            registers = dut.soc_inst.cpu_core.register_file.registers
            csr = dut.soc_inst.cpu_core.csr_file
            
            assert registers[2].value == 0x7, f"Register x2 (CSRRC read) should be 0x7, got 0x{registers[2].value.integer:08x}"
            assert csr.mscratch.value == 0x4, f"CSR mscratch should be 0x4, got 0x{csr.mscratch.value.integer:08x}"
            
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)



@cocotb.test()
async def test_csr_instr(dut):
    """Test CSR instructions (CSRRW, CSRRS, CSRRC)"""

    hex_memory = {
        0x00000000: NOP_INSTR,
        # Load immediate values into registers
        0x00000004: 0x12300093,  # ADDI x1, x0, 0x123
        0x00000008: 0x00008113,  # ADDI x2, x1, 0x0000 (x2 = 0x123)
        0x0000000C: 0x00008193,  # ADDI x3, x1, 0x0000 (x3 = 0x123)
        
        # Test CSRRW: Write mscratch with x1, read into x4
        0x00000010: encode_csrrw(4, CSR_MSCRATCH, 1),  # CSRRW x4, mscratch, x1
        # Test CSRRS: Read mscratch into x5, set bits with x2
        0x00000014: encode_csrrs(5, CSR_MSCRATCH, 2),  # CSRRS x5, mscratch, x2
        # Test CSRRC: Read mscratch into x6, clear bits with x3
        0x00000018: encode_csrrc(6, CSR_MSCRATCH, 3),  # CSRRC x6, mscratch, x3
        
        # Test CSRRWI: Write mscratch with immediate 0x5, read into x7
        0x0000001C: encode_csrrwi(7, CSR_MSCRATCH, 5),  # CSRRWI x7, mscratch, 5
        # Test CSRRSI: Read mscratch into x8, set bits with immediate 0x3
        0x00000020: encode_csrrsi(8, CSR_MSCRATCH, 3),  # CSRRSI x8, mscratch, 3
        # Test CSRRCI: Read mscratch into x9, clear bits with immediate 0x7
        0x00000024: encode_csrrci(9, CSR_MSCRATCH, 7),  # CSRRCI x9, mscratch, 7
        
        # Test reading other CSRs
        0x00000028: encode_csrrw(10, CSR_MSTATUS, 0),   # CSRRW x10, mstatus, x0 (read only)
        0x0000002C: encode_csrrw(11, CSR_MISA, 0),      # CSRRW x11, misa, x0 (read only)
        0x00000030: encode_csrrw(12, CSR_MTVEC, 0),     # CSRRW x12, mtvec, x0 (read only)
        
        # Write to mtvec
        0x00000034: 0x10000093,  # ADDI x1, x0, 0x100
        0x00000038: encode_csrrw(13, CSR_MTVEC, 1),    # CSRRW x13, mtvec, x1
        
        # NOPs for completion
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
        0x00000050: NOP_INSTR,
        0x00000054: NOP_INSTR,
        0x00000058: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000050:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            # Check CSRRW: x4 should contain initial mscratch value (0x0 after reset)
            # Then mscratch should be written with x1 (0x123)
            # After CSRRW, x4 = old mscratch (0x0), mscratch = 0x123
            
            # Check CSRRS: x5 should contain mscratch (0x123)
            # Then mscratch |= x2 (0x123), so mscratch = 0x123
            # After CSRRS, x5 = old mscratch (0x123), mscratch = 0x123
            
            # Check CSRRC: x6 should contain mscratch (0x123)
            # Then mscratch &= ~x3 (0x123), so mscratch = 0x0
            # After CSRRC, x6 = old mscratch (0x123), mscratch = 0x0
            
            # Check CSRRWI: x7 should contain mscratch (0x0)
            # Then mscratch = 5, so mscratch = 5
            # After CSRRWI, x7 = old mscratch (0x0), mscratch = 5
            
            # Check CSRRSI: x8 should contain mscratch (5)
            # Then mscratch |= 3, so mscratch = 7
            # After CSRRSI, x8 = old mscratch (5), mscratch = 7
            
            # Check CSRRCI: x9 should contain mscratch (7)
            # Then mscratch &= ~7, so mscratch = 0
            # After CSRRCI, x9 = old mscratch (7), mscratch = 0
            
            # Check mtvec write: x13 should contain old mtvec (0x0)
            # Then mtvec = 0x100
            # After CSRRW, x13 = old mtvec (0x0), mtvec = 0x100
            
            # Note: Register x0 is always 0, so CSRRW with x0 as source doesn't write
            
            # Verify CSRRW result: x4 should be 0 (initial mscratch value)
            assert registers[4].value == 0, f"Register x4 (CSRRW read) should be 0, got 0x{registers[4].value.integer:08x}"
            
            # Verify CSRRS result: x5 should be 0x123 (mscratch after CSRRW)
            assert registers[5].value == 0x123, f"Register x5 (CSRRS read) should be 0x123, got 0x{registers[5].value.integer:08x}"
            
            # Verify CSRRC result: x6 should be 0x123 (mscratch after CSRRS)
            assert registers[6].value == 0x123, f"Register x6 (CSRRC read) should be 0x123, got 0x{registers[6].value.integer:08x}"
            
            # Verify CSRRWI result: x7 should be 0 (mscratch after CSRRC)
            assert registers[7].value == 0, f"Register x7 (CSRRWI read) should be 0, got 0x{registers[7].value.integer:08x}"
            
            # Verify CSRRSI result: x8 should be 5 (mscratch after CSRRWI)
            assert registers[8].value == 5, f"Register x8 (CSRRSI read) should be 5, got 0x{registers[8].value.integer:08x}"
            
            # Verify CSRRCI result: x9 should be 7 (mscratch after CSRRSI)
            assert registers[9].value == 7, f"Register x9 (CSRRCI read) should be 7, got 0x{registers[9].value.integer:08x}"
            
            # Verify mstatus read: x10 should be 0x00001800 (reset value)
            assert registers[10].value == 0x00001800, f"Register x10 (mstatus) should be 0x00001800, got 0x{registers[10].value.integer:08x}"
            
            # Verify misa read: x11 should be 0x40001104 (reset value)
            assert registers[11].value == 0x40001104, f"Register x11 (misa) should be 0x40001104, got 0x{registers[11].value.integer:08x}"
            
            # Verify mtvec read: x12 should be 0 (initial value)
            assert registers[12].value == 0, f"Register x12 (mtvec initial) should be 0, got 0x{registers[12].value.integer:08x}"
            
            # Verify mtvec write and read: x13 should be 0 (old mtvec), new mtvec = 0x100
            assert registers[13].value == 0, f"Register x13 (mtvec old) should be 0, got 0x{registers[13].value.integer:08x}"
            
            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)

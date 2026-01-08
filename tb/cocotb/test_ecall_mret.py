import cocotb
from test_utils import NOP_INSTR
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
)


def encode_csrrw(rd, csr, rs1):
    """Encode CSRRW instruction: rd = CSR[csr]; CSR[csr] = rs1"""
    return (csr << 20) | (rs1 << 15) | (0x1 << 12) | (rd << 7) | 0x73


# CSR addresses
CSR_MSTATUS = 0x300
CSR_MTVEC = 0x305
CSR_MEPC = 0x341
CSR_MCAUSE = 0x342
CSR_MTVAL = 0x343

# Instruction encodings
ECALL_INSTR = 0x00000073  # ECALL: opcode=0x73, funct3=0, imm12=0
MRET_INSTR = 0x30200073   # MRET: opcode=0x73, funct3=0, imm12=0x302


@cocotb.test()
async def test_ecall_basic(dut):
    """Basic test for ECALL instruction: should trigger exception and jump to mtvec"""

    # Set up exception handler address
    exception_handler = 0x00000100
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x10000093,  # ADDI x1, x0, 0x100 (set mtvec)
        0x00000008: encode_csrrw(0, CSR_MTVEC, 1),  # CSRRW x0, mtvec, x1 (mtvec = 0x100)
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: ECALL_INSTR,  # ECALL - should jump to 0x100
        0x0000001C: NOP_INSTR,   # This should not be reached
        0x00000020: NOP_INSTR,
        # Exception handler
        0x00000100: NOP_INSTR,
        0x00000104: NOP_INSTR,
        0x00000108: NOP_INSTR,
        0x0000010C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        # Check when we reach the exception handler
        if dut.soc_inst.cpu_core.instr_addr.value == 0x0000010C:
            csr = dut.soc_inst.cpu_core.csr_file

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0, got 0x{int(dut.soc_inst.error_flag.value)}"

            # Verify exception was handled correctly
            # mepc should contain PC of ECALL instruction (0x18)
            assert csr.mepc.value == 0x18, f"mepc should be 0x18, got 0x{csr.mepc.value.integer:08x}"
            
            # mcause should be 11 (CAUSE_MACHINE_ECALL)
            assert csr.mcause.value == 11, f"mcause should be 11, got 0x{csr.mcause.value.integer:08x}"
            
            # mtval should be 0 for ECALL
            assert csr.mtval.value == 0, f"mtval should be 0, got 0x{csr.mtval.value.integer:08x}"
            
            # mstatus should be updated: MPP=3, MPIE=MIE, MIE=0
            # Initial mstatus = 0x00001800 (MPP=3, MIE=0)
            # After exception: MPP=3, MPIE=0 (since MIE was 0), MIE=0
            # Expected: 0x00001800 (MPP=3, MPIE=0, MIE=0)
            assert csr.mstatus.value.to_unsigned() == 0x00001800, f"mstatus should be 0x00001800, got 0x{csr.mstatus.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_ecall_with_mie_enabled(dut):
    """Test ECALL with MIE enabled: should save MIE to MPIE"""

    exception_handler = 0x00000100
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: 0x10000093,  # ADDI x1, x0, 0x100 (set mtvec)
        0x00000008: encode_csrrw(0, CSR_MTVEC, 1),  # CSRRW x0, mtvec, x1
        0x0000000C: 0x00800093,  # ADDI x1, x0, 0x8 (set MIE bit)
        0x00000010: encode_csrrw(0, CSR_MSTATUS, 1),  # CSRRW x0, mstatus, x1 (enable MIE)
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: ECALL_INSTR,  # ECALL
        0x00000024: NOP_INSTR,
        # Exception handler
        0x00000100: NOP_INSTR,
        0x00000104: NOP_INSTR,
        0x00000108: NOP_INSTR,
        0x0000010C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        if dut.soc_inst.cpu_core.instr_addr.value == 0x0000010C:
            csr = dut.soc_inst.cpu_core.csr_file

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0, got 0x{int(dut.soc_inst.error_flag.value)}"

            # Verify mepc
            assert csr.mepc.value == 0x20, f"mepc should be 0x20, got 0x{csr.mepc.value.integer:08x}"
            
            # Verify mcause
            assert csr.mcause.value == 11, f"mcause should be 11, got 0x{csr.mcause.value.integer:08x}"
            
            # Verify mtval
            assert csr.mtval.value == 0, f"mtval should be 0, got 0x{csr.mtval.value.integer:08x}"
            
            # mstatus: MPP=3, MPIE=1 (MIE was 1), MIE=0
            # Expected: 0x00001800 (MPP=3, MPIE=1, MIE=0)
            assert csr.mstatus.value == 0x00001800, f"mstatus should be 0x00001800, got 0x{csr.mstatus.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_mret_basic(dut):
    """Basic test for MRET instruction: should return from exception handler"""

    exception_handler = 0x00000100
    return_address = 0x00000020
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Setup: set mtvec and simulate exception state
        0x00000004: 0x10000093,  # ADDI x1, x0, 0x100 (set mtvec)
        0x00000008: encode_csrrw(0, CSR_MTVEC, 1),  # CSRRW x0, mtvec, x1
        # Set mstatus to simulate post-exception state (MPP=3, MPIE=1, MIE=0)
        0x0000000C: 0x000010b7,  # LUI x1, 0x1 (x1 = 0x00001000)
        0x00000010: 0x80008093,  # ADDI x1, x1, 0x800 (x1 = 0x00001800)
        0x00000014: encode_csrrw(0, CSR_MSTATUS, 1),  # CSRRW x0, mstatus, x1
        0x00000018: 0x02400093,  # ADDI x1, x0, 0x24 (set mepc)
        0x0000001C: encode_csrrw(0, CSR_MEPC, 1),  # CSRRW x0, mepc, x1
        0x00000020: 0x0e0001ef,  # JAL x3, 0xe0 (jump to exception handler)
        0x00000024: NOP_INSTR,   # Return address (mepc = 0x24)
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
        0x00000038: NOP_INSTR,
        # Exception handler
        0x00000100: NOP_INSTR,
        0x00000104: MRET_INSTR,  # MRET - should jump back to 0x20
        0x00000108: NOP_INSTR,   # This should not be reached
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        # Check when we return from exception handler
        if dut.soc_inst.cpu_core.instr_addr.value == 0x00000038:
            csr = dut.soc_inst.cpu_core.csr_file

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0, got 0x{int(dut.soc_inst.error_flag.value)}"

            # Verify mstatus was updated by MRET
            # Before MRET: mstatus = 0x00001800 (MPP=3, MPIE=1, MIE=0)
            # After MRET: MIE = MPIE = 1, MPIE = 1, MPP = 0
            # Expected: 0x00000888 (MPP=0, MPIE=1, MIE=1)
            assert csr.mstatus.value == 0x00000088, f"mstatus should be 0x00000088, got 0x{csr.mstatus.value.to_unsigned():08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


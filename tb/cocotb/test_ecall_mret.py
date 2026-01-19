import cocotb
from test_utils import (
    NOP_INSTR,
    encode_csrrw,
)
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
)


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
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000010C:
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
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000010C:
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
            assert csr.mstatus.value == 0x00001880, f"mstatus should be 0x00001880, got 0x{csr.mstatus.value.integer:08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_mret_basic(dut):
    """Basic test for MRET instruction: should return from exception handler"""


    hex_memory = {
        0x00000000: NOP_INSTR,
        # Setup: set mtvec to point to exception handler
        0x00000004: 0x10000093,  # ADDI x1, x0, 0x100 (set mtvec)
        0x00000008: encode_csrrw(0, CSR_MTVEC, 1),  # CSRRW x0, mtvec, x1 (mtvec = 0x100)
        0x0000000C: NOP_INSTR,
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: ECALL_INSTR,  # ECALL - should jump to 0x100 (exception handler)
        0x0000001C: NOP_INSTR,   # Return address after ECALL (mepc + 4 = 0x18 + 4 = 0x1C)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        # Exception handler
        0x00000100: encode_csrrw(1, CSR_MEPC, 0),  # CSRRW x1, mepc, x0 (read mepc into x1)
        0x00000104: 0x00408093,  # ADDI x1, x1, 4 (increment mepc by 4 to skip ECALL)
        0x00000108: encode_csrrw(0, CSR_MEPC, 1),  # CSRRW x0, mepc, x1 (write updated mepc back)
        0x0000010C: MRET_INSTR,  # MRET - should jump back to 0x1C (address after ECALL)
        0x00000110: NOP_INSTR,   # This should not be reached
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)

    max_cycles = 10000

    def callback(dut, memory):
        # Check when we return from exception handler to address after ECALL
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000024:
            csr = dut.soc_inst.cpu_core.csr_file

            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0, got 0x{int(dut.soc_inst.error_flag.value)}"

            # Verify mstatus was updated by MRET
            # After ECALL: mstatus has MPP=3, MPIE=MIE (from before), MIE=0
            # After MRET: MIE = MPIE, MPIE = 1, MPP = 0
            # Since initial MIE was 0, after MRET: MIE = 0, MPIE = 1, MPP = 0
            # Expected: 0x00000080 (MPP=0, MPIE=1, MIE=0)
            assert csr.mstatus.value.to_unsigned() == 0x00000080, f"mstatus should be 0x00000080, got 0x{csr.mstatus.value.to_unsigned():08x}"

            return True
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)


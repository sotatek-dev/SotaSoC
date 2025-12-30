import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
import random

@cocotb.test()
async def test_soc(dut):
    """Test the SoC"""

    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await Timer(15, unit="ns")
    dut.rst_n.value = 1

    instr_fetch_delay = int(dut.soc_inst.mem_ctrl.INSTR_FETCH_DELAY.value) + 1

    max_cycles = 200000;
    cycles = 0;
    
    # Execute for several cycles
    for _ in range(max_cycles):
        await RisingEdge(dut.clk)
        if dut.soc_inst.cpu_core.instr_data.value.to_unsigned() == 0x00000073:
            cycles = 5 * instr_fetch_delay;
            print(f"Intruction: 0x{int(dut.soc_inst.cpu_core.instr_data.value):08x}, PC: 0x{int(dut.soc_inst.cpu_core.instr_addr.value):08x}")
            print("Found ECALL instruction")
        if cycles > 0:
            cycles -= 1;
            if cycles == 0:
                print("Test finished, checking results")
                registers = dut.soc_inst.cpu_core.register_file.registers
                assert registers[10].value.to_unsigned() == 0, f"Register x10 should be 0, got 0x{registers[10].value.to_unsigned():08x}"
                return;

    assert False, "Didn't find ECALL instruction"
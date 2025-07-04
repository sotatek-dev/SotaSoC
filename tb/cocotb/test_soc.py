import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
import random

@cocotb.test()
async def test_soc(dut):
    """Test the SoC"""

    cycles = 100

    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    
    # Execute for several cycles
    for i in range(cycles):
        await FallingEdge(dut.clk)
        # print(f"Cycle {i}")

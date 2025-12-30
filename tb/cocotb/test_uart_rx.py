import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
import random

@cocotb.test()
async def test_uart_rx(dut):
    """Test the UART RX"""

    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await Timer(15, unit="ns")
    dut.rst_n.value = 1

    instr_fetch_delay = dut.soc_inst.mem_ctrl.INSTR_FETCH_DELAY.value + 1

    max_cycles = 10000;
    cycles = 0;

    uart_cycles = -1;
    bit_index = 0;
    bits = [0, 1, 1, 0, 0, 0, 0, 1, 0, 1]; # start bit, C (0x43), stop bit

    for _ in range(max_cycles):
        await RisingEdge(dut.clk)
        
        if uart_cycles >= 0:
            if uart_cycles % 87 == 0:
                bit_index += 1;
                if bit_index < len(bits):
                    dut.soc_inst.uart_rx.value = bits[bit_index];
            uart_cycles -= 1;

        if dut.soc_inst.mem_ctrl.uart_rx_en == 1:
            if uart_cycles < 0:
                uart_cycles = 87 * 20 - 1;
                bit_index = 0;
                dut.soc_inst.uart_rx.value = bits[bit_index];
            # print(f"UART RX: {dut.soc_inst.mem_ctrl.uart_rx_data.value}")

        if dut.soc_inst.cpu_core.instr_data.value == 0x00000073:
            cycles = 5 * instr_fetch_delay;
            print(f"Intruction: 0x{int(dut.soc_inst.cpu_core.instr_data.value):08x}, PC: 0x{int(dut.soc_inst.cpu_core.instr_addr.value):08x}")
            print("Found ECALL instruction")
        if cycles > 0:
            cycles -= 1;
            if cycles == 0:
                print("Test finished, checking results")
                registers = dut.soc_inst.cpu_core.register_file.registers
                assert registers[10].value == 0, f"Register x10 should be 0, got 0x{registers[10].value.integer:08x}"
                assert registers[7].value == 0x43, f"Register x7 should be 0x43, got 0x{registers[7].value.integer:08x}"
                return;

    assert False, "Didn't find ECALL instruction"
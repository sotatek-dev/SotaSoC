import cocotb
import os
from test_utils import NOP_INSTR
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
    read_word_from_memory,
    load_hex_file,
)
import random

@cocotb.test()
async def test_uart_rx(dut):
    """Test the UART RX"""

    hex_file_path = os.environ.get('HEX_FILE', None)

    # Load memory from hex file
    memory = load_hex_file(hex_file_path)

    instr_fetch_delay = 32

    max_cycles = 10000;
    cycles = 0;

    uart_cycles = -1;
    bit_index = 0;
    bits = [0, 1, 1, 0, 0, 0, 0, 1, 0, 1]; # start bit, C (0x43), stop bit

    def callback(dut, memory):
        nonlocal cycles
        nonlocal uart_cycles
        nonlocal bit_index

        if uart_cycles >= 0:
            if uart_cycles % 87 == 0:
                bit_index += 1;
                if bit_index < len(bits):
                    dut.soc_inst.uart_rx.value = bits[bit_index];
            uart_cycles -= 1;

        if dut.soc_inst.mem_ctrl.uart_rx_en.value == 1:
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
                return True;
        return False

    await test_spi_memory(dut, memory, max_cycles, callback)
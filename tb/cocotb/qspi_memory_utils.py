import cocotb
import os
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
from test_utils import NOP_INSTR, CLK_HZ, FLASH_BASE_ADDR, PSRAM_BASE_ADDR

FSM_IDLE = 0
FSM_SEND_CMD = 1
FSM_SEND_CMD_QUAD = 2
FSM_SEND_ADDR = 3
FSM_DUMMY = 4
FSM_DATA_TRANSFER = 5
FSM_PAUSE = 6
FSM_DONE = 7

def print_debug(message):
    # print(message)
    return 0

def get_packed_bit(handle, bit_index):
    """Get a single bit from a packed array/struct handle"""
    return (int(handle.value) >> bit_index) & 1

def set_packed_bit(handle, bit_index, value):
    """Set a single bit in a packed array/struct handle"""
    current_val = 0
    handle.value = (current_val & ~(1 << bit_index)) | ((value & 1) << bit_index)

def convert_hex_memory_to_byte_memory(hex_memory):
    """Convert hex memory to byte memory"""
    byte_memory = bytearray(32 * 1024 * 1024)
    for addr, value in hex_memory.items():
        byte_memory[addr] = value & 0xFF
        byte_memory[addr + 1] = (value >> 8) & 0xFF
        byte_memory[addr + 2] = (value >> 16) & 0xFF
        byte_memory[addr + 3] = (value >> 24) & 0xFF
    return byte_memory

def load_bin_file(bin_file_path):
    """Load binary file and return byte-addressed memory array"""
    # Create byte-addressed memory (like RTL unified_mem)
    memory = bytearray(32 * 1024 * 1024)  # 32MB memory space
    
    if bin_file_path and os.path.exists(bin_file_path):
        with open(bin_file_path, 'rb') as f:
            binary_data = f.read()
            # Copy binary data directly into memory starting at address 0x00000000
            memory[0:len(binary_data)] = binary_data
        fill_start = len(binary_data)
        print(f"Loaded {len(binary_data)} bytes from {bin_file_path}")
    else:
        print(f"Warning: Binary file not found or not specified: {bin_file_path}")
        # Fill with default NOP instructions
        for i in range(0, 16, 4):
            nop = NOP_INSTR
            memory[i] = nop & 0xFF
            memory[i + 1] = (nop >> 8) & 0xFF
            memory[i + 2] = (nop >> 16) & 0xFF
            memory[i + 3] = (nop >> 24) & 0xFF
        fill_start = 16

    # Fill the rest with random bytes to simulate uninitialized RAM
    remaining = len(memory) - fill_start
    memory[fill_start:] = os.urandom(remaining)

    return memory

def read_word_from_memory(memory, addr):
    """Read a 32-bit word from byte-addressed memory (little-endian)"""
    return ((memory[addr] << 24) | 
            (memory[addr + 1] << 16) | 
            (memory[addr + 2] << 8) | 
            (memory[addr + 3]))

def write_word_to_memory(memory, addr, data):
    """Write a 32-bit word to byte-addressed memory (little-endian)"""
    memory[addr] = (data >> 24) & 0xFF
    memory[addr + 1] = (data >> 16) & 0xFF
    memory[addr + 2] = (data >> 8) & 0xFF
    memory[addr + 3] = data & 0xFF

def read_halfword_from_memory(memory, addr):
    """Read a 16-bit halfword from byte-addressed memory (little-endian)"""
    return (memory[addr] << 8) | (memory[addr + 1])

def write_halfword_to_memory(memory, addr, data):
    """Write a 16-bit halfword to byte-addressed memory (little-endian)"""
    memory[addr] = (data >> 8) & 0xFF
    memory[addr + 1] = data & 0xFF

def read_byte_from_memory(memory, addr):
    """Read a 8-bit byte from byte-addressed memory"""
    return memory[addr]

def write_byte_to_memory(memory, addr, data):
    """Write a 8-bit byte to byte-addressed memory"""
    memory[addr] = data & 0xFF

async def test_spi_memory(dut, memory, max_cycles, callback):
    """Test the SPI memory"""

    clk_cycle_time = 1_000_000_000 / CLK_HZ

    clock = Clock(dut.clk, clk_cycle_time, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await Timer(45, unit="ns")
    dut.rst_n.value = 1

    is_instr = False
    flash_in_cont_mode = False
    command = 0x00
    fsm_state = FSM_IDLE
    bit_counter = 0
    addr = 0x000000
    data = 0x00000000

    cycles = 0

    spi_clk_high = True

    dut.bus_io_in.value = 0;

    for _ in range(max_cycles):
        if fsm_state == FSM_IDLE:
            await FallingEdge(dut.clk)
            if dut.flash_cs_n.value == 0:
                print_debug(f"SPI_IDLE: start flash access, flash_in_cont_mode={flash_in_cont_mode}")
                is_instr = True
                if flash_in_cont_mode:
                    command = 0xEB
                    fsm_state = FSM_SEND_ADDR
                else:
                    command = 0
                    fsm_state = FSM_SEND_CMD
                bit_counter = 0
                dut.bus_io_in.value = 0;
                addr = 0
                data = 0
            if dut.ram_cs_n.value == 0:
                print_debug(f"SPI_IDLE: start ram access")
                is_instr = False
                fsm_state = FSM_SEND_CMD_QUAD
                bit_counter = 0
                dut.bus_io_in.value = 0;
                command = 0
                addr = 0
                data = 0
        else:
            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")
            if dut.bus_sclk.value == 1:
                spi_clk_high = True

            if (is_instr == True and dut.flash_cs_n.value == 1) or (is_instr == False and dut.ram_cs_n.value == 1):
                print_debug(f"SPI_: is_instr={is_instr} fsm_state={fsm_state}, command={command}, bit_counter={bit_counter}, addr=0x{addr:08x}, data=0x{data:08x}")
                if not is_instr and command == 0x38:
                    if bit_counter > 0:
                        print(f"SPI: Writing {bit_counter} bits to memory: addr=0x{addr:08x}, data=0x{data:08x})")
                        if (bit_counter == 32):
                            write_word_to_memory(memory, addr, data)
                        elif (bit_counter == 16):
                            write_halfword_to_memory(memory, addr, data)
                        elif (bit_counter == 8):
                            write_byte_to_memory(memory, addr, data)
                        else:
                            assert False, f"Invalid bit_counter: {bit_counter}"
                # assert False, "SPI CSN is not active"
                fsm_state = FSM_IDLE
                
            if fsm_state == FSM_SEND_CMD:
                if dut.bus_sclk.value == 1:
                    print_debug(f"SPI1: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.bus_sclk.value}, spi_io_in={dut.bus_io_in.value}, addr=0x{addr:08x}")
                    if dut.bus_sclk.value == 1:
                        command = (command << 1) | get_packed_bit(dut.bus_io_out, 0)
                        bit_counter += 1
                        if bit_counter == 8:
                            fsm_state = FSM_SEND_ADDR
                            bit_counter = 0
            elif fsm_state == FSM_SEND_CMD_QUAD:
                if dut.bus_sclk.value == 1:
                    print_debug(f"SPI2: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.bus_sclk.value}, spi_io_in={dut.bus_io_in.value}, addr=0x{addr:08x}")
                    if dut.bus_sclk.value == 1:
                        command = (command << 4) | int(dut.bus_io_out.value)
                        bit_counter += 4
                        if bit_counter == 8:
                            fsm_state = FSM_SEND_ADDR
                            bit_counter = 0
            elif fsm_state == FSM_SEND_ADDR:
                if dut.bus_sclk.value == 1:
                    print_debug(f"SPI3: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.bus_sclk.value}, spi_io_in={dut.bus_io_in.value}, addr=0x{addr:08x}")
                    if dut.bus_sclk.value == 1:
                        addr = (addr << 4) | int(dut.bus_io_out.value)
                        bit_counter += 4
                        if bit_counter == 24:
                            bit_counter = 0
                            if is_instr:
                                fsm_state = FSM_DUMMY
                                addr = addr + FLASH_BASE_ADDR
                                print(f"SPI: Reading from instr memory: addr=0x{addr:08x}")
                                data = read_word_from_memory(memory, addr)
                                print(f"SPI: data: 0x{data:08x}")
                            else:
                                addr = addr + PSRAM_BASE_ADDR
                                if command == 0xEB:
                                    fsm_state = FSM_DUMMY
                                    print(f"SPI: Reading from data memory: addr=0x{addr:08x}")
                                    data = read_word_from_memory(memory, addr)
                                    print(f"SPI: data: 0x{data:08x}")
                                else:
                                    fsm_state = FSM_DATA_TRANSFER
                                    print(f"SPI: Writing to data memory: addr=0x{addr:08x}")
                                    data = 0
            elif fsm_state == FSM_DUMMY:
                # await RisingEdge(dut.spi_sclk)
                if dut.bus_sclk.value == 1:
                    print_debug(f"SPI4: is_instr={is_instr} fsm_state=DUMMY, bit_counter={bit_counter}, spi_sclk={dut.bus_sclk.value}, spi_io_in={dut.bus_io_in.value}, addr=0x{addr:08x}")
                    if dut.bus_sclk.value == 1:
                        bit_counter += 1
                        if bit_counter == 6:
                            fsm_state = FSM_DATA_TRANSFER
                            bit_counter = 0
                            print(f"SPI: End dummy phase")
            else:
                if is_instr:
                    if dut.bus_sclk.value == 0 and spi_clk_high == True:
                        spi_clk_high = False
                        print_debug(f"SPI5: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.bus_sclk.value}, spi_io_in={dut.bus_io_in.value}, addr=0x{addr:08x}")
                        if fsm_state == FSM_DATA_TRANSFER:
                            if dut.bus_sclk.value == 0:
                                # print(f"SPI MISO: bit_counter={bit_counter}, spi_io_in[1]={data & 1}, instr_data=0x{data:08x}")
                                dut.bus_io_in.value = ((data & 0xFFFFFFFF) >> (28 - bit_counter)) & 0xF
                                bit_counter += 4
                                flash_in_cont_mode = True
                                if bit_counter == 32:
                                    bit_counter = 0
                                    addr = addr + 4
                                    print(f"SPI: Reading next instr from instr memory: addr=0x{addr:08x}")
                                    data = read_word_from_memory(memory, addr)
                                    print(f"SPI: data: 0x{data:08x}")

                        elif fsm_state == FSM_DONE:
                            fsm_state = FSM_IDLE
                elif not is_instr and command == 0xEB:
                    if dut.bus_sclk.value == 0 and spi_clk_high == True:
                        spi_clk_high = False
                        print_debug(f"SPI5: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.bus_sclk.value}, spi_io_in={dut.bus_io_in.value}, addr=0x{addr:08x}")
                        if fsm_state == FSM_DATA_TRANSFER:
                            if dut.bus_sclk.value == 0:
                                dut.bus_io_in.value = ((data & 0xFFFFFFFF) >> (28 - bit_counter)) & 0xF
                                bit_counter += 4
                                if bit_counter == 32:
                                    bit_counter = 0
                                    addr = addr + 4

                        elif fsm_state == FSM_DONE:
                            fsm_state = FSM_IDLE
                else:
                    # await RisingEdge(dut.spi_sclk)
                    if dut.bus_sclk.value == 0:
                        print_debug(f"SPI6: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.bus_sclk.value}, spi_io_in={dut.bus_io_in.value}, addr=0x{addr:08x}")
                        if fsm_state == FSM_DATA_TRANSFER:
                            data = (data << 4) | int(dut.bus_io_out.value)
                            bit_counter += 4
                            if bit_counter == 32:
                                print(f"SPI: Write data: addr=0x{addr:08x}, data=0x{data:08x}")
                                write_word_to_memory(memory, addr, data)
                                fsm_state = FSM_DONE
                        elif fsm_state == FSM_DONE:
                            fsm_state = FSM_IDLE

        if callback(dut, memory):
            return

    assert False, "Failed"


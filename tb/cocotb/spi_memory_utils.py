import cocotb
import os
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
from test_utils import NOP_INSTR

FSM_IDLE = 0
FSM_SEND_CMD_ADDR = 1
FSM_DATA_TRANSFER = 2
FSM_DONE_STATE = 3

def convert_hex_memory_to_byte_memory(hex_memory):
    """Convert hex memory to byte memory"""
    byte_memory = bytearray(16 * 1024 * 1024)
    for addr, value in hex_memory.items():
        byte_memory[addr] = value & 0xFF
        byte_memory[addr + 1] = (value >> 8) & 0xFF
        byte_memory[addr + 2] = (value >> 16) & 0xFF
        byte_memory[addr + 3] = (value >> 24) & 0xFF
    return byte_memory

def load_hex_file(hex_file_path):
    """Load hex file and return byte-addressed memory array"""
    # Create byte-addressed memory (like RTL unified_mem)
    memory = bytearray(16 * 1024 * 1024)  # 16MB memory space
    
    if hex_file_path and os.path.exists(hex_file_path):
        with open(hex_file_path, 'r') as f:
            addr = 0x00000000
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        instr = int(line, 16)
                        # Store as little-endian bytes (matching RTL behavior)
                        memory[addr] = instr & 0xFF
                        memory[addr + 1] = (instr >> 8) & 0xFF
                        memory[addr + 2] = (instr >> 16) & 0xFF
                        memory[addr + 3] = (instr >> 24) & 0xFF
                        addr += 4
                    except ValueError:
                        print(f"Warning: Invalid hex line: {line}")
                        continue
        print(f"Loaded {(addr)//4} instructions from {hex_file_path}")
    else:
        print(f"Warning: Hex file not found or not specified: {hex_file_path}")
        # Fill with default NOP instructions
        for i in range(0, 16, 4):
            nop = NOP_INSTR
            memory[i] = nop & 0xFF
            memory[i + 1] = (nop >> 8) & 0xFF
            memory[i + 2] = (nop >> 16) & 0xFF
            memory[i + 3] = (nop >> 24) & 0xFF
    
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

    clk_hz = dut.soc_inst.CLK_HZ.value
    clk_cycle_time = 1000000000 / clk_hz

    clock = Clock(dut.clk, clk_cycle_time, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await Timer(15, units="ns")
    dut.rst_n.value = 1

    is_instr = False
    command = 0x00
    fsm_state = FSM_IDLE
    bit_counter = 0
    addr = 0x00000000
    data = 0x00000000

    cycles = 0

    dut.soc_inst.spi_miso.value = 0

    for _ in range(max_cycles):
        if fsm_state == FSM_IDLE:
            await FallingEdge(dut.clk)
            if dut.soc_inst.flash_cs_n.value == 0:
                is_instr = True
                fsm_state = FSM_SEND_CMD_ADDR
                bit_counter = 0
                dut.soc_inst.spi_miso.value = 0
                addr = 0
                data = 0
            if dut.soc_inst.ram_cs_n.value == 0:
                is_instr = False
                fsm_state = FSM_SEND_CMD_ADDR
                bit_counter = 0
                dut.soc_inst.spi_miso.value = 0
                addr = 0
                data = 0
        else:
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            if (is_instr == True and dut.soc_inst.flash_cs_n.value == 1) or (is_instr == False and dut.soc_inst.ram_cs_n.value == 1):
                # print(f"SPI1: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, addr=0x{addr:08x}, data=0x{data:08x}")
                if not is_instr and command == 0x02:
                    if bit_counter > 0:
                        print(f"Writing {bit_counter} bits to memory: addr=0x{addr:08x}, data=0x{data:08x})")
                        if (bit_counter == 32):
                            write_word_to_memory(memory, addr & 0x00FFFFFF, data)
                        elif (bit_counter == 16):
                            write_halfword_to_memory(memory, addr & 0x00FFFFFF, data)
                        elif (bit_counter == 8):
                            write_byte_to_memory(memory, addr & 0x00FFFFFF, data)
                        else:
                            assert False, f"Invalid bit_counter: {bit_counter}"
                # assert False, "SPI CSN is not active"
                fsm_state = FSM_IDLE
                
            if fsm_state == FSM_SEND_CMD_ADDR:
                # await RisingEdge(dut.soc_inst.spi_sclk)
                if dut.soc_inst.spi_sclk.value == 1:
                    # print(f"SPI1: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.soc_inst.spi_sclk.value}, spi_miso={dut.soc_inst.spi_miso.value}, addr=0x{addr:08x}")
                    if dut.soc_inst.spi_sclk.value == 1:
                        addr = (addr << 1) | dut.soc_inst.spi_mosi.value
                        bit_counter += 1
                        if bit_counter == 32:
                            fsm_state = FSM_DATA_TRANSFER
                            bit_counter = 0
                            if is_instr:
                                print(f"Reading from instr memory: addr=0x{addr:08x}")
                                data = read_word_from_memory(memory, addr & 0x00FFFFFF)
                                print(f"data: 0x{data:08x}")
                            else:
                                command = (addr >> 24) & 0xFF
                                if command == 0x03:
                                    print(f"Reading from data memory: addr=0x{addr:08x}")
                                    data = read_word_from_memory(memory, addr & 0x00FFFFFF)
                                    print(f"data: 0x{data:08x}")
                                else:
                                    print(f"Writing to data memory: addr=0x{addr:08x}")
                                    data = 0
            else:
                if is_instr or (not is_instr and command == 0x03):
                    # await FallingEdge(dut.soc_inst.spi_sclk)
                    if dut.soc_inst.spi_sclk.value == 0:
                        # print(f"SPI2: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.soc_inst.spi_sclk.value}, spi_miso={dut.soc_inst.spi_miso.value}, addr=0x{addr:08x}")
                        if fsm_state == FSM_DATA_TRANSFER:
                            if dut.soc_inst.spi_sclk.value == 0:
                                # print(f"SPI MISO: bit_counter={bit_counter}, spi_miso={data & 1}, instr_data=0x{data:08x}")
                                dut.soc_inst.spi_miso.value = ((data & 0xFFFFFFFF) >> (31 - bit_counter)) & 1
                                bit_counter += 1
                                if bit_counter == 32:
                                    fsm_state = FSM_DONE_STATE
                        elif fsm_state == FSM_DONE_STATE:
                            fsm_state = FSM_IDLE
                            if is_instr:
                                await RisingEdge(dut.soc_inst.flash_cs_n)
                            else:
                                await RisingEdge(dut.soc_inst.ram_cs_n)
                else:
                    # await RisingEdge(dut.soc_inst.spi_sclk)
                    if dut.soc_inst.spi_sclk.value == 0:
                        # print(f"SPI3: is_instr={is_instr} fsm_state={fsm_state}, bit_counter={bit_counter}, spi_sclk={dut.soc_inst.spi_sclk.value}, spi_miso={dut.soc_inst.spi_miso.value}, addr=0x{addr:08x}")
                        if fsm_state == FSM_DATA_TRANSFER:
                            data = (data << 1) | dut.soc_inst.spi_mosi.value
                            bit_counter += 1
                            if bit_counter == 32:
                                print(f"Write data: addr=0x{addr:08x}, data=0x{data:08x}")
                                write_word_to_memory(memory, addr & 0x00FFFFFF, data)
                                fsm_state = FSM_DONE_STATE
                        elif fsm_state == FSM_DONE_STATE:
                            fsm_state = FSM_IDLE

        if callback(dut, memory):
            return

    assert False, "Failed"


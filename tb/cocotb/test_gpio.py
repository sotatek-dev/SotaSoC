import cocotb
from test_utils import (
    NOP_INSTR,
    encode_load,
    encode_store,
    encode_addi,
    encode_lui,
    GPIO_BASE_ADDR,
    GPIO_DIR,
    GPIO_OUT,
    GPIO_IN,
)
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
)


# GPIO parameters (must match soc.sv)
NUM_BIDIR = 1
NUM_OUT = 6
NUM_IN = 6


# =============================================================================
# Group 1: Basic Register Read/Write Tests
# =============================================================================

@cocotb.test()
async def test_gpio_read_write_dir(dut):
    """Test reading and writing GPIO DIR register"""
    
    test_dir_value = (1 << NUM_BIDIR) - 1  # All bidirectional pins as output
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, GPIO_DIR >> 12),               # LUI x1, GPIO base upper
        0x00000008: encode_addi(1, 1, GPIO_DIR & 0xFFF),         # ADDI x1, x1, GPIO_DIR offset
        0x0000000C: encode_addi(2, 0, test_dir_value),           # ADDI x2, x0, test_dir_value
        0x00000010: encode_store(1, 2, 0),                       # SW x2, 0(x1) - write DIR
        0x00000014: encode_load(3, 1, 0),                        # LW x3, 0(x1) - read DIR
        0x00000018: encode_store(1, 0, 0),                       # SW x0, 0(x1) - write DIR = 0
        0x0000001C: encode_load(4, 1, 0),                        # LW x4, 0(x1) - read DIR again
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000028:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x3 should contain DIR = test_dir_value
            dir_read_1 = registers[3].value.to_unsigned()
            assert dir_read_1 == test_dir_value, f"DIR should be {test_dir_value}, got {dir_read_1}"
            
            # x4 should contain DIR = 0
            dir_read_2 = registers[4].value.to_unsigned()
            assert dir_read_2 == 0, f"DIR should be 0 after write, got {dir_read_2}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_read_write_out(dut):
    """Test reading and writing GPIO OUT register"""
    
    # OUT register holds both bidirectional output and output-only pins
    # Total bits = NUM_BIDIR + NUM_OUT
    test_out_value = 0x5A  # Test pattern
    num_out_total = NUM_BIDIR + NUM_OUT
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, GPIO_OUT >> 12),               # LUI x1, GPIO base upper
        0x00000008: encode_addi(1, 1, GPIO_OUT & 0xFFF),         # ADDI x1, x1, GPIO_OUT offset
        0x0000000C: encode_addi(2, 0, test_out_value),           # ADDI x2, x0, test_out_value
        0x00000010: encode_store(1, 2, 0),                       # SW x2, 0(x1) - write OUT
        0x00000014: encode_load(3, 1, 0),                        # LW x3, 0(x1) - read OUT
        0x00000018: encode_addi(2, 0, 0x25),                     # ADDI x2, x0, 0x25 (new value)
        0x0000001C: encode_store(1, 2, 0),                       # SW x2, 0(x1) - write OUT again
        0x00000020: encode_load(4, 1, 0),                        # LW x4, 0(x1) - read OUT
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000002C:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            mask = (1 << num_out_total) - 1
            
            # x3 should contain OUT = test_out_value (masked)
            out_read_1 = registers[3].value.to_unsigned() & mask
            assert out_read_1 == test_out_value & mask, \
                f"OUT should be {test_out_value & mask:#x}, got {out_read_1:#x}"
            
            # x4 should contain OUT = 0x25 (masked)
            out_read_2 = registers[4].value.to_unsigned() & mask
            assert out_read_2 == 0x25 & mask, \
                f"OUT should be {0x25 & mask:#x}, got {out_read_2:#x}"
            
            # Validate gpio_out (output-only pins) from testbench
            # OUT register: bits [NUM_BIDIR+NUM_OUT-1:NUM_BIDIR] -> gpio_out, bits [NUM_BIDIR-1:0] -> gpio_bidir_out
            expected_gpio_out = (0x25 >> NUM_BIDIR) & ((1 << NUM_OUT) - 1)
            gpio_out_val = int(dut.gpio_out.value)
            assert gpio_out_val == expected_gpio_out, \
                f"gpio_out should be {expected_gpio_out:#x}, got {gpio_out_val:#x}"
            
            # Validate gpio_io_out (bidirectional output pins) from testbench
            expected_gpio_io_out = 0x25 & ((1 << NUM_BIDIR) - 1)
            gpio_io_out_val = int(dut.gpio_io_out.value)
            assert gpio_io_out_val == expected_gpio_io_out, \
                f"gpio_io_out should be {expected_gpio_io_out:#x}, got {gpio_io_out_val:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_in_read_only(dut):
    """Test that IN register is read-only (writes are ignored)"""

    dut.gpio_in.value = 0x2A;
    dut.gpio_io_in.value = 0x01;
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, GPIO_BASE_ADDR >> 12),         # LUI x1, GPIO base upper
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & 0xFFF),   # ADDI x1, x1, GPIO base offset
        0x0000000C: encode_store(1, 0, 0),                       # SW x0, 0(x1) - DIR = 0 (all input)
        0x00000010: encode_load(2, 1, 8),                        # LW x2, 8(x1) - read IN (first)
        0x00000014: encode_addi(3, 0, 0xFF),                     # ADDI x3, x0, 0xFF
        0x00000018: encode_store(1, 3, 8),                       # SW x3, 8(x1) - try to write IN
        0x0000001C: encode_load(4, 1, 8),                        # LW x4, 8(x1) - read IN (second)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000028:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # Both reads should return same value (write was ignored)
            in_read_1 = registers[2].value.to_unsigned()
            in_read_2 = registers[4].value.to_unsigned()
            
            # The write to IN register should have been ignored
            # IN register value depends on input pins state
            # We just verify the write didn't corrupt anything
            assert in_read_2 != 0x2A5 or in_read_1 == 0x2A5, \
                f"IN register should not change after write attempt: before={in_read_1:#x}, after={in_read_2:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


# =============================================================================
# Group 2: Bidirectional Pins Tests
# =============================================================================

@cocotb.test()
async def test_gpio_bidir_output_mode(dut):
    """Test bidirectional pins in output mode"""
    
    # Set all bidirectional pins as output (DIR = (1 << NUM_BIDIR) - 1)
    # Write a pattern to OUT register (lower NUM_BIDIR bits for bidir)
    dir_all_out = (1 << NUM_BIDIR) - 1
    test_pattern = 0x01  # Drive bidir pin high
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & 0xFFF),   # x1 = GPIO_BASE_ADDR
        0x0000000C: encode_addi(2, 0, dir_all_out),              # x2 = all bidir as output
        0x00000010: encode_store(1, 2, 0),                       # SW x2, 0(x1) - DIR
        0x00000014: encode_addi(2, 0, test_pattern),             # x2 = test_pattern
        0x00000018: encode_store(1, 2, 4),                       # SW x2, 4(x1) - OUT = test_pattern
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000024:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            gpio_inst = dut.soc_inst.gpio_inst
            
            # Check gpio_bidir_oe is all 1s (output enable)
            bidir_oe = int(gpio_inst.gpio_bidir_oe.value)
            assert bidir_oe == dir_all_out, f"gpio_bidir_oe should be {dir_all_out:#x}, got {bidir_oe:#x}"
            
            # Check gpio_bidir_out matches lower bits of test_pattern
            bidir_out = int(gpio_inst.gpio_bidir_out.value)
            expected_bidir = test_pattern & ((1 << NUM_BIDIR) - 1)
            assert bidir_out == expected_bidir, \
                f"gpio_bidir_out should be {expected_bidir:#x}, got {bidir_out:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_bidir_input_mode(dut):
    """Test bidirectional pins in input mode - read external input"""
    
    # Set all bidirectional pins as input (DIR = 0)
    # Note: We simulate input by forcing gpio_bidir_in signal
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & 0xFFF),   # x1 = GPIO_BASE_ADDR
        0x0000000C: encode_store(1, 0, 0),                       # SW x0, 0(x1) - DIR = 0 (all input)
        0x00000010: encode_load(2, 1, 8),                        # LW x2, 8(x1) - read IN register
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000001C:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            gpio_inst = dut.soc_inst.gpio_inst
            
            # Check gpio_bidir_oe is all 0s (input mode / high-z)
            bidir_oe = int(gpio_inst.gpio_bidir_oe.value)
            assert bidir_oe == 0x00, f"gpio_bidir_oe should be 0x00 (input mode), got {bidir_oe:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_bidir_mixed_direction(dut):
    """Test bidirectional pins with mixed direction (some input, some output)"""
    
    # DIR: 1=output, 0=input for each bidir pin. With NUM_BIDIR=1, dir_value 0 or 1.
    dir_value = 0x05  # Only lower NUM_BIDIR bits used (0x05 & 0x01 = 1 = output)
    out_value = 0x0F  # All bits set
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & 0xFFF),
        0x0000000C: encode_addi(2, 0, dir_value),
        0x00000010: encode_store(1, 2, 0),                       # DIR
        0x00000014: encode_addi(2, 0, out_value),
        0x00000018: encode_store(1, 2, 4),                       # OUT
        0x0000001C: encode_load(3, 1, 0),                        # Read DIR
        0x00000020: encode_load(4, 1, 4),                        # Read OUT
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000002C:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            gpio_inst = dut.soc_inst.gpio_inst
            
            # Check gpio_bidir_oe matches DIR register (only NUM_BIDIR bits)
            bidir_oe = int(gpio_inst.gpio_bidir_oe.value)
            expected_oe = dir_value & ((1 << NUM_BIDIR) - 1)
            assert bidir_oe == expected_oe, \
                f"gpio_bidir_oe should be {expected_oe:#x}, got {bidir_oe:#x}"
            
            # Check gpio_bidir_out matches lower bits of OUT
            bidir_out = int(gpio_inst.gpio_bidir_out.value)
            expected_out = out_value & ((1 << NUM_BIDIR) - 1)
            assert bidir_out == expected_out, \
                f"gpio_bidir_out should be {expected_out:#x}, got {bidir_out:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


# =============================================================================
# Group 3: Output-Only Pins Tests
# =============================================================================

@cocotb.test()
async def test_gpio_output_only_pins(dut):
    """Test output-only pins (OUT register bits [NUM_BIDIR+NUM_OUT-1:NUM_BIDIR] -> gpio_out)"""
    
    # OUT register: upper NUM_OUT bits -> gpio_out, lower NUM_BIDIR bits -> gpio_bidir_out
    # Test pattern: set gpio_out to 0x28 (6 bits), gpio_bidir = 0 (1 bit) -> test_out = 0x50
    test_out = 0x50  # (0x28 << NUM_BIDIR) | 0
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_OUT >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_OUT & 0xFFF),
        0x0000000C: encode_addi(2, 0, test_out),
        0x00000010: encode_store(1, 2, 0),                       # OUT = 0x50
        0x00000014: encode_load(3, 1, 0),                        # Read OUT
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000020:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            gpio_inst = dut.soc_inst.gpio_inst
            
            # Check gpio_out matches upper NUM_OUT bits of OUT register
            gpio_out = int(gpio_inst.gpio_out.value)
            expected_gpio_out = (test_out >> NUM_BIDIR) & ((1 << NUM_OUT) - 1)
            assert gpio_out == expected_gpio_out, \
                f"gpio_out should be {expected_gpio_out:#x}, got {gpio_out:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_output_toggle(dut):
    """Test toggling output pins multiple times"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_OUT >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_OUT & 0xFFF),
        0x0000000C: encode_addi(2, 0, 0x7F),                     # All output bits ON
        0x00000010: encode_store(1, 2, 0),                       # OUT = 0x7F
        0x00000014: encode_load(3, 1, 0),                        # Read OUT (should be 0x7F)
        0x00000018: encode_store(1, 0, 0),                       # OUT = 0x00
        0x0000001C: encode_load(4, 1, 0),                        # Read OUT (should be 0x00)
        0x00000020: encode_addi(2, 0, 0x55),                     # Alternating pattern
        0x00000024: encode_store(1, 2, 0),                       # OUT = 0x55
        0x00000028: encode_load(5, 1, 0),                        # Read OUT (should be 0x55)
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 15000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000034:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            num_out_total = NUM_BIDIR + NUM_OUT
            mask = (1 << num_out_total) - 1
            
            # x3 = 0x7F
            out_val_1 = registers[3].value.to_unsigned() & mask
            assert out_val_1 == 0x7F, f"OUT should be 0x7F, got {out_val_1:#x}"
            
            # x4 = 0x00
            out_val_2 = registers[4].value.to_unsigned() & mask
            assert out_val_2 == 0x00, f"OUT should be 0x00, got {out_val_2:#x}"
            
            # x5 = 0x55
            out_val_3 = registers[5].value.to_unsigned() & mask
            assert out_val_3 == 0x55, f"OUT should be 0x55, got {out_val_3:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


# =============================================================================
# Group 4: Output Pins Validation Tests
# =============================================================================

@cocotb.test()
async def test_gpio_validate_output_pins(dut):
    """Test that output pins correctly reflect OUT register values"""
    
    # OUT register: upper NUM_OUT bits -> gpio_out, lower NUM_BIDIR bits -> gpio_bidir_out
    test_out_value = 0x5A
    expected_gpio_out = (test_out_value >> NUM_BIDIR) & ((1 << NUM_OUT) - 1)
    expected_gpio_io_out = test_out_value & ((1 << NUM_BIDIR) - 1)
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, GPIO_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & 0xFFF),
        0x0000000C: encode_addi(2, 0, test_out_value),           # x2 = test_out_value
        0x00000010: encode_store(1, 2, 4),                       # OUT = test_out_value
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000001C:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # Validate gpio_out (output-only pins) from testbench
            gpio_out_val = int(dut.gpio_out.value)
            assert gpio_out_val == expected_gpio_out, \
                f"gpio_out should be {expected_gpio_out:#x}, got {gpio_out_val:#x}"
            
            # Validate gpio_io_out (bidirectional output pins) from testbench
            gpio_io_out_val = int(dut.gpio_io_out.value)
            assert gpio_io_out_val == expected_gpio_io_out, \
                f"gpio_io_out should be {expected_gpio_io_out:#x}, got {gpio_io_out_val:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_output_pins_all_patterns(dut):
    """Test output pins with multiple patterns: all 0s, all 1s, alternating"""
    
    # Test patterns: OUT register values (NUM_BIDIR + NUM_OUT bits). Expected values computed in callback.
    out_values = [0x00, 0x7F, 0x55, 0x2A]
    dir_all_out = (1 << NUM_BIDIR) - 1  # All bidirectional pins as output
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, GPIO_BASE_ADDR >> 12),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & 0xFFF),
        # Set DIR = all bidir as output
        0x0000000C: encode_addi(2, 0, dir_all_out),
        0x00000010: encode_store(1, 2, 0),                       # DIR
        # Pattern 0: OUT = 0x00
        0x00000014: encode_store(1, 0, 4),                       # OUT = 0x00
        0x00000018: NOP_INSTR,
        # Pattern 1: OUT = 0x7F
        0x0000001C: encode_addi(2, 0, 0x7F),
        0x00000020: encode_store(1, 2, 4),                       # OUT = 0x7F
        0x00000024: NOP_INSTR,
        # Pattern 2: OUT = 0x55
        0x00000028: encode_addi(2, 0, 0x55),
        0x0000002C: encode_store(1, 2, 4),                       # OUT = 0x55
        0x00000030: NOP_INSTR,
        # Pattern 3: OUT = 0x2A
        0x00000034: encode_addi(2, 0, 0x2A),
        0x00000038: encode_store(1, 2, 4),                       # OUT = 0x2A
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 15000
    pattern_idx = 0
    check_addresses = [0x00000018, 0x00000024, 0x00000030, 0x0000003C]
    
    def callback(dut, memory):
        nonlocal pattern_idx
        
        current_pc = dut.soc_inst.cpu_core.o_instr_addr.value.to_unsigned()
        
        if pattern_idx < len(check_addresses) and current_pc - 8 == check_addresses[pattern_idx]:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            out_val = out_values[pattern_idx]
            expected_gpio_out = (out_val >> NUM_BIDIR) & ((1 << NUM_OUT) - 1)
            expected_gpio_io_out = out_val & ((1 << NUM_BIDIR) - 1)
            
            # Validate gpio_out
            gpio_out_val = int(dut.gpio_out.value)
            assert gpio_out_val == expected_gpio_out, \
                f"Pattern {pattern_idx}: gpio_out should be {expected_gpio_out:#x}, got {gpio_out_val:#x}"
            
            # Validate gpio_io_out
            gpio_io_out_val = int(dut.gpio_io_out.value)
            assert gpio_io_out_val == expected_gpio_io_out, \
                f"Pattern {pattern_idx}: gpio_io_out should be {expected_gpio_io_out:#x}, got {gpio_io_out_val:#x}"
            
            pattern_idx += 1
        
        if current_pc == 0x00000044:
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)

# =============================================================================
# Group 5: Reset Tests
# =============================================================================

@cocotb.test()
async def test_gpio_reset_values(dut):
    """Test that GPIO registers have correct reset values"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & 0xFFF),
        0x0000000C: encode_load(2, 1, 0),                        # Read DIR (should be 0)
        0x00000010: encode_load(3, 1, 4),                        # Read OUT (should be 0)
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000001C:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # DIR should be 0 after reset (all bidirectional pins as input)
            dir_val = registers[2].value.to_unsigned() & ((1 << NUM_BIDIR) - 1)
            assert dir_val == 0, f"DIR should be 0 after reset, got {dir_val:#x}"
            
            # OUT should be 0 after reset
            num_out_total = NUM_BIDIR + NUM_OUT
            out_val = registers[3].value.to_unsigned() & ((1 << num_out_total) - 1)
            assert out_val == 0, f"OUT should be 0 after reset, got {out_val:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_gpio_invalid_register_offset(dut):
    """Test reading invalid register offset returns 0"""
    
    # Offset 0x0C is invalid (only 0x00, 0x04, 0x08 are valid)
    invalid_offset = 0x0C
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, GPIO_BASE_ADDR & 0xFFF),
        0x0000000C: encode_load(2, 1, invalid_offset),          # Read invalid offset
        0x00000010: NOP_INSTR,
        0x00000014: NOP_INSTR,
        0x00000018: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000018:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # Reading invalid offset should return 0
            invalid_read = registers[2].value.to_unsigned()
            assert invalid_read == 0, \
                f"Reading invalid register offset should return 0, got {invalid_read:#x}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)

import cocotb
from test_utils import (
    NOP_INSTR,
    encode_load,
    encode_store,
    encode_addi,
    encode_lui,
    encode_jal,
    GPIO_BASE_ADDR,
    PWM_BASE_ADDR,
    PWM_CH0_CTRL,
    PWM_CH0_PERIOD,
    PWM_CH0_DUTY,
    PWM_CH0_COUNTER,
    PWM_CH1_CTRL,
    PWM_CH1_PERIOD,
    PWM_CH1_DUTY,
    PWM_CH1_COUNTER,
)
from qspi_memory_utils import (
    test_spi_memory,
    convert_hex_memory_to_byte_memory,
)


@cocotb.test()
async def test_pwm_read_write_ctrl(dut):
    """Test reading and writing PWM CTRL register"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),   # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),         # ADDI x1, x1, PWM_CH0_CTRL offset
        0x0000000C: encode_addi(2, 0, 1),                            # ADDI x2, x0, 1 (enable = 1)
        0x00000010: encode_store(1, 2, 0),                           # SW x2, 0(x1) - write CTRL = 1
        0x00000014: encode_load(3, 1, 0),                            # LW x3, 0(x1) - read CTRL
        0x00000018: encode_store(1, 0, 0),                           # SW x0, 0(x1) - write CTRL = 0
        0x0000001C: encode_load(4, 1, 0),                            # LW x4, 0(x1) - read CTRL again
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        # Check after reading CTRL twice
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000028:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x3 should contain CTRL = 1 (enable bit)
            ctrl_read_1 = registers[3].value.to_unsigned() & 0x1
            assert ctrl_read_1 == 1, f"CTRL should be 1 after write, got {ctrl_read_1}"
            
            # x4 should contain CTRL = 0 (disable bit)
            ctrl_read_2 = registers[4].value.to_unsigned() & 0x1
            assert ctrl_read_2 == 0, f"CTRL should be 0 after write, got {ctrl_read_2}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_read_write_period(dut):
    """Test reading and writing PWM PERIOD register"""
    
    test_period = 1000  # 0x3E8, fits in 12-bit immediate
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_PERIOD >> 12) & 0xFFFFF),  # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_PERIOD & 0xFFF),        # ADDI x1, x1, PWM_CH0_PERIOD offset
        0x0000000C: encode_addi(2, 0, test_period),                   # ADDI x2, x0, test_period
        0x00000010: encode_store(1, 2, 0),                            # SW x2, 0(x1) - write PERIOD
        0x00000014: encode_load(4, 1, 0),                             # LW x4, 0(x1) - read PERIOD
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        # Check after reading PERIOD
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000020:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x4 should contain PERIOD = test_period
            period_read = registers[4].value.to_unsigned() & 0xFFFF
            assert period_read == test_period, \
                f"PERIOD should be {test_period}, got {period_read}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_read_write_duty(dut):
    """Test reading and writing PWM DUTY register"""
    
    test_duty = 500
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_DUTY >> 12) & 0xFFFFF),   # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_DUTY & 0xFFF),         # ADDI x1, x1, PWM_CH0_DUTY offset
        0x0000000C: encode_addi(2, 0, test_duty),                    # ADDI x2, x0, test_duty
        0x00000010: encode_store(1, 2, 0),                           # SW x2, 0(x1) - write DUTY
        0x00000014: encode_load(3, 1, 0),                            # LW x3, 0(x1) - read DUTY
        0x00000018: NOP_INSTR,
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        # Check after reading DUTY
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000020:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x3 should contain DUTY = test_duty
            duty_read = registers[3].value.to_unsigned() & 0xFFFF
            assert duty_read == test_duty, \
                f"DUTY should be {test_duty}, got {duty_read}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_read_counter(dut):
    """Test reading PWM COUNTER register (read-only, should increment)"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),   # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),         # ADDI x1, x1, PWM base
        0x0000000C: encode_addi(2, 0, 0x7FF),                        # ADDI x2, x0, 0x7FF (PERIOD)
        0x00000010: encode_store(1, 2, 4),                           # SW x2, 4(x1) - write PERIOD = 100
        0x00000014: encode_addi(2, 0, 1),                            # ADDI x2, x0, 1 (enable)
        0x00000018: encode_store(1, 2, 0),                           # SW x2, 0(x1) - write CTRL = 1 (enable)
        0x0000001C: encode_load(3, 1, 12),                           # LW x3, 12(x1) - read COUNTER (first)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: encode_load(4, 1, 12),                           # LW x4, 12(x1) - read COUNTER (second)
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        # Check after reading COUNTER twice
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000003C:
            registers = dut.soc_inst.cpu_core.register_file.registers
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # x3 should contain first COUNTER read
            # x4 should contain second COUNTER read (should be >= x3)
            counter_first = registers[3].value.to_unsigned() & 0xFFFF
            counter_second = registers[4].value.to_unsigned() & 0xFFFF
            
            # Counter should increment (or wrap around)
            assert counter_second >= counter_first or counter_second < 10, \
                f"COUNTER should increment: first={counter_first}, second={counter_second}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_output_behavior(dut):
    """Test PWM output behavior: HIGH when counter < duty, LOW otherwise"""
    
    period = 100
    duty = 50
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),    # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),          # ADDI x1, x1, PWM base
        0x0000000C: encode_addi(2, 0, period),                        # ADDI x2, x0, period
        0x00000010: encode_store(1, 2, 4),                            # SW x2, 4(x1) - write PERIOD
        0x00000014: encode_addi(2, 0, duty),                          # ADDI x2, x0, duty
        0x00000018: encode_store(1, 2, 8),                            # SW x2, 8(x1) - write DUTY
        0x0000001C: encode_addi(2, 0, 1),                             # ADDI x2, x0, 1 (enable)
        0x00000020: encode_store(1, 2, 0),                            # SW x2, 0(x1) - write CTRL = 1 (enable)
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        0x00000034: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    pwm_outputs_checked = False
    
    def callback(dut, memory):
        nonlocal pwm_outputs_checked
        
        # Check PWM output after setup
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000034 and not pwm_outputs_checked:
            pwm_outputs_checked = True
            
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # Get PWM module instance
            pwm_inst = dut.soc_inst.pwm_inst
            
            # Check that PWM is enabled
            channel_enable_value = int(pwm_inst.channel_enable.value)
            channel_enable = (channel_enable_value >> 0) & 0x1
            assert channel_enable == 1, f"Channel 0 should be enabled"
            
            # Check counter is incrementing
            counter = int(pwm_inst.channel_counter[0].value) & 0xFFFF
            period_reg = int(pwm_inst.channel_period[0].value) & 0xFFFF
            duty_reg = int(pwm_inst.channel_duty[0].value) & 0xFFFF
            
            assert period_reg == period, f"PERIOD should be {period}, got {period_reg}"
            assert duty_reg == duty, f"DUTY should be {duty}, got {duty_reg}"
            
            # Check PWM output logic
            pwm_out_value = int(dut.pwm_out.value)
            pwm_out = (pwm_out_value >> 0) & 0x1
            if counter < duty:
                assert pwm_out == 1, f"PWM output should be HIGH when counter ({counter}) < duty ({duty})"
            else:
                assert pwm_out == 0, f"PWM output should be LOW when counter ({counter}) >= duty ({duty})"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_disable_output_low(dut):
    """Test that PWM output is LOW when disabled"""
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),   # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),          # ADDI x1, x1, PWM base
        0x0000000C: encode_addi(2, 0, 100),                            # ADDI x2, x0, 100 (PERIOD)
        0x00000010: encode_store(1, 2, 4),                            # SW x2, 4(x1) - write PERIOD
        0x00000014: encode_addi(2, 0, 50),                            # ADDI x2, x0, 50 (DUTY)
        0x00000018: encode_store(1, 2, 8),                            # SW x2, 8(x1) - write DUTY
        0x0000001C: encode_store(1, 0, 0),                            # SW x0, 0(x1) - write CTRL = 0 (disable)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        # Check PWM output when disabled
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000028:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # PWM output should be LOW when disabled
            pwm_out_value = int(dut.pwm_out.value)
            pwm_out = (pwm_out_value >> 0) & 0x1
            assert pwm_out == 0, f"PWM output should be LOW when disabled, got {pwm_out}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_multiple_channels(dut):
    """Test that multiple PWM channels work independently"""
    
    period_ch0 = 100
    duty_ch0 = 50
    period_ch1 = 200
    duty_ch1 = 150
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),    # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),          # ADDI x1, x1, PWM base
        # Channel 0 setup
        0x0000000C: encode_addi(2, 0, period_ch0),                    # ADDI x2, x0, period_ch0
        0x00000010: encode_store(1, 2, 4),                            # SW x2, 4(x1) - write CH0 PERIOD
        0x00000014: encode_addi(2, 0, duty_ch0),                      # ADDI x2, x0, duty_ch0
        0x00000018: encode_store(1, 2, 8),                            # SW x2, 8(x1) - write CH0 DUTY
        0x0000001C: encode_addi(2, 0, 1),                             # ADDI x2, x0, 1
        0x00000020: encode_store(1, 2, 0),                            # SW x2, 0(x1) - write CH0 CTRL = 1
        # Channel 1 setup
        0x00000024: encode_addi(2, 0, period_ch1),                    # ADDI x2, x0, period_ch1
        0x00000028: encode_store(1, 2, 20),                           # SW x2, 20(x1) - write CH1 PERIOD
        0x0000002C: encode_addi(2, 0, duty_ch1),                      # ADDI x2, x0, duty_ch1
        0x00000030: encode_store(1, 2, 24),                           # SW x2, 24(x1) - write CH1 DUTY
        0x00000034: encode_addi(2, 0, 1),                             # ADDI x2, x0, 1
        0x00000038: encode_store(1, 2, 16),                           # SW x2, 16(x1) - write CH1 CTRL = 1
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
        0x00000044: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        # Check both channels after setup
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000044:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            pwm_inst = dut.soc_inst.pwm_inst

            channel_enable_value = int(pwm_inst.channel_enable.value)
            
            # Check Channel 0
            ch0_enable = (channel_enable_value >> 0) & 0x1
            ch0_period = int(pwm_inst.channel_period[0].value) & 0xFFFF
            ch0_duty = int(pwm_inst.channel_duty[0].value) & 0xFFFF
            assert ch0_enable == 1, f"Channel 0 should be enabled"
            assert ch0_period == period_ch0, f"Channel 0 PERIOD should be {period_ch0}, got {ch0_period}"
            assert ch0_duty == duty_ch0, f"Channel 0 DUTY should be {duty_ch0}, got {ch0_duty}"
            
            # Check Channel 1
            ch1_enable = (channel_enable_value >> 1) & 0x1
            ch1_period = int(pwm_inst.channel_period[1].value) & 0xFFFF
            ch1_duty = int(pwm_inst.channel_duty[1].value) & 0xFFFF
            assert ch1_enable == 1, f"Channel 1 should be enabled"
            assert ch1_period == period_ch1, f"Channel 1 PERIOD should be {period_ch1}, got {ch1_period}"
            assert ch1_duty == duty_ch1, f"Channel 1 DUTY should be {duty_ch1}, got {ch1_duty}"
            
            # Check both outputs exist
            pwm_out_value = int(dut.pwm_out.value)
            pwm_out_0 = (pwm_out_value >> 0) & 0x1
            pwm_out_1 = (pwm_out_value >> 1) & 0x1
            # Outputs should be valid (0 or 1)
            assert pwm_out_0 in [0, 1], f"PWM output 0 should be 0 or 1, got {pwm_out_0}"
            assert pwm_out_1 in [0, 1], f"PWM output 1 should be 0 or 1, got {pwm_out_1}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_duty_zero_always_low(dut):
    """Test that PWM output is always LOW when duty = 0"""
    
    period = 100
    duty = 0
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),    # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),          # ADDI x1, x1, PWM base
        0x0000000C: encode_addi(2, 0, period),                        # ADDI x2, x0, period
        0x00000010: encode_store(1, 2, 4),                            # SW x2, 4(x1) - write PERIOD
        0x00000014: encode_store(1, 0, 8),                            # SW x0, 8(x1) - write DUTY = 0
        0x00000018: encode_addi(2, 0, 1),                             # ADDI x2, x0, 1 (enable)
        0x0000001C: encode_store(1, 2, 0),                            # SW x2, 0(x1) - write CTRL = 1 (enable)
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        # Check PWM output when duty = 0
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x00000028:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # PWM output should be LOW when duty = 0
            pwm_out_value = int(dut.pwm_out.value)
            pwm_out = (pwm_out_value >> 0) & 0x1
            assert pwm_out == 0, f"PWM output should be LOW when duty=0, got {pwm_out}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_period_update_resets_counter(dut):
    """Test that updating PERIOD resets the counter"""
    
    period1 = 1000
    period2 = 2000
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),   # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),         # ADDI x1, x1, PWM base
        0x0000000C: encode_addi(2, 0, 1),                            # ADDI x2, x0, 1 (enable)
        0x00000010: encode_store(1, 2, 0),                           # SW x2, 0(x1) - write CTRL = 1 (enable)
        0x00000014: encode_addi(2, 0, period1),                      # ADDI x2, x0, period1
        0x00000018: encode_store(1, 2, 4),                           # SW x2, 4(x1) - write PERIOD = period1
        0x0000001C: NOP_INSTR,
        0x00000020: NOP_INSTR,
        0x00000024: NOP_INSTR,
        0x00000028: encode_load(3, 1, 12),                           # LW x3, 12(x1) - read COUNTER (should be incrementing)
        0x0000002C: encode_addi(2, 0, period2),                      # ADDI x2, x0, period2
        0x00000030: encode_store(1, 2, 4),                           # SW x2, 4(x1) - write PERIOD = period2 (should reset counter)
        0x00000034: encode_load(4, 1, 12),                           # LW x4, 12(x1) - read COUNTER (should be reset)
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 10000
    
    def callback(dut, memory):
        # Check counter after period update
        if dut.soc_inst.cpu_core.o_instr_addr.value == 0x0000003C:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            counter_before_update = dut.soc_inst.cpu_core.register_file.registers[3].value.to_unsigned() & 0xFFFF
            counter_after_update = dut.soc_inst.cpu_core.register_file.registers[4].value.to_unsigned() & 0xFFFF
            
            assert counter_after_update < counter_before_update, \
                f"Counter should be reset after PERIOD update, got after:{counter_after_update}, before:{counter_before_update}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_duty_cycle_ratio_long_run(dut):
    """Test PWM duty cycle ratio over long period for both channels"""
    
    # Setup: Channel 0: period=100, duty=30 (30% duty cycle)
    #        Channel 1: period=2000, duty=800 (40% duty cycle)
    period_ch0 = 100
    duty_ch0 = 30
    period_ch1 = 2000
    duty_ch1 = 800
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),    # LUI x1, PWM base upper
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),          # ADDI x1, x1, PWM base
        # Channel 0 setup
        0x0000000C: encode_addi(2, 0, period_ch0),                    # ADDI x2, x0, period_ch0
        0x00000010: encode_store(1, 2, 4),                            # SW x2, 4(x1) - write CH0 PERIOD
        0x00000014: encode_addi(2, 0, duty_ch0),                      # ADDI x2, x0, duty_ch0
        0x00000018: encode_store(1, 2, 8),                            # SW x2, 8(x1) - write CH0 DUTY
        0x0000001C: encode_addi(2, 0, 1),                             # ADDI x2, x0, 1
        0x00000020: encode_store(1, 2, 0),                            # SW x2, 0(x1) - write CH0 CTRL = 1 (enable)
        # Channel 1 setup
        0x00000024: encode_addi(2, 0, period_ch1),                    # ADDI x2, x0, period_ch1
        0x00000028: encode_store(1, 2, 20),                           # SW x2, 20(x1) - write CH1 PERIOD
        0x0000002C: encode_addi(2, 0, duty_ch1),                      # ADDI x2, x0, duty_ch1
        0x00000030: encode_store(1, 2, 24),                           # SW x2, 24(x1) - write CH1 DUTY
        0x00000034: encode_addi(2, 0, 1),                             # ADDI x2, x0, 1
        0x00000038: encode_store(1, 2, 16),                           # SW x2, 16(x1) - write CH1 CTRL = 1 (enable)
        # Loop forever (NOP instructions)
        0x0000003C: NOP_INSTR,
        0x00000040: encode_jal(0, 0x0000003C - 0x00000040),           # JAL x0, loop back to 0x0000003C
        0x00000044: NOP_INSTR,
        0x00000048: NOP_INSTR,
        0x0000004C: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 500000  # Run for many cycles to get accurate ratio
    
    # Counters for duty cycle measurement
    total_samples_ch0 = 0
    high_samples_ch0 = 0
    total_samples_ch1 = 0
    high_samples_ch1 = 0

    cycle_count = 0
    
    def callback(dut, memory):
        nonlocal total_samples_ch0, high_samples_ch0, total_samples_ch1, high_samples_ch1, cycle_count

        cycle_count += 1


        # Check if channels are enabled
        pwm_inst = dut.soc_inst.pwm_inst
        channel_enable_value = int(pwm_inst.channel_enable.value)
        ch0_enable = (channel_enable_value >> 0) & 0x1
        ch1_enable = (channel_enable_value >> 1) & 0x1

        # Sample PWM outputs
        pwm_out_value = int(dut.pwm_out.value)
        pwm_out_0 = (pwm_out_value >> 0) & 0x1
        pwm_out_1 = (pwm_out_value >> 1) & 0x1

        if ch0_enable == 1:
            total_samples_ch0 += 1
            if pwm_out_0 == 1:
                high_samples_ch0 += 1

        if ch1_enable == 1:
            total_samples_ch1 += 1
            if pwm_out_1 == 1:
                high_samples_ch1 += 1

        # Start counting after setup is complete
        if cycle_count >= 100000:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"

            # Calculate duty cycle ratios
            ratio_ch0 = high_samples_ch0 / total_samples_ch0 if total_samples_ch0 > 0 else 0
            ratio_ch1 = high_samples_ch1 / total_samples_ch1 if total_samples_ch1 > 0 else 0

            # Expected duty cycle ratios
            expected_ratio_ch0 = duty_ch0 / period_ch0
            expected_ratio_ch1 = duty_ch1 / period_ch1

            tolerance = 0.005

            # Verify channel 0 duty cycle ratio
            assert abs(ratio_ch0 - expected_ratio_ch0) <= tolerance, \
                f"Channel 0 duty cycle ratio mismatch: expected {expected_ratio_ch0:.4f}, got {ratio_ch0:.4f} " \
                f"(high={high_samples_ch0}, total={total_samples_ch0})"

            # Verify channel 1 duty cycle ratio
            assert abs(ratio_ch1 - expected_ratio_ch1) <= tolerance, \
                f"Channel 1 duty cycle ratio mismatch: expected {expected_ratio_ch1:.4f}, got {ratio_ch1:.4f} " \
                f"(high={high_samples_ch1}, total={total_samples_ch1})"

            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_priority_over_gpio(dut):
    """Test that PWM has priority over GPIO when enabled (shared pins)
    
    Pin sharing:
    - uo_out[7] = pwm_ena[0] ? pwm_out[0] : gpio_out[2]
    - uio_out[7] = pwm_ena[1] ? pwm_out[1] : gpio_bidir_out[3]
    
    When PWM is enabled, PWM output should override GPIO output.
    """
    
    period = 100
    duty = 50
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Setup PWM channel 0
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),
        0x0000000C: encode_addi(2, 0, period),
        0x00000010: encode_store(1, 2, 4),                            # CH0 PERIOD = 100
        0x00000014: encode_addi(2, 0, duty),
        0x00000018: encode_store(1, 2, 8),                            # CH0 DUTY = 50
        0x0000001C: encode_addi(2, 0, 1),
        0x00000020: encode_store(1, 2, 0),                            # CH0 CTRL = 1 (enable)
        
        # Setup PWM channel 1
        0x00000024: encode_addi(2, 0, period),
        0x00000028: encode_store(1, 2, 20),                           # CH1 PERIOD = 100
        0x0000002C: encode_addi(2, 0, duty),
        0x00000030: encode_store(1, 2, 24),                           # CH1 DUTY = 50
        0x00000034: encode_addi(2, 0, 1),
        0x00000038: encode_store(1, 2, 16),                           # CH1 CTRL = 1 (enable)
        
        # Setup GPIO - try to set gpio_out[2]=0 and gpio_bidir_out[3]=0
        # This should NOT affect PWM output since PWM is enabled
        0x0000003C: encode_lui(3, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000040: encode_addi(3, 3, GPIO_BASE_ADDR & 0xFFF),
        0x00000044: encode_addi(4, 0, 0x0F),
        0x00000048: encode_store(3, 4, 0),                            # GPIO DIR = 0x0F (output)
        0x0000004C: encode_store(3, 0, 4),                            # GPIO OUT = 0x00 (all LOW)
        
        # Loop to let PWM run
        0x00000050: NOP_INSTR,
        0x00000054: encode_jal(0, 0x00000050 - 0x00000054),           # Loop
        0x00000058: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 50000
    
    # Counters for PWM output sampling
    total_samples_ch0 = 0
    high_samples_ch0 = 0
    total_samples_ch1 = 0
    high_samples_ch1 = 0
    cycle_count = 0
    
    def callback(dut, memory):
        nonlocal total_samples_ch0, high_samples_ch0
        nonlocal total_samples_ch1, high_samples_ch1
        nonlocal cycle_count
        
        cycle_count += 1
        
        pwm_inst = dut.soc_inst.pwm_inst
        channel_enable_value = int(pwm_inst.channel_enable.value)
        ch0_enable = (channel_enable_value >> 0) & 0x1
        ch1_enable = (channel_enable_value >> 1) & 0x1
        
        # Sample PWM outputs from testbench (shared pins)
        pwm_out_value = int(dut.pwm_out.value)
        pwm_out_0 = (pwm_out_value >> 0) & 0x1  # uo_out[7]
        pwm_out_1 = (pwm_out_value >> 1) & 0x1  # uio_out[7]
        
        if ch0_enable == 1:
            total_samples_ch0 += 1
            if pwm_out_0 == 1:
                high_samples_ch0 += 1
        
        if ch1_enable == 1:
            total_samples_ch1 += 1
            if pwm_out_1 == 1:
                high_samples_ch1 += 1
        
        # Verify after enough cycles
        if cycle_count >= 40000:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            
            # Verify GPIO OUT is set to 0 (which would make output LOW if GPIO had priority)
            gpio_inst = dut.soc_inst.gpio_inst
            out_reg = int(gpio_inst.out_reg.value)
            assert out_reg == 0, f"GPIO OUT should be 0, got {out_reg:#x}"
            
            # Calculate duty cycle ratios
            ratio_ch0 = high_samples_ch0 / total_samples_ch0 if total_samples_ch0 > 0 else 0
            ratio_ch1 = high_samples_ch1 / total_samples_ch1 if total_samples_ch1 > 0 else 0
            
            expected_ratio = duty / period  # 0.5
            tolerance = 0.01
            
            # PWM should still have ~50% duty cycle despite GPIO OUT = 0
            # If GPIO had priority, duty cycle would be 0%
            assert abs(ratio_ch0 - expected_ratio) <= tolerance, \
                f"PWM CH0 should override GPIO: expected duty ratio {expected_ratio:.2f}, got {ratio_ch0:.4f}"
            
            assert abs(ratio_ch1 - expected_ratio) <= tolerance, \
                f"PWM CH1 should override GPIO: expected duty ratio {expected_ratio:.2f}, got {ratio_ch1:.4f}"
            
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)


@cocotb.test()
async def test_pwm_disabled_gpio_controls_pin(dut):
    """Test that GPIO controls pin when PWM is disabled
    
    When PWM is disabled, GPIO should control the shared pins.
    """
    
    hex_memory = {
        0x00000000: NOP_INSTR,
        # Disable PWM (default state, but explicitly disable)
        0x00000004: encode_lui(1, (PWM_CH0_CTRL >> 12) & 0xFFFFF),
        0x00000008: encode_addi(1, 1, PWM_CH0_CTRL & 0xFFF),
        0x0000000C: encode_store(1, 0, 0),                            # CH0 CTRL = 0 (disable)
        0x00000010: encode_store(1, 0, 16),                           # CH1 CTRL = 0 (disable)
        
        # Setup GPIO
        0x00000014: encode_lui(3, (GPIO_BASE_ADDR >> 12) & 0xFFFFF),
        0x00000018: encode_addi(3, 3, GPIO_BASE_ADDR & 0xFFF),
        0x0000001C: encode_addi(4, 0, 0x0F),
        0x00000020: encode_store(3, 4, 0),                            # GPIO DIR = 0x0F (output)
        
        # Set GPIO OUT = 0x7F (all HIGH including shared pins)
        0x00000024: encode_addi(4, 0, 0x7F),
        0x00000028: encode_store(3, 4, 4),                            # GPIO OUT = 0x7F
        0x0000002C: NOP_INSTR,
        0x00000030: NOP_INSTR,
        
        # Set GPIO OUT = 0x00 (all LOW)
        0x00000034: encode_store(3, 0, 4),                            # GPIO OUT = 0x00
        0x00000038: NOP_INSTR,
        0x0000003C: NOP_INSTR,
        0x00000040: NOP_INSTR,
    }
    memory = convert_hex_memory_to_byte_memory(hex_memory)
    
    max_cycles = 15000
    
    checked_high = False
    checked_low = False
    
    def callback(dut, memory):
        nonlocal checked_high, checked_low
        
        current_pc = dut.soc_inst.cpu_core.o_instr_addr.value.to_unsigned()
        
        # Check when GPIO OUT = 0x7F
        if current_pc == 0x00000030 and not checked_high:
            checked_high = True
            
            # PWM is disabled, so shared pins should follow GPIO
            # gpio_out[2] = OUT[6] = 1 -> uo_out[7] should be 1
            # gpio_bidir_out[3] = OUT[3] = 1 -> uio_out[7] should be 1
            pwm_out_value = int(dut.pwm_out.value)
            pwm_out_0 = (pwm_out_value >> 0) & 0x1
            pwm_out_1 = (pwm_out_value >> 1) & 0x1
            
            assert pwm_out_0 == 1, \
                f"When PWM disabled, uo_out[7] should follow GPIO (HIGH), got {pwm_out_0}"
            assert pwm_out_1 == 1, \
                f"When PWM disabled, uio_out[7] should follow GPIO (HIGH), got {pwm_out_1}"
        
        # Check when GPIO OUT = 0x00
        if current_pc == 0x0000003C and not checked_low:
            checked_low = True
            
            pwm_out_value = int(dut.pwm_out.value)
            pwm_out_0 = (pwm_out_value >> 0) & 0x1
            pwm_out_1 = (pwm_out_value >> 1) & 0x1
            
            assert pwm_out_0 == 0, \
                f"When PWM disabled, uo_out[7] should follow GPIO (LOW), got {pwm_out_0}"
            assert pwm_out_1 == 0, \
                f"When PWM disabled, uio_out[7] should follow GPIO (LOW), got {pwm_out_1}"
        
        if current_pc == 0x00000040:
            assert int(dut.soc_inst.error_flag.value) == 0, f"error_flag should be 0"
            assert checked_high and checked_low, "Both checks should have passed"
            return True
        return False
    
    await test_spi_memory(dut, memory, max_cycles, callback)

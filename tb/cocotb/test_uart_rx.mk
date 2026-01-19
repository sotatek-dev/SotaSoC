# Makefile

# Include common configuration
include $(dir $(lastword $(MAKEFILE_LIST)))Makefile.inc

# Remove timer and PWM sources for this test (not needed)
VERILOG_SOURCES := $(filter-out $(PROJECT_ROOT)/rtl/peri/timer/mtime_timer.v,$(VERILOG_SOURCES))
VERILOG_SOURCES := $(filter-out $(PROJECT_ROOT)/rtl/peri/pwm/pwm.v,$(VERILOG_SOURCES))

# MODULE is the basename of the Python test file
MODULE = test_uart_rx

# Set a unique build directory for this test
SIM_BUILD = sim_build_spi_mem

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

# Makefile for RV32E Core Tests

# Defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Additional Verilog files
VERILOG_SOURCES += $(PWD)/rtl/rv32e_core.v
VERILOG_SOURCES += $(PWD)/rtl/rv32e_alu.v
VERILOG_SOURCES += $(PWD)/rtl/rv32e_register.v 
VERILOG_SOURCES += $(PWD)/tb/cocotb/test_rv32e_core_tb.v

# Top level module
TOPLEVEL = test_rv32e_core_tb

# Set Python path to find the test module
export PYTHONPATH := $(PWD)/tb/cocotb:$(PYTHONPATH)

# Module name
MODULE = test_rv32e_core

# Set a unique build directory for this test
SIM_BUILD = sim_build_core

# Include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

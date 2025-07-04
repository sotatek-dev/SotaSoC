# Makefile for RV32I Core Tests

# Defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Additional Verilog files
VERILOG_SOURCES += $(PWD)/rtl/rv32i_core.sv
VERILOG_SOURCES += $(PWD)/rtl/rv32i_alu.v
VERILOG_SOURCES += $(PWD)/rtl/rv32i_register.v 
VERILOG_SOURCES += $(PWD)/tb/cocotb/test_rv32i_core_tb.sv

COMPILE_ARGS += -g2012 

# Top level module
TOPLEVEL = test_rv32i_core_tb

# Set Python path to find the test module
export PYTHONPATH := $(PWD)/tb/cocotb:$(PYTHONPATH)

# Module name
MODULE = test_rv32i_core_jump

# Set a unique build directory for this test
SIM_BUILD = sim_build_core_jump

# Include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

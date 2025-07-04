# Makefile for RV32I Register File Tests

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/rtl/rv32i_register.v
VERILOG_SOURCES += $(PWD)/tb/cocotb/test_rv32i_register_tb.v

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = test_rv32i_register_tb

# MODULE is the basename of the Python test file
MODULE = test_rv32i_register

# Set Python path to find the test module
export PYTHONPATH := $(PWD)/tb/cocotb:$(PYTHONPATH)

# Set a unique build directory for this test
SIM_BUILD = sim_build_register

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

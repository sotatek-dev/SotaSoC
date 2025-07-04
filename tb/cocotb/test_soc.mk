# Makefile

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/rtl/rv32i_core.sv
VERILOG_SOURCES += $(PWD)/rtl/rv32i_alu.v
VERILOG_SOURCES += $(PWD)/rtl/rv32i_register.v 
VERILOG_SOURCES += $(PWD)/rtl/test_mem_ctl.v
VERILOG_SOURCES += $(PWD)/rtl/soc.v
VERILOG_SOURCES += $(PWD)/tb/cocotb/test_soc_tb.sv

COMPILE_ARGS += -g2012 

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = test_soc_tb

# MODULE is the basename of the Python test file
MODULE = test_soc

# Set Python path to find the test module
export PYTHONPATH := $(PWD)/tb/cocotb:$(PYTHONPATH)

# Set a unique build directory for this test
SIM_BUILD = sim_build_alu

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

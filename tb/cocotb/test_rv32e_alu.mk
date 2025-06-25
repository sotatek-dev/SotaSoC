# Makefile

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/rtl/rv32e_alu.v
VERILOG_SOURCES += $(PWD)/tb/cocotb/test_rv32e_alu_tb.v

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = test_rv32e_alu_tb

# MODULE is the basename of the Python test file
MODULE = test_rv32e_alu

# Set Python path to find the test module
export PYTHONPATH := $(PWD)/tb/cocotb:$(PYTHONPATH)

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

# Additional targets for Verilog testing
test-verilog:
	@echo "Building and running Verilog testbench..."
	iverilog -o sim_build/verilog_test.vvp $(PWD)/rtl/rv32e_alu.v $(PWD)/tb/tb_rv32e_alu.v
	vvp sim_build/verilog_test.vvp

wave-verilog: test-verilog
	@echo "Opening waveform viewer..."
	gtkwave rv32e_alu.vcd

.PHONY: test-verilog wave-verilog 
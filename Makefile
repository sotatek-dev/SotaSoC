# Makefile


# Additional targets for Verilog testing
test-verilog:
	@echo "Building and running Verilog testbench..."
	iverilog -o sim_build/verilog_test.vvp $(PWD)/rtl/rv32e_alu.v $(PWD)/tb/tb_rv32e_alu.v
	vvp sim_build/verilog_test.vvp

wave-verilog: test-verilog
	@echo "Opening waveform viewer..."
	gtkwave rv32e_alu.vcd

.PHONY: test-verilog wave-verilog 
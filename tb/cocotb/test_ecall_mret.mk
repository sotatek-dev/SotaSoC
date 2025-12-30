# Makefile for ECALL and MRET instruction tests

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/rtl/rv32i_core.sv
VERILOG_SOURCES += $(PWD)/rtl/rv32i_alu.v
VERILOG_SOURCES += $(PWD)/rtl/rv32i_register.v
VERILOG_SOURCES += $(PWD)/rtl/rv32i_csr.v
VERILOG_SOURCES += $(PWD)/rtl/mem_ctl.v
VERILOG_SOURCES += $(PWD)/rtl/soc.v
VERILOG_SOURCES += $(PWD)/rtl/peri/spi/spi_master.v
VERILOG_SOURCES += $(PWD)/rtl/peri/uart/uart_ctl.v
VERILOG_SOURCES += $(PWD)/rtl/peri/uart/uart_tx.v
VERILOG_SOURCES += $(PWD)/rtl/peri/uart/uart_rx.v
VERILOG_SOURCES += $(PWD)/tb/cocotb/test_soc_tb.sv

COMPILE_ARGS += -g2012 -I$(PWD)/rtl -DSIMULATION

# Pass HEX_FILE parameter to simulation if provided
ifdef HEX_FILE
    export HEX_FILE
endif

ifdef CLK_HZ
    COMPILE_ARGS += -DCLK_HZ=$(CLK_HZ)
endif

ifdef FLASH_SIZE
    FLASH_SIZE_DEC := $(shell printf "%d" $(FLASH_SIZE))
    COMPILE_ARGS += -DFLASH_SIZE=$(FLASH_SIZE_DEC)
endif

ifdef PSRAM_SIZE
    PSRAM_SIZE_DEC := $(shell printf "%d" $(PSRAM_SIZE))
    COMPILE_ARGS += -DPSRAM_SIZE=$(PSRAM_SIZE_DEC)
endif

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = test_soc_tb

# MODULE is the basename of the Python test file
MODULE = test_ecall_mret

# Set Python path to find the test module
export PYTHONPATH := $(PWD)/tb/cocotb:$(PYTHONPATH)

# Set a unique build directory for this test
SIM_BUILD = sim_build_ecall_mret

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim


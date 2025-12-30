# Makefile for RISCOF signature extraction test
# Based on test_spi_mem.mk

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

PROJECT_ROOT ?= $(PWD)

VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/rv32i_core.sv
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/rv32i_alu.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/rv32i_register.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/rv32i_csr.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/mem_ctl.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/soc.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/spi/spi_master.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/uart/uart_ctl.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/uart/uart_tx.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/uart/uart_rx.v
VERILOG_SOURCES += $(PROJECT_ROOT)/tb/cocotb/test_soc_tb.sv

COMPILE_ARGS += -g2012 -I$(PROJECT_ROOT)/rtl -DSIMULATION

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
MODULE = test_riscof_signature

# Set Python path to find the test module
export PYTHONPATH := $(dir $(abspath $(lastword $(MAKEFILE_LIST)))):$(PYTHONPATH)

# Set a unique build directory for this test
SIM_BUILD = sim_build_riscof_signature

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim


# Common Makefile configuration for cocotb tests

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

PROJECT_ROOT ?= $(PWD)

# Common Verilog sources for SOC tests
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/rv32i_core.sv
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/rv32i_alu.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/rv32i_register.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/rv32i_csr.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/mem_ctl.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/soc.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/spi/qspi_master.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/uart/uart_ctl.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/uart/uart_tx.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/uart/uart_rx.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/timer/mtime_timer.v
VERILOG_SOURCES += $(PROJECT_ROOT)/rtl/peri/pwm/pwm.v
VERILOG_SOURCES += $(PROJECT_ROOT)/tb/cocotb/test_soc_tb.sv

COMPILE_ARGS += -g2012 -I$(PROJECT_ROOT)/rtl -DSIMULATION

# Pass BIN_FILE parameter to simulation if provided
ifdef BIN_FILE
    export BIN_FILE
endif

# Pass HEX_FILE parameter to simulation if provided
ifdef HEX_FILE
    export HEX_FILE
endif

ifdef FLASH_BASE_ADDR
    FLASH_BASE_ADDR_DEC := $(shell printf "%d" $(FLASH_BASE_ADDR))
    COMPILE_ARGS += -DFLASH_BASE_ADDR=$(FLASH_BASE_ADDR_DEC)
endif

ifdef PSRAM_BASE_ADDR
    PSRAM_BASE_ADDR_DEC := $(shell printf "%d" $(PSRAM_BASE_ADDR))
    COMPILE_ARGS += -DPSRAM_BASE_ADDR=$(PSRAM_BASE_ADDR_DEC)
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

# Set Python path to find the test module
export PYTHONPATH := $(PROJECT_ROOT)/tb/cocotb:$(PYTHONPATH)


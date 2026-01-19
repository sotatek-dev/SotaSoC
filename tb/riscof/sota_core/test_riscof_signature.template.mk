# Makefile for RISCOF signature extraction test
# Based on test_spi_mem.mk

PROJECT_ROOT ?= $(PWD)
# Include common configuration from cocotb directory
include $(PROJECT_ROOT)/tb/cocotb/Makefile.inc

# MODULE is the basename of the Python test file
MODULE = test_riscof_signature

# Set Python path to find the test module
export PYTHONPATH := $(dir $(abspath $(lastword $(MAKEFILE_LIST)))):$(PYTHONPATH)

# Set a unique build directory for this test
SIM_BUILD = sim_build_riscof_signature

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim


# Makefile

# Include common configuration
include $(dir $(lastword $(MAKEFILE_LIST)))Makefile.inc

# MODULE is the basename of the Python test file
MODULE = test_csr

# Set a unique build directory for this test
SIM_BUILD = sim_build_csr

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim


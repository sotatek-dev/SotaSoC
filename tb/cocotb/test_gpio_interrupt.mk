# Makefile for GPIO interrupt tests

include $(dir $(lastword $(MAKEFILE_LIST)))Makefile.inc

MODULE = test_gpio_interrupt
SIM_BUILD = sim_build_gpio_interrupt

include $(shell cocotb-config --makefiles)/Makefile.sim

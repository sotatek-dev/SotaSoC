#!/usr/bin/env python3
"""
Basic test to verify cocotb is working
"""

import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_basic():
    """Basic test that doesn't require a DUT"""
    await Timer(1, unit='ns')
    assert True, "Basic test passed"

@cocotb.test()
async def test_basic_math():
    """Basic math test"""
    await Timer(1, unit='ns')
    result = 10 + 20
    assert result == 30, f"Math failed: {result} != 30" 
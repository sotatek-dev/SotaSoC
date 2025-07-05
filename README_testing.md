# RISC-V SoC Test Scripts

This directory contains bash scripts to automate testing of multiple hex files with the SoC testbench.

## Overview

The SoC testbench (`tb/cocotb/test_soc.py`) tests RISC-V programs by:
1. Loading a hex file into the processor memory
2. Running the processor simulation
3. Looking for an ECALL instruction (`0x00000073`)
4. Checking if register `x10` equals 0 after the ECALL
5. **PASS**: if `x10 == 0`, **FAIL**: if `x10 != 0`

## Available Scripts
### 1. `test_all_hex.sh` - Complete Test Script
Tests all hex files in the `tb/riscv-tests/hex/` directory.

**Usage:**
```bash
chmod +x test_all_hex.sh
./scripts/test_all_hex.sh
```

## How the Scripts Work

1. **Find hex files**: Scans `tb/riscv-tests/hex/` for `*.hex` files
2. **Run tests**: For each hex file, runs:
   ```bash
   make -f tb/cocotb/test_soc.mk HEX_FILE=<path_to_hex_file>
   ```
3. **Determine pass/fail**: Checks the output for:
   - `"test_soc passed"` → **PASS**
   - `"test_soc failed"` → **FAIL**
4. **Log results**: Saves detailed output to `test_logs/<test_name>.log`
5. **Extract errors**: For failed tests, shows the assertion error message

## Output Format

The scripts provide colored output:
- 🟢 **GREEN**: Passed tests
- 🔴 **RED**: Failed tests  
- 🟡 **YELLOW**: Unknown status
- **ERROR**: Make command failed

Example output:
```
==========================================
Running tests for all hex files...
==========================================
Found 42 hex files to test

Testing add.S... PASS
Testing and.S... FAIL
    Error: assert 00000000000000000000000000010011 == 0
Testing addi.S... PASS
Testing beq.S... PASS
...

==========================================
Test Summary:
==========================================
Total tests:  42
Passed:       38
Failed:       4

4 test(s) failed.
Check individual log files in test_logs/ for details.
```

## Log Files

All test outputs are saved in the `test_logs/` directory:
- `test_logs/<test_name>.log` - Complete simulation output for each test
- Useful for debugging failed tests
- Contains detailed processor execution traces

## Manual Testing

You can still test individual files manually:
```bash
make -f tb/cocotb/test_soc.mk HEX_FILE=tb/riscv-tests/hex/add.S.hex
```

## Requirements

- **cocotb**: Python testing framework
- **Icarus Verilog**: Simulator (or other supported simulator)
- **Make**: Build system
- **Bash**: For running the test scripts

## Troubleshooting

### Script won't run
```bash
chmod +x test_all_hex.sh  # Make sure script is executable
```

### No hex files found
- Check that `tb/riscv-tests/hex/` directory exists
- Verify hex files are present with `.hex` extension

### Make command fails
- Check that cocotb is installed: `pip install cocotb`
- Verify simulator is installed (e.g., `iverilog`)
- Check that all Verilog source files exist

### Test hangs or takes too long
- Check the `max_cycles` setting in `tb/cocotb/test_soc.py`
- Some tests might have infinite loops or not reach ECALL

## Understanding Test Results

### What does a PASS mean?
- The program executed successfully
- Reached the ECALL instruction
- Register `x10` was 0 (indicating success in RISC-V test convention)

### What does a FAIL mean?
- The program reached ECALL but `x10` was non-zero
- This typically indicates the test detected an error condition
- Check the specific error value in `x10` for debugging clues

### Common failure patterns:
- `x10 = 0x00000001`: Generic test failure
- `x10 = 0x00000013`: Specific assertion failed (like in `and.S`)
- Other values: Test-specific error codes 
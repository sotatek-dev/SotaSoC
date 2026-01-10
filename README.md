# RV32E SoC

This is a System-on-Chip (SoC) featuring a RISC-V core with support for the following extensions:
- **RV32E**: 32-bit RISC-V with 16 registers (embedded variant)
- **Zicsr**: Control and Status Register extension
- **Zifencei**: Instruction-fetch fence extension

## Features

### Memory Support
- **QSPI Flash**: Program storage in QSPI flash memory
- **QSPI PSRAM**: Support for QSPI PSRAM memory

### Peripherals
- **UART**: Universal Asynchronous Receiver-Transmitter
- **Timer**: Timer peripheral for system timing

## Testing

### Environment Setup

Install required dependencies:

```bash
sudo apt-get install make python3 python3-pip libpython3-dev iverilog
python -m venv venv
source venv/bin/activate
pip install "cocotb~=2.0"
```

### Core Tests

Run the core test suites:

```bash
make -f tb/cocotb/test_rv32i_core.mk
make -f tb/cocotb/test_rv32i_core_hazard.mk
make -f tb/cocotb/test_rv32i_core_jump.mk
```

### RISC-V Tests

Run the complete RISC-V test suite:

```bash
./scripts/test_all_bin_spi.sh
```

To test individual files:

```bash
make -f tb/cocotb/test_spi_mem.mk TESTCASE=test_spi_bin_file BIN_FILE=tb/riscv-tests/bin/addi.S.bin
```

### RISCOF Tests

For RISCOF (RISC-V Compatibility Framework) testing, see [tb/riscof/README.md](tb/riscof/README.md).

### Testing Your Own Program

To test your own RISC-V program:

1. Compile your program to ELF format
2. Convert to binary format:
   ```bash
   riscv64-unknown-elf-objcopy -O binary program.elf program.bin
   ```
3. Run the test with your binary:
   ```bash
   make -f tb/cocotb/test_spi_mem.mk TESTCASE=test_spi_bin_file BIN_FILE=program.bin
   ```

## Project Structure

- `rtl/`: RTL source files
  - `rv32i_core.sv`: Main RISC-V core implementation
  - `soc.v`: System-on-Chip top level
  - `peri/`: Peripheral modules (UART, Timer, SPI)
- `tb/`: Testbench files
  - `cocotb/`: Cocotb-based testbenches
  - `riscof/`: RISCOF test framework
  - `riscv-tests/`: RISC-V test suite
- `scripts/`: Utility scripts for testing and setup


# RV32I Simple ALU Test

This is a minimal setup to test a simple ALU module using Icarus Verilog and Python tests with cocotb.

## Project Structure

```
RV32I/
├── rtl/
│   └── rv32i_alu.v          # Simple ALU module
├── tb/
│   ├── tb_rv32i_alu.v       # Verilog testbench
│   ├── cocotb_tb.v           # cocotb testbench wrapper
│   └── cocotb/
│       ├── test_rv32i_alu.py # Python tests
│       └── test_basic.py      # Basic cocotb test
├── build/                    # Build artifacts
├── Makefile                  # cocotb build and test automation
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## ALU Operations

The simple ALU supports the following operations:

- `0000` - ADD: result = a + b
- `0001` - SUB: result = a - b  
- `0010` - AND: result = a & b
- `0011` - OR:  result = a | b
- `0100` - XOR: result = a ^ b

## Prerequisites

- Python 3.7+
- Icarus Verilog
- GTKWave (optional, for waveform viewing)

### Installation

#### macOS (using Homebrew)
```bash
brew install icarus-verilog
brew install gtkwave
```

#### Python Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Run Python Tests (Recommended)
```bash
make
```

### Run Specific Test Module
```bash
MODULE=test_basic make
```

### Run Verilog Tests
```bash
make test
```

### View Waveforms
```bash
make wave
```

### Clean Build Artifacts
```bash
make clean
```

## Test Results

### Python Tests (cocotb)
All 8 Python tests pass:
- ✅ Addition: 10 + 20 = 30
- ✅ Subtraction: 30 - 10 = 20
- ✅ AND: 0f0f0f0f & 00ff00ff = 000f000f
- ✅ OR: 0f0f0f0f | 00ff00ff = 0fff0fff
- ✅ XOR: 0f0f0f0f ^ 00ff00ff = 0ff00ff0
- ✅ Zero result: 15 - 15 = 0
- ✅ Negative result: 10 - 20 = -10 (0xFFFFFFF6)
- ✅ Default operation: Invalid op → 0

### Verilog Tests
The Verilog testbench also verifies all operations with detailed output.

## Python Testing Features

The Python tests using cocotb provide:
- **Comprehensive testing**: All ALU operations tested
- **Edge cases**: Zero results, negative numbers, invalid operations
- **Easy debugging**: Detailed error messages and assertions
- **Waveform generation**: VCD files for waveform analysis
- **Fast execution**: Efficient test framework

## Next Steps

This simple setup provides a foundation for:
1. Adding more complex ALU operations
2. Implementing more sophisticated test scenarios
3. Building the full RV32I processor
4. Adding performance and timing tests
5. Creating instruction-level tests 
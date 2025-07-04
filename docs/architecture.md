# RV32I Processor Architecture

## Overview

This document describes the architecture and implementation of the RV32I processor, a RISC-V embedded processor that implements the RV32I base integer instruction set.

## RV32I ISA Features

The RV32I (Embedded) base integer instruction set is a reduced version of RV32I designed for embedded applications:

- **32-bit address space**: Full 32-bit addressing capability
- **16 general-purpose registers**: x0-x15 (instead of 32 registers in RV32I)
- **Base integer operations**: Arithmetic, logical, and control flow instructions
- **Memory operations**: Load and store instructions with byte, half-word, and word access
- **System instructions**: Basic system calls and debug support

## Processor Architecture

### Pipeline Stages

The RV32I processor implements a 4-stage pipeline:

1. **Fetch Stage**
   - Instruction memory access
   - Program counter management
   - Branch prediction (simple)

2. **Decode Stage**
   - Instruction decoding
   - Register file read
   - Control signal generation
   - Immediate value extraction

3. **Execute Stage**
   - ALU operations
   - Branch condition evaluation
   - Address calculation for memory operations

4. **Memory Stage**
   - Data memory access
   - Register file write
   - Pipeline register updates

### Key Components

#### Register File
- **16 registers**: x0-x15 as per RV32I specification
- **Dual read ports**: For rs1 and rs2 operands
- **Single write port**: For rd destination
- **x0 hardwired to zero**: Always reads as 0, writes ignored

#### ALU (Arithmetic Logic Unit)
- **Arithmetic operations**: ADD, SUB, SLT, SLTU
- **Logical operations**: AND, OR, XOR
- **Shift operations**: SLL, SRL, SRA
- **Comparison operations**: For branch conditions

#### Instruction Decoder
- **Opcode decoding**: Identifies instruction type
- **Field extraction**: rs1, rs2, rd, immediate values
- **Control signal generation**: ALU op, memory control, register write enable
- **Illegal instruction detection**: Validates instruction format

#### Memory Interface
- **Instruction memory**: 32-bit aligned access
- **Data memory**: Byte-addressable with alignment checking
- **Load/Store operations**: Byte, half-word, and word access

## Instruction Set Support

### Arithmetic Instructions
- `ADD`, `ADDI`: Addition
- `SUB`: Subtraction
- `SLT`, `SLTI`: Set if less than (signed)
- `SLTU`, `SLTIU`: Set if less than (unsigned)

### Logical Instructions
- `AND`, `ANDI`: Bitwise AND
- `OR`, `ORI`: Bitwise OR
- `XOR`, `XORI`: Bitwise XOR

### Shift Instructions
- `SLL`, `SLLI`: Logical left shift
- `SRL`, `SRLI`: Logical right shift
- `SRA`, `SRAI`: Arithmetic right shift

### Memory Instructions
- `LB`, `LH`, `LW`: Load byte, half-word, word
- `LBU`, `LHU`: Load byte, half-word (unsigned)
- `SB`, `SH`, `SW`: Store byte, half-word, word

### Control Flow Instructions
- `BEQ`, `BNE`: Branch if equal/not equal
- `BLT`, `BGE`: Branch if less/greater or equal (signed)
- `BLTU`, `BGEU`: Branch if less/greater or equal (unsigned)
- `JAL`: Jump and link
- `JALR`: Jump and link register

### Immediate Instructions
- `LUI`: Load upper immediate
- `AUIPC`: Add upper immediate to PC

### System Instructions
- `ECALL`: Environment call
- `EBREAK`: Environment break

## Memory Map

```
0x00000000 - 0x00000FFF: Data Memory (4KB)
0x80000000 - 0x80000FFF: Instruction Memory (4KB)
0x40000000 - 0x4FFFFFFF: Peripheral Space
```

## Implementation Details

### Clock and Reset
- **Clock**: Single clock domain design
- **Reset**: Asynchronous active-low reset
- **Frequency**: Target 100MHz operation

### Data Path
- **Data width**: 32-bit throughout
- **Address width**: 32-bit
- **Register width**: 4-bit (for 16 registers)

### Control Signals
- **ALU operation**: 4-bit control
- **Memory control**: Read/write enable, width select
- **Register control**: Write enable
- **Branch control**: Branch type and condition

### Pipeline Hazards
- **Data hazards**: Handled by forwarding (future enhancement)
- **Control hazards**: Simple branch prediction
- **Structural hazards**: Single-issue pipeline

## Performance Characteristics

### Timing
- **CPI**: 1.0 for most instructions
- **Branch penalty**: 1 cycle for taken branches
- **Memory latency**: 1 cycle for aligned access

### Resource Usage
- **Registers**: 16 general-purpose + control registers
- **Memory**: 4KB instruction + 4KB data
- **Logic**: ~1000 LUTs (estimated)

## Future Enhancements

### Pipeline Improvements
- **Forwarding logic**: Eliminate data hazards
- **Branch prediction**: Reduce control hazards
- **Out-of-order execution**: Improve performance

### Memory System
- **Cache**: Instruction and data caches
- **Memory management**: MMU support
- **DMA**: Direct memory access

### ISA Extensions
- **M extension**: Integer multiplication and division
- **C extension**: Compressed instructions
- **F extension**: Single-precision floating point

## Verification Strategy

### Unit Testing
- **ALU tests**: All arithmetic and logical operations
- **Register file tests**: Read/write operations
- **Decoder tests**: Instruction decoding and control signals

### Integration Testing
- **Pipeline tests**: Multi-cycle instruction sequences
- **Memory tests**: Load/store operations
- **Branch tests**: Control flow instructions

### Compliance Testing
- **RISC-V compliance**: Official test suite
- **Performance testing**: Benchmark programs
- **Stress testing**: Random instruction sequences 
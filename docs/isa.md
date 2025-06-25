# RV32E Instruction Set Architecture (ISA)

## Overview

RV32E is a reduced version of the RISC-V RV32I instruction set architecture designed for embedded systems. The "E" stands for "Embedded" and it uses only 16 registers instead of the full 32 registers found in RV32I.

## Key Characteristics

- **Architecture**: 32-bit RISC-V embedded variant
- **Registers**: 16 general-purpose registers (x0-x15)
- **Address Space**: 32-bit address space
- **Endianness**: Little-endian
- **Base ISA**: RV32E (Embedded)
- **Extensions**: None (base integer instructions only)

## Register Set

### General-Purpose Registers (16 registers)

| Register | ABI Name | Description | Preserved |
|----------|----------|-------------|-----------|
| x0       | zero     | Hardwired to zero | N/A |
| x1       | ra       | Return address | No |
| x2       | sp       | Stack pointer | Yes |
| x3       | gp       | Global pointer | Yes |
| x4       | tp       | Thread pointer | Yes |
| x5       | t0       | Temporary/alternate link register | No |
| x6       | t1       | Temporary | No |
| x7       | t2       | Temporary | No |
| x8       | s0/fp    | Saved register/frame pointer | Yes |
| x9       | s1       | Saved register | Yes |
| x10      | a0       | Function argument/return value | No |
| x11      | a1       | Function argument/return value | No |
| x12      | a2       | Function argument | No |
| x13      | a3       | Function argument | No |
| x14      | a4       | Function argument | No |
| x15      | a5       | Function argument | No |

### Special Registers

- **PC**: Program Counter (32-bit)
- **CSRs**: Control and Status Registers (if implemented)

## Instruction Formats

RV32E uses the same instruction formats as RV32I:

### R-Type (Register-Register)
```
31       25 24    20 19    15 14    12 11    7 6      0
  funct7   |  rs2   |  rs1   | funct3 |  rd   | opcode
```

### I-Type (Register-Immediate)
```
31         20 19    15 14    12 11    7 6      0
   imm[11:0] |  rs1   | funct3 |  rd   | opcode
```

### S-Type (Store)
```
31        25 24    20 19    15 14    12 11    7 6      0
  imm[11:5] |  rs2   |  rs1   | funct3 | imm[4:0] | opcode
```

### B-Type (Branch)
```
31           25 24    20 19    15 14    12 11    7 6      0
  imm[12,10:5] |  rs2   |  rs1   | funct3 | imm[4:1,11] | opcode
```

### U-Type (Upper Immediate)
```
31          12 11    7 6      0
   imm[31:12] |  rd   | opcode
```

### J-Type (Jump)
```
31                    12 11    7 6      0
  imm[20,10:1,11,19:12] |  rd   | opcode
```

## Instruction Categories

### 1. Arithmetic and Logical Instructions

#### Integer Register-Register Operations (R-Type)

| Instruction | Opcode | funct3 | funct7 | Operation |
|-------------|--------|--------|--------|-----------|
| ADD rd, rs1, rs2 | 0110011 | 000 | 0000000 | rd = rs1 + rs2 |
| SUB rd, rs1, rs2 | 0110011 | 000 | 0100000 | rd = rs1 - rs2 |
| SLL rd, rs1, rs2 | 0110011 | 001 | 0000000 | rd = rs1 << rs2[4:0] |
| SLT rd, rs1, rs2 | 0110011 | 010 | 0000000 | rd = (rs1 < rs2) ? 1 : 0 (signed) |
| SLTU rd, rs1, rs2 | 0110011 | 011 | 0000000 | rd = (rs1 < rs2) ? 1 : 0 (unsigned) |
| XOR rd, rs1, rs2 | 0110011 | 100 | 0000000 | rd = rs1 ^ rs2 |
| SRL rd, rs1, rs2 | 0110011 | 101 | 0000000 | rd = rs1 >> rs2[4:0] (logical) |
| SRA rd, rs1, rs2 | 0110011 | 101 | 0100000 | rd = rs1 >> rs2[4:0] (arithmetic) |
| OR rd, rs1, rs2 | 0110011 | 110 | 0000000 | rd = rs1 \| rs2 |
| AND rd, rs1, rs2 | 0110011 | 111 | 0000000 | rd = rs1 & rs2 |

#### Integer Register-Immediate Operations (I-Type)

| Instruction | Opcode | funct3 | Operation |
|-------------|--------|--------|-----------|
| ADDI rd, rs1, imm | 0010011 | 000 | rd = rs1 + sign_extend(imm) |
| SLTI rd, rs1, imm | 0010011 | 010 | rd = (rs1 < sign_extend(imm)) ? 1 : 0 |
| SLTIU rd, rs1, imm | 0010011 | 011 | rd = (rs1 < sign_extend(imm)) ? 1 : 0 (unsigned) |
| XORI rd, rs1, imm | 0010011 | 100 | rd = rs1 ^ sign_extend(imm) |
| ORI rd, rs1, imm | 0010011 | 110 | rd = rs1 \| sign_extend(imm) |
| ANDI rd, rs1, imm | 0010011 | 111 | rd = rs1 & sign_extend(imm) |
| SLLI rd, rs1, shamt | 0010011 | 001 | rd = rs1 << shamt |
| SRLI rd, rs1, shamt | 0010011 | 101 | rd = rs1 >> shamt (logical) |
| SRAI rd, rs1, shamt | 0010011 | 101 | rd = rs1 >> shamt (arithmetic) |

### 2. Load and Store Instructions

#### Load Instructions (I-Type)

| Instruction | Opcode | funct3 | Operation |
|-------------|--------|--------|-----------|
| LB rd, offset(rs1) | 0000011 | 000 | rd = sign_extend(M[rs1 + offset][7:0]) |
| LH rd, offset(rs1) | 0000011 | 001 | rd = sign_extend(M[rs1 + offset][15:0]) |
| LW rd, offset(rs1) | 0000011 | 010 | rd = M[rs1 + offset] |
| LBU rd, offset(rs1) | 0000011 | 100 | rd = zero_extend(M[rs1 + offset][7:0]) |
| LHU rd, offset(rs1) | 0000011 | 101 | rd = zero_extend(M[rs1 + offset][15:0]) |

#### Store Instructions (S-Type)

| Instruction | Opcode | funct3 | Operation |
|-------------|--------|--------|-----------|
| SB rs2, offset(rs1) | 0100011 | 000 | M[rs1 + offset] = rs2[7:0] |
| SH rs2, offset(rs1) | 0100011 | 001 | M[rs1 + offset] = rs2[15:0] |
| SW rs2, offset(rs1) | 0100011 | 010 | M[rs1 + offset] = rs2 |

### 3. Control Transfer Instructions

#### Unconditional Jumps

| Instruction | Type | Operation |
|-------------|------|-----------|
| JAL rd, offset | J-Type | rd = PC + 4; PC = PC + sign_extend(offset) |
| JALR rd, rs1, offset | I-Type | rd = PC + 4; PC = (rs1 + sign_extend(offset)) & ~1 |

#### Conditional Branches (B-Type)

| Instruction | funct3 | Operation |
|-------------|--------|-----------|
| BEQ rs1, rs2, offset | 000 | if (rs1 == rs2) PC = PC + sign_extend(offset) |
| BNE rs1, rs2, offset | 001 | if (rs1 != rs2) PC = PC + sign_extend(offset) |
| BLT rs1, rs2, offset | 100 | if (rs1 < rs2) PC = PC + sign_extend(offset) (signed) |
| BGE rs1, rs2, offset | 101 | if (rs1 >= rs2) PC = PC + sign_extend(offset) (signed) |
| BLTU rs1, rs2, offset | 110 | if (rs1 < rs2) PC = PC + sign_extend(offset) (unsigned) |
| BGEU rs1, rs2, offset | 111 | if (rs1 >= rs2) PC = PC + sign_extend(offset) (unsigned) |

### 4. Upper Immediate Instructions (U-Type)

| Instruction | Operation |
|-------------|-----------|
| LUI rd, imm | rd = sign_extend(imm << 12) |
| AUIPC rd, imm | rd = PC + sign_extend(imm << 12) |

### 5. System Instructions

| Instruction | Opcode | funct3 | Operation |
|-------------|--------|--------|-----------|
| FENCE | 0001111 | 000 | Order memory accesses |
| ECALL | 1110011 | 000 | Environment call |
| EBREAK | 1110011 | 000 | Environment break |

## Implementation Details

### ALU Operations (Implementation-Specific)

The RV32E implementation includes a comprehensive ALU supporting all arithmetic and logical operations. **Note: The following ALU operation codes are microarchitectural details specific to this implementation and are NOT part of the RV32E ISA specification.**

```verilog
// ALU operation codes (implementation-specific)
localparam ADD  = 4'b0000;  // Addition
localparam SUB  = 4'b0001;  // Subtraction
localparam AND  = 4'b0010;  // Bitwise AND
localparam OR   = 4'b0011;  // Bitwise OR
localparam XOR  = 4'b0100;  // Bitwise XOR
localparam SLL  = 4'b0101;  // Logical left shift
localparam SRL  = 4'b0110;  // Logical right shift
localparam SRA  = 4'b0111;  // Arithmetic right shift
localparam SLT  = 4'b1000;  // Set if less than (signed)
localparam SLTU = 4'b1001;  // Set if less than (unsigned)
localparam SEQ  = 4'b1010;  // Set if equal
localparam SNE  = 4'b1011;  // Set if not equal
localparam SGE  = 4'b1100;  // Set if greater than or equal (signed)
localparam SGEU = 4'b1101;  // Set if greater than or equal (unsigned)
localparam SGT  = 4'b1110;  // Set if greater than (signed)
localparam SGTU = 4'b1111;  // Set if greater than (unsigned)
```

### Flag Generation (Implementation-Specific)

The ALU generates three status flags as part of this specific implementation:
- **Zero Flag**: Set when result equals zero
- **Negative Flag**: Set when result is negative (MSB = 1)
- **Overflow Flag**: Set on arithmetic overflow

**Note**: These flags are implementation details and may not be present in all RV32E implementations.

## Memory Model

- **Address Space**: 32-bit flat address space
- **Alignment**: Natural alignment required for loads/stores
- **Endianness**: Little-endian byte order
- **Memory Access**: Byte-addressable

## Calling Convention

### Function Arguments
- a0-a5 (x10-x15): Function arguments
- a0-a1 (x10-x11): Return values

### Callee-Saved Registers
- s0-s1 (x8-x9): Must be preserved by callee
- sp (x2): Stack pointer
- gp (x3): Global pointer
- tp (x4): Thread pointer

### Caller-Saved Registers
- t0-t2 (x5-x7): May be modified by callee
- ra (x1): Return address
- a0-a5 (x10-x15): Function arguments

## Differences from RV32I

1. **Register Count**: 16 registers vs 32 registers
2. **Register Range**: x0-x15 vs x0-x31
3. **ABI**: Modified calling convention for reduced register set
4. **Code Size**: Generally smaller due to reduced register pressure
5. **Performance**: May have higher register pressure in complex functions

## Use Cases

RV32E is ideal for:
- **Embedded systems** with limited resources
- **IoT devices** requiring low power consumption
- **Microcontrollers** with constrained memory
- **Simple processors** where register count is not critical
- **Educational implementations** of RISC-V

## Compliance

This implementation follows the RISC-V RV32E specification as defined in the RISC-V Instruction Set Manual, Volume I: Unprivileged ISA.

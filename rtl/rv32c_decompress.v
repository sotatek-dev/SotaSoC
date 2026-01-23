/* RISC-V C Extension Decompression Module

   This module decompresses 16-bit compressed instructions into their
   32-bit equivalent instructions according to the RISC-V Compressed
   Extension specification.

   Input:  16-bit compressed instruction
   Output: 32-bit decompressed instruction
*/

module rv32c_decompress (
    input wire [15:0] instr_16bit,      // 16-bit compressed instruction
    output reg [31:0] instr_32bit,      // 32-bit decompressed instruction
    output reg is_valid                 // 1 if instruction is valid compressed instruction
);

    localparam INSTR_INVALID = 32'hFFFFFFFF;

    // Extract instruction fields
    wire [1:0] op = instr_16bit[1:0];
    wire [2:0] funct3 = instr_16bit[15:13];
    wire [2:0] funct3_sub1 = instr_16bit[12:10];
    wire [1:0] funct2 = instr_16bit[6:5];
    wire [3:0] funct4 = instr_16bit[15:12];

    wire [4:0] cr_rs2 = instr_16bit[6:2];
    wire [4:0] cr_rs1 = instr_16bit[11:7];
    wire [4:0] cr_rd = instr_16bit[11:7];
    wire [3:0] cr_funct4 = instr_16bit[15:12];

    wire [5:0] ci_imm = {instr_16bit[12], instr_16bit[6:2]};
    wire [4:0] ci_rs1 = instr_16bit[11:7];
    wire [4:0] ci_rd = instr_16bit[11:7];
    wire [9:0] ci_nzimm = {instr_16bit[12], instr_16bit[4:3], instr_16bit[5], instr_16bit[2], instr_16bit[6], 4'b0};
    wire [4:0] ci_shamt = instr_16bit[6:2];
    wire [7:0] ci_imm8 = {instr_16bit[3:2], instr_16bit[12], instr_16bit[6:4], 2'b00};

    wire [7:0] css_imm = {instr_16bit[8:7], instr_16bit[12:9], 2'b00};
    wire [4:0] css_rs2 = instr_16bit[6:2];

    wire [9:0] ciw_nzuimm = {instr_16bit[10:7], instr_16bit[12:11], instr_16bit[5], instr_16bit[6], 2'b00};
    wire [2:0] ciw_rd = instr_16bit[4:2];

    wire [6:0] cl_imm = {instr_16bit[5], instr_16bit[12:10], instr_16bit[6], 2'b00};
    wire [2:0] cl_rd = instr_16bit[4:2];
    wire [2:0] cl_rs1 = instr_16bit[9:7];

    wire [6:0] cs_imm = {instr_16bit[5], instr_16bit[12:10], instr_16bit[6], 2'b00};
    wire [2:0] cs_rd = instr_16bit[9:7];
    wire [2:0] cs_rs1 = instr_16bit[9:7];
    wire [2:0] cs_rs2 = instr_16bit[4:2];

    wire [8:0] cb_imm = {instr_16bit[12], instr_16bit[6:5], instr_16bit[2], instr_16bit[11:10], instr_16bit[4:3], 1'b0};
    wire [2:0] cb_rs1 = instr_16bit[9:7];
    wire [4:0] cb_shamt = instr_16bit[6:2];
    wire [5:0] cb_imm6 = {instr_16bit[12], instr_16bit[6:2]};

    wire [11:0] cj_imm = {instr_16bit[12], instr_16bit[8], instr_16bit[10:9], instr_16bit[6], instr_16bit[7], instr_16bit[2], instr_16bit[11], instr_16bit[5:3], 1'b0};

    // Decompression logic
    always @(*) begin
        is_valid = 1'b1;

        case (op)
            // Quadrant 0: op[1:0] = 2'b00
            2'b00: begin
                case (funct3)
                    // C.ADDI4SPN: Add immediate to stack pointer (nzuimm[9:2])
                    // Decompresses to: ADDI rd', sp, 4*imm
                    3'b000: begin
                        if (ciw_nzuimm == 8'b0) begin
                            // Reserved: nzuimm = 0
                            instr_32bit = INSTR_INVALID;
                            is_valid = 1'b0;
                        end else begin
                            // Decompress to ADDI: imm[11:0] = {2'b00, nzuimm[9:2], 2'b00}
                            instr_32bit = {
                                2'b00,                         // zero-extend
                                ciw_nzuimm,                    // imm[9:0] = nzuimm[9:0]
                                5'd2,                          // rs1 = x2 (stack pointer)
                                3'b000,                        // funct3 = ADD
                                {2'b01, ciw_rd},               // rd'
                                7'b0010011                     // opcode = OP-IMM
                            };
                        end
                    end

                    // C.LW: Load word
                    // Decompresses to: LW rd', 4*imm(rs1')
                    3'b010: begin
                        instr_32bit = {
                            {5'b00000},                        // imm[11:7] = zero-extend
                            cl_imm[6:0],                       // imm[6:0] = cl_imm[6:0]
                            {2'b01, cl_rs1},                   // rs1'
                            3'b010,                            // funct3 = LW
                            {2'b01, cl_rd},                    // rd'
                            7'b0000011                         // opcode = LOAD
                        };
                    end

                    // C.SW: Store word
                    // Decompresses to: SW rs2', offset(rs1')
                    3'b110: begin
                        instr_32bit = {
                            {5'b00000},                        // imm[11:7] = zero-extend
                            cs_imm[6:5],                       // imm[6:5] = cs_imm[6:5]
                            {2'b01, cs_rs2},                   // rs2'
                            {2'b01, cl_rs1},                   // rs1'
                            3'b010,                            // funct3 = SW
                            cs_imm[4:0],                       // imm[4:0] = cs_imm[4:0]
                            7'b0100011                         // opcode = STORE
                        };
                    end

                    default: begin
                        instr_32bit = INSTR_INVALID;
                        is_valid = 1'b0;
                    end
                endcase
            end

            // Quadrant 1: op[1:0] = 2'b01
            2'b01: begin
                case (funct3)
                    // C.ADDI: Add immediate
                    // Decompresses to: ADDI rd, rd, imm[5:0]
                    // Special case: C.NOP if rd = 0
                    3'b000: begin
                        if (instr_16bit[11:7] == 5'b0) begin
                            // C.NOP: ADDI x0, x0, 0
                            // This is a valid instruction
                            instr_32bit = 32'h00000013; // NOP
                        end else begin
                            instr_32bit = {
                                {6{ci_imm[5]}},                 // imm[11:6] = sign-extend from ci_imm[5]
                                ci_imm[5:0],                    // imm[5:0] = ci_imm[5:0]
                                ci_rs1[4:0],                    // rs1 = rd'
                                3'b000,                         // funct3 = ADD
                                ci_rd[4:0],                     // rd = rd'
                                7'b0010011                      // opcode = OP-IMM
                            };
                        end
                    end

                    // C.JAL: Jump and link (RV32 only)
                    // Decompresses to: JAL x1, offset[11:1]
                    3'b001: begin
                        instr_32bit = {
                            {cj_imm[11]},                      // Sign extend
                            cj_imm[10:1],
                            cj_imm[11],                        // imm[11]
                            {8{cj_imm[11]}},                   // imm[19:12] = Sign extend
                            5'd1,                              // rd = x1 (return address)
                            7'b1101111                         // opcode = JAL
                        };
                    end

                    // C.LI: Load immediate
                    // Decompresses to: ADDI rd, x0, imm[5:0]
                    3'b010: begin
                        instr_32bit = {
                            {6{ci_imm[5]}},                 // imm[11:6] = sign-extend from ci_imm[5]
                            ci_imm[5:0],                    // imm[5:0] = ci_imm[5:0]
                            5'd0,                           // rs1 = x0
                            3'b000,                         // funct3 = ADD
                            ci_rd[4:0],                     // rd = rd'
                            7'b0010011                      // opcode = OP-IMM
                        };
                    end

                    // C.LUI or C.ADDI16SP
                    3'b011: begin
                        // Note: not sure C.LUI with rd = x0 is valid or not
                        if (ci_rd != 5'd2) begin
                            // C.LUI: Load upper immediate
                            // Decompresses to: LUI rd, imm[17:12]
                            if (ci_imm == 6'b0) begin
                                // Reserved: imm = 0
                                instr_32bit = INSTR_INVALID;
                                is_valid = 1'b0;
                            end else begin
                                instr_32bit = {
                                    {14{ci_imm[5]}},           // sign-extend from ci_imm[5]
                                    ci_imm[5:0],               //
                                    ci_rd[4:0],                // rd = rd'
                                    7'b0110111                 // opcode = LUI
                                };
                            end
                        end else begin
                            // C.ADDI16SP
                            // Decompresses to: ADDI x2, x2, nzimm[9:4]
                            if (ci_nzimm == 6'b0) begin
                                // Reserved: nzimm = 0
                                instr_32bit = INSTR_INVALID;
                                is_valid = 1'b0;
                            end else begin
                                instr_32bit = {
                                    {2{ci_nzimm[9]}},           // sign-extend from ci_nzimm[9]
                                    ci_nzimm[9:0],
                                    5'd2,                       // rs1 = x2 (stack pointer)
                                    3'b000,                     // funct3 = ADD
                                    5'd2,                       // rd = x2
                                    7'b0010011                  // opcode = OP-IMM
                                };
                            end
                        end
                    end

                    // C.SRLI, C.SRAI, C.ANDI: ALU operations with compressed registers
                    3'b100: begin
                        case (funct3_sub1)
                            // C.SRLI: Shift right logical immediate
                            // Decompresses to: SRLI rd', rd', shamt[5:0]
                            3'b000, 3'b100: begin
                                instr_32bit = {
                                    7'b0,                       // 0x00
                                    cb_shamt,                   // shamt[4:0]
                                    {2'b01, cb_rs1},            // rs1 = rd' (maps to x8-x15)
                                    3'b101,                     // funct3 = SRL
                                    {2'b01, cb_rs1},            // rd = rd' (maps to x8-x15)
                                    7'b0010011                  // opcode = OP-IMM
                                };
                            end

                            // C.SRAI: Shift right arithmetic immediate
                            // Decompresses to: SRAI rd', rd', shamt[5:0]
                            3'b001, 3'b101: begin
                                instr_32bit = {
                                    7'b0100000,                 // 0x20
                                    cb_shamt,                   // shamt[4:0]
                                    {2'b01, cb_rs1},            // rs1 = rd' (maps to x8-x15)
                                    3'b101,                     // funct3 = SRA
                                    {2'b01, cb_rs1},            // rd = rd' (maps to x8-x15)
                                    7'b0010011                  // opcode = OP-IMM
                                };
                            end

                            // C.ANDI: AND immediate
                            // Decompresses to: ANDI rd', rd', imm[5:0]
                            3'b010, 3'b110: begin
                                instr_32bit = {
                                    {6{cb_imm6[5]}},            // sign-extend from cb_imm6[5]
                                    cb_imm6,                    //
                                    {2'b01, cb_rs1},            // rs1 = rd' (maps to x8-x15)
                                    3'b111,                     // funct3 = ANDI
                                    {2'b01, cb_rs1},            // rd = rd' (maps to x8-x15)
                                    7'b0010011                  // opcode = OP-IMM
                                };
                            end

                            // C.SUB, C.XOR, C.OR, C.AND: Register operations
                            3'b011: begin
                                case (funct2)
                                    // C.SUB: Subtract
                                    // Decompresses to: SUB rd', rd', rs2'
                                    2'b00: begin
                                        instr_32bit = {
                                            7'b0100000,         // funct7 = SUB
                                            {2'b01, cs_rs2},    // rs2' (maps to x8-x15)
                                            {2'b01, cs_rd},     // rs1 = rd' (maps to x8-x15)
                                            3'b000,             // funct3 = ADD/SUB
                                            {2'b01, cs_rd},     // rd = rd' (maps to x8-x15)
                                            7'b0110011          // opcode
                                        };
                                    end

                                    // C.XOR: XOR
                                    // Decompresses to: XOR rd', rd', rs2'
                                    2'b01: begin
                                        instr_32bit = {
                                            7'b0000000,         // funct7 = 0
                                            {2'b01, cs_rs2},    // rs2' (maps to x8-x15)
                                            {2'b01, cs_rd},     // rs1 = rd' (maps to x8-x15)
                                            3'b100,             // funct3 = XOR
                                            {2'b01, cs_rd},     // rd = rd' (maps to x8-x15)
                                            7'b0110011          // opcode
                                        };
                                    end
                                    
                                    // C.OR: OR
                                    // Decompresses to: OR rd', rd', rs2'
                                    2'b10: begin
                                        instr_32bit = {
                                            7'b0000000,         // funct7 = 0
                                            {2'b01, cs_rs2},    // rs2' (maps to x8-x15)
                                            {2'b01, cs_rd},     // rs1 = rd' (maps to x8-x15)
                                            3'b110,             // funct3 = OR
                                            {2'b01, cs_rd},     // rd = rd' (maps to x8-x15)
                                            7'b0110011          // opcode
                                        };
                                    end

                                    // C.AND: AND
                                    // Decompresses to: AND rd', rd', rs2'
                                    2'b11: begin
                                        instr_32bit = {
                                            7'b0000000,         // funct7 = 0
                                            {2'b01, cs_rs2},    // rs2' (maps to x8-x15)
                                            {2'b01, cs_rd},     // rs1 = rd' (maps to x8-x15)
                                            3'b111,             // funct3 = AND
                                            {2'b01, cs_rd},     // rd = rd' (maps to x8-x15)
                                            7'b0110011          // opcode
                                        };
                                    end

                                    default: begin
                                        instr_32bit = INSTR_INVALID;
                                        is_valid = 1'b0;
                                    end
                                endcase
                            end
                            
                            default: begin
                                instr_32bit = INSTR_INVALID;
                                is_valid = 1'b0;
                            end
                        endcase
                    end

                    // C.J: Jump
                    // Decompresses to: JAL x0, offset[11:1]
                    3'b101: begin
                        // imm = {instr[12], instr[8], instr[10:9], instr[6], instr[7], instr[2], instr[11], instr[5:3], 1'b0}
                        instr_32bit = {
                            {cj_imm[11]},                      // Sign extend
                            cj_imm[10:1],
                            cj_imm[11],                        // imm[11]
                            {8{cj_imm[11]}},                   // imm[19:12] = Sign extend
                            5'd0,                              // rd = x0 (return address)
                            7'b1101111                         // opcode = JAL
                        };
                    end

                    // C.BEQZ: Branch if equal to zero
                    3'b110: begin
                        // C.BEQZ: Branch if equal to zero
                        // Decompresses to: BEQ rs1', x0, offset[8:1]
                        instr_32bit = {
                            {3{cb_imm[8]}},            // Sign extend
                            cb_imm[8:5],               // cb_imm[8:5]
                            5'd0,                      // rs2 = x0
                            {2'b01, cb_rs1},           // rs1' (maps to x8-x15)
                            3'b000,                    // funct3 = BEQ
                            {cb_imm[4:1], cb_imm[8]},  // cb_imm[11] == cb_imm[8] sign extend
                            7'b1100011                 // opcode = BRANCH
                        };
                    end

                    // C.BNEZ: Branch if not equal to zero
                    3'b111: begin
                        // C.BNEZ: Branch if not equal to zero
                        // Decompresses to: BNE rs1', x0, offset[8:1]
                        instr_32bit = {
                            {3{cb_imm[8]}},            // Sign extend
                            cb_imm[8:5],               // cb_imm[8:5]
                            5'd0,                      // rs2 = x0
                            {2'b01, cb_rs1},           // rs1' (maps to x8-x15)
                            3'b001,                    // funct3 = BNE
                            {cb_imm[4:1], cb_imm[8]},  // cb_imm[11] == cb_imm[8] sign extend
                            7'b1100011                 // opcode = BRANCH
                        };
                    end

                    default: begin
                        instr_32bit = INSTR_INVALID;
                        is_valid = 1'b0;
                    end
                endcase
            end
            
            // Quadrant 2: op[1:0] = 2'b10
            2'b10: begin
                case (funct3)
                    // C.SLLI: Shift left logical immediate
                    // Decompresses to: SLLI rd, rd, shamt[5:0]
                    3'b000: begin
                        instr_32bit = {
                            7'b0000000,                    //
                            ci_shamt[4:0],                 // shamt[4:0]
                            ci_rs1[4:0],                   // rs1 = rd
                            3'b001,                        // funct3 = SLL
                            ci_rd[4:0],                    // rd
                            7'b0010011                     // opcode = OP-IMM
                        };
                    end
                    
                    // C.LWSP: Load word from stack pointer
                    // Decompresses to: LW rd, offset(x2)
                    3'b010: begin
                        if (ci_rd == 5'd0) begin
                            // Reserved
                            instr_32bit = INSTR_INVALID;
                            is_valid = 1'b0;
                        end else begin
                            instr_32bit = {
                                {4'b0000},                     // imm[11:8] = zero-extend
                                ci_imm8[7:0],                  // imm[7:0] = cl_imm[6:0]
                                5'd2,                          // rs1 = x2 (stack pointer)
                                3'b010,                        // funct3 = LW
                                ci_rd[4:0],                    // rd
                                7'b0000011                     // opcode = LOAD
                            };
                        end
                    end
                    
                    // C.JR, C.MV, C.JALR, C.ADDI, C.EBREAK
                    3'b100: begin
                        if (instr_16bit[12] == 1'b0) begin
                            if (cr_rs2 == 5'd0) begin
                                if (cr_rs1 == 5'd0) begin
                                    // Reserved
                                    instr_32bit = INSTR_INVALID;
                                    is_valid = 1'b0;
                                end else begin
                                    // C.JR: Jump register
                                    // Decompresses to: JALR x0, 0(rs1)
                                    instr_32bit = {
                                        12'b0,                  // imm = 0
                                        cr_rs1[4:0],            // rs1
                                        3'b000,                 // funct3 = JALR
                                        5'd0,                   // rd = x0
                                        7'b1100111              // opcode = JALR
                                    };
                                end
                            end else begin
                                // Note: not sure C.MV with rs1 = x0 is valid or not
                                // C.MV: Move register
                                // Decompresses to: ADD rd, x0, rs2
                                instr_32bit = {
                                    7'b0000000,             // funct7
                                    cr_rs2[4:0],            // rs2 = rs2'
                                    5'd0,                   // rs1 = x0
                                    3'b000,                 // funct3 = ADD
                                    cr_rd[4:0],             // rd = rd'
                                    7'b0110011              // opcode = OP-IMM
                                };
                            end
                        end else begin
                            if (cr_rs2 == 5'd0) begin
                                if (cr_rs1 == 5'd0) begin
                                    instr_32bit = 32'h00100073; // EBREAK
                                end else begin
                                    // C.JALR: Jump and link register
                                    // Decompresses to: JALR x1, 0(rs1)
                                    instr_32bit = {
                                        7'b0000000,             // funct7
                                        cr_rs1[4:0],            // rs1
                                        3'b000,                 // funct3 = ADD
                                        5'd1,                   // rd = x1
                                        7'b1100111              // opcode = JALR
                                    };
                                end
                            end else begin
                                // Note: not sure C.ADD with rs1 = x0 is valid or not
                                // C.ADD
                                // Decompresses to: ADD rd, rd, rs2
                                instr_32bit = {
                                    7'b0000000,             // funct7
                                    cr_rs2[4:0],            // rs2
                                    cr_rd[4:0],             // rd
                                    3'b000,                 // funct3 = ADD
                                    cr_rd[4:0],             // rd
                                    7'b0110011              // opcode = OP
                                };
                            end
                        end
                    end
                    
                    // C.SWSP: Store word to stack pointer
                    // Decompresses to: SW rs2, offset[7:2](x2)
                    3'b110: begin
                        // imm = {instr[8:7], instr[12:9], 2'b00}
                        instr_32bit = {
                            {4'b0000},                         // Upper bits
                            css_imm[7:5],                      //
                            css_rs2[4:0],                      // rs2
                            5'd2,                              // rs1 = x2 (stack pointer)
                            3'b010,                            // funct3 = SW
                            css_imm[4:0],                      // 
                            7'b0100011                         // opcode = STORE
                        };
                    end

                    default: begin
                        instr_32bit = INSTR_INVALID;
                        is_valid = 1'b0;
                    end
                endcase
            end

            // Invalid opcode (should be 2'b11, but that's reserved)
            default: begin
                instr_32bit = INSTR_INVALID;
                is_valid = 1'b0;
            end
        endcase
    end

endmodule

/* RV32I Core - Main processor module */

/*
    5-Stage Pipeline
    IF (Instruction Fetch): Fetches instructions from memory
    ID (Instruction Decode): Decodes instructions and reads registers
    EX (Execute): Performs ALU operations
    MEM (Memory): Handles memory access
    WB (Writeback): Writes results back to registers
*/

`include "debug_defines.vh"

module rv32i_core #(
    parameter RESET_ADDR = 32'h00000000
) (
    input wire clk,
    input wire rst_n,
    
    // Memory interface
    input wire [31:0] i_instr_data,    // Instruction from memory
    input wire [31:0] i_mem_data,      // Data from memory
    input wire i_instr_ready,          // Instruction memory ready signal
    input wire i_mem_ready,            // Data memory ready signal
    output wire [31:0] o_instr_addr,   // Instruction address
    output wire [31:0] o_mem_addr,     // Memory address
    output wire [31:0] o_mem_wdata,    // Data to write to memory
    output wire [2:0] o_mem_flag,      // funct3 from store instruction: 000=SB, 001=SH, 010=SW
    output wire o_mem_we,              // Memory write enable
    output wire o_mem_re,              // Memory read enable

    output wire [47:0] o_mtime,

    // Interrupt interface
    input wire i_timer_interrupt,       // Machine timer interrupt (MTIP)

    output wire o_error_flag            // Error flag
);

    localparam INSTR_NOP = 32'h00000013;
    localparam PC_FLUSH_ADDR = 32'h00FFFFFF;
    localparam MASK_MCAUSE = 32'h8000000F;
    localparam MASK_ADDR = 32'h00FFFFFF;
    localparam INT_CAUSE_TIMER = 32'h80000007;

    // RISC-V Opcodes
    localparam OPCODE_R        = 7'b0110011;  // R-type: ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND
    localparam OPCODE_I        = 7'b0010011;  // I-type ALU: ADDI, SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI
    localparam OPCODE_L        = 7'b0000011;  // I-type Load: LB, LH, LW, LBU, LHU
    localparam OPCODE_S        = 7'b0100011;  // S-type Store: SB, SH, SW
    localparam OPCODE_B        = 7'b1100011;  // B-type Branch: BEQ, BNE, BLT, BGE, BLTU, BGEU
    localparam OPCODE_JAL      = 7'b1101111;  // J-type: JAL
    localparam OPCODE_JALR     = 7'b1100111;  // I-type: JALR
    localparam OPCODE_LUI      = 7'b0110111;  // U-type: LUI
    localparam OPCODE_AUIPC    = 7'b0010111;  // U-type: AUIPC
    localparam OPCODE_SYSTEM   = 7'b1110011;  // I-type System: ECALL, EBREAK, MRET, CSR*
    localparam OPCODE_FENCE    = 7'b0001111;  // I-type: FENCE

    // Pipeline registers
    reg [31:0] if_instr, if_pc;

    reg [31:0] id_instr, id_pc, id_rs1_data, id_rs2_data, id_imm;
    reg [3:0] id_alu_op;
    reg [31:0] id_alu_a, id_alu_b;

    reg [31:0] ex_instr, ex_pc, ex_rs1_data, ex_rs2_data, ex_alu_result;
    reg ex_mem_we, ex_mem_re, ex_reg_we;

    reg [31:0] pc;
    wire [31:0] pc_next;

    reg [31:0] mem_instr, mem_alu_result, mem_rs1_data, mem_rs2_data;
    reg [4:0] mem_rd_addr;
    reg mem_mem_we, mem_mem_re, mem_reg_we;

    reg error_flag_reg;

    reg [47:0] mtime_counter;


    // Memory stall signals
    reg mem_stall;

    // Instruction type signals
    wire if_is_i_type, if_is_s_type, if_is_b_type, if_is_j_type, if_is_u_type;

    // Instruction fields
    wire [6:0] if_opcode;
    wire [2:0] if_funct3;
    /* verilator lint_off UNUSEDSIGNAL */
    wire [6:0] if_funct7;
    wire [11:0] if_imm12;
    wire [31:0] if_imm, imm_i, imm_s, imm_b, imm_u, imm_j;

    wire [4:0] if_rs1_addr, if_rs2_addr;

    wire [31:0] if_rs1_data, if_rs2_data;

    wire [3:0] if_alu_op;
    wire [31:0] if_alu_a, if_alu_b;

    wire [6:0] id_opcode;
    wire [2:0] id_funct3;
    wire [11:0] id_imm12;
    wire id_mem_we, id_mem_re, id_reg_we;


    wire [6:0] ex_opcode;
    wire [4:0] ex_rd_addr;
    wire [2:0] ex_funct3;
    wire [6:0] ex_funct7;
    wire ex_is_valid_opcode;
    wire ex_is_branch;

    // Writeback result selection
    wire [6:0] mem_opcode;
    wire [4:0] _unused_mem_rd_addr;
    wire [2:0] mem_funct3;
    wire [31:0] mem_reg_wdata;
    wire [31:0] mem_value;

    // Control signals
    wire [31:0] alu_result;


    // CSR signals
    wire id_csr_we;
    wire mem_csr_we;
    wire [11:0] mem_csr_addr;
    wire [2:0] mem_csr_op;
    wire [31:0] mem_csr_wdata;
    wire [31:0] csr_rdata;
    wire csr_illegal;

    // Interrupt detection signals from CSR
    wire [31:0] csr_mip, csr_mie, csr_mstatus;

    // Exception handling signals
    wire id_is_ecall, id_is_ebreak, id_is_mret;
    reg ex_is_ecall, ex_is_ebreak, ex_is_mret;
    wire [31:0] mtvec, mepc;

    wire ex_is_exception;
    wire [31:0] ex_exception_cause;
    wire [31:0] ex_exception_pc;
    wire [31:0] ex_exception_value;

    wire exception_trigger, mret_trigger;
    wire [31:0] exception_cause;
    wire [31:0] exception_pc;
    wire [31:0] exception_value;

    // Interrupt handling signals
    reg id_int_is_interrupt;
    wire int_pending;
    wire int_enabled;
    wire int_is_interrupt;  // Interrupt detected in IF/ID stage
    wire [31:0] int_pc_next;

    // Instruction decoding
    assign if_opcode = if_instr[6:0];
    assign if_funct3 = if_instr[14:12];
    assign if_funct7 = if_instr[31:25];
    assign if_rs1_addr = if_instr[19:15];
    assign if_rs2_addr = if_instr[24:20];

    assign if_is_i_type = (if_opcode == OPCODE_I) || (if_opcode == OPCODE_L) || (if_opcode == OPCODE_JALR);
    assign if_is_s_type = (if_opcode == OPCODE_S);
    assign if_is_b_type = (if_opcode == OPCODE_B);
    assign if_is_j_type = (if_opcode == OPCODE_JAL);
    assign if_is_u_type = (if_opcode == OPCODE_LUI) || (if_opcode == OPCODE_AUIPC);

    // Immediate generation
    assign if_imm12 = if_instr[31:20];
    assign imm_i = {{20{if_imm12[11]}}, if_imm12};
    assign imm_s = {{20{if_instr[31]}}, if_instr[31:25], if_instr[11:7]};
    assign imm_b = {{20{if_instr[31]}}, if_instr[7], if_instr[30:25], if_instr[11:8], 1'b0};
    assign imm_u = {if_instr[31:12], 12'b0};
    assign imm_j = {{12{if_instr[31]}}, if_instr[19:12], if_instr[20], if_instr[30:21], 1'b0};

    assign if_imm = if_is_i_type ? imm_i :
                    if_is_s_type ? imm_s :
                    if_is_b_type ? imm_b :
                    if_is_j_type ? imm_j :
                    if_is_u_type ? imm_u :
                    32'd0;


    assign id_opcode = id_instr[6:0];
    assign id_funct3 = id_instr[14:12];
    assign id_imm12 = id_instr[31:20];

    assign ex_opcode = ex_instr[6:0];
    assign ex_funct3 = ex_instr[14:12];
    assign ex_funct7 = ex_instr[31:25];
    assign ex_rd_addr = ex_instr[11:7];

    assign mem_opcode = mem_instr[6:0];
    assign mem_funct3 = mem_instr[14:12];
    assign _unused_mem_rd_addr = mem_instr[11:7];

    // Instruction address
    assign o_instr_addr = pc;
    assign o_mtime = mtime_counter;

    // Register file instantiation
    rv32i_register register_file (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(if_rs1_addr),
        .rs2_addr(if_rs2_addr),
        .rs1_data(if_rs1_data),
        .rs2_data(if_rs2_data),
        .rd_addr(mem_rd_addr),
        .rd_data(mem_reg_wdata),
        .rd_we(mem_reg_we)
    );

    // ALU instantiation
    rv32i_alu alu (
        .op(id_alu_op),
        .a(id_alu_a),
        .b(id_alu_b),
        .result(alu_result)
    );

    // CSR module instantiation
    rv32i_csr csr_file (
        .clk(clk),
        .rst_n(rst_n),
        .csr_addr(mem_csr_addr),
        .csr_wdata(mem_csr_wdata),
        .csr_we(mem_csr_we),
        .csr_op(mem_csr_op),
        .csr_rdata(csr_rdata),
        .csr_illegal(csr_illegal),
        .mtime(mtime_counter),
        .exception_trigger(exception_trigger),
        .exception_cause(exception_cause),
        .exception_pc(exception_pc),
        .exception_value(exception_value),
        .mtvec_out(mtvec),
        .mret_trigger(mret_trigger),
        .mepc_out(mepc),
        .timer_interrupt(i_timer_interrupt),
        .mip_out(csr_mip),
        .mie_out(csr_mie),
        .mstatus_out(csr_mstatus)
    );

    // Interrupt detection logic
    // Interrupts are taken when:
    // 1. MIE (bit 3 of mstatus) is set (global interrupt enable)
    // 2. The specific interrupt is enabled in mie (MTIE = bit 7 for timer)
    // 3. The interrupt is pending in mip (MTIP = bit 7 for timer)
    // 4. No exception is being handled
    // 5. We're not in the middle of handling an exception or interrupt

    // Check for timer interrupt (MTIP = bit 7 of mip, MTIE = bit 7 of mie)
    wire int_timer_pending = csr_mip[7] && csr_mie[7];  // MIE bit

    // Interrupt is pending if any enabled interrupt is pending
    assign int_pending = int_timer_pending;
    assign int_enabled = csr_mstatus[3];  // MIE bit

    // Only handle interrupt when there is no memory stall, exception, or interrupt is already being handled
    // Also make sure to handle interrupt only if if_pc is a valid address,
    // otherwise, we can not return to the correct address after interrupt is handled
    // Note that we detect timer interrupt in IF, but handle it in ID to cut critical path
    assign int_is_interrupt = int_pending && int_enabled
                                && (if_pc != PC_FLUSH_ADDR);
                                // && !mem_stall
                                // && !exception_trigger;
    assign int_pc_next = id_pc;  // PC of instruction that would execute next

    assign ex_is_valid_opcode = (ex_opcode == OPCODE_R)       // R-type
                            || (ex_opcode == OPCODE_I)       // I-type ALU
                            || (ex_opcode == OPCODE_L)       // I-type Load
                            || (ex_opcode == OPCODE_S)       // S-type Store
                            || (ex_opcode == OPCODE_B)       // B-type Branch
                            || (ex_opcode == OPCODE_JAL)     // J-type JAL
                            || (ex_opcode == OPCODE_JALR)    // I-type JALR
                            || (ex_opcode == OPCODE_LUI)     // U-type LUI
                            || (ex_opcode == OPCODE_AUIPC)   // U-type AUIPC
                            || (ex_opcode == OPCODE_SYSTEM)  // I-type System (CSR, ECALL, EBREAK, MRET)
                            || (ex_opcode == OPCODE_FENCE);  // I-type FENCE

    assign o_error_flag = error_flag_reg;

    // ECALL detection (opcode OPCODE_SYSTEM, funct3 == 3'b000, imm12 == 12'h000)
    assign id_is_ecall = (id_opcode == OPCODE_SYSTEM) && (id_funct3 == 3'b000) && (id_imm12 == 12'h000);
    
    // EBREAK detection (opcode OPCODE_SYSTEM, funct3 == 3'b000, imm12 == 12'h001)
    assign id_is_ebreak = (id_opcode == OPCODE_SYSTEM) && (id_funct3 == 3'b000) && (id_imm12 == 12'h001);
    
    // MRET detection (opcode OPCODE_SYSTEM, funct3 == 3'b000, imm12 == 12'h302)
    assign id_is_mret = (id_opcode == OPCODE_SYSTEM) && (id_funct3 == 3'b000) && (id_imm12 == 12'h302);

    // CSR instruction detection
    assign id_csr_we = (id_opcode == OPCODE_SYSTEM) && (id_funct3 != 3'b000); // CSR instructions (not ECALL/EBREAK)
    assign mem_csr_we = (mem_opcode == OPCODE_SYSTEM) && (mem_funct3 != 3'b000); // CSR instructions (not ECALL/EBREAK)
    assign mem_csr_addr = mem_instr[31:20];  // CSR address (12 bits)
    assign mem_csr_op = mem_funct3;  // CSR operation type

    // Control unit
    wire alu_i_type_bit;
    assign alu_i_type_bit = (if_funct3 == 3'b101) ? if_funct7[5] : 1'b0;
    assign if_alu_op = (if_opcode == OPCODE_R     ) ? {if_funct7[5], if_funct3} :    // R-type
                        (if_opcode == OPCODE_I    ) ? {alu_i_type_bit, if_funct3} :  // I-type (ALU)
                        (if_opcode == OPCODE_L    ) ? 4'b0000 :                      // I-type (Load) - ADD for address
                        (if_opcode == OPCODE_S    ) ? 4'b0000 :                      // S-type (Store) - ADD for address
                        (if_opcode == OPCODE_JAL  ) ? 4'b0000 :                      // J-type (JAL)
                        (if_opcode == OPCODE_JALR ) ? 4'b0000 :                      // I-type (JALR)
                        (if_opcode == OPCODE_LUI  ) ? 4'b0000 :                      // U-type (LUI)
                        (if_opcode == OPCODE_AUIPC) ? 4'b0000 :                      // U-type (AUIPC) - ADD
                        4'b1111; // default (NOP)

    // ALU operand A selection
    assign if_alu_a = (if_opcode == OPCODE_R      ) ? if_rs1_data :      // R-type (ALU)
                        (if_opcode == OPCODE_I    ) ? if_rs1_data :      // I-type (ALU)
                        (if_opcode == OPCODE_L    ) ? if_rs1_data :      // I-type (Load)
                        (if_opcode == OPCODE_S    ) ? if_rs1_data :      // S-type (Store)
                        (if_opcode == OPCODE_JAL  ) ? if_pc :            // J-type (JAL)
                        (if_opcode == OPCODE_JALR ) ? if_pc :            // I-type (JALR)
                        (if_opcode == OPCODE_LUI  ) ? 32'd0 :            // U-type (LUI)
                        (if_opcode == OPCODE_AUIPC) ? if_pc :            // U-type (AUIPC)
                        32'd0;

    // ALU operand B selection
    assign if_alu_b = (if_opcode == OPCODE_R      ) ? if_rs2_data :      // R-type (ALU)
                        (if_opcode == OPCODE_I    ) ? if_imm :           // I-type (ALU)
                        (if_opcode == OPCODE_L    ) ? if_imm :           // I-type (Load)
                        (if_opcode == OPCODE_S    ) ? if_imm :           // S-type (Store)
                        (if_opcode == OPCODE_JAL  ) ? 32'd4 :            // J-type (JAL)
                        (if_opcode == OPCODE_JALR ) ? 32'd4 :            // I-type (JALR)
                        (if_opcode == OPCODE_LUI  ) ? if_imm :           // U-type (LUI)
                        (if_opcode == OPCODE_AUIPC) ? if_imm :           // U-type (AUIPC)
                        32'd0;

    assign id_mem_we = (id_opcode == OPCODE_S) ? 1'b1 : 1'b0; // Only Store instructions write to memory

    assign id_mem_re = (id_opcode == OPCODE_L) ? 1'b1 : 1'b0; // Only Load instructions read from memory

    assign id_reg_we = (id_opcode == OPCODE_R      ) ? 1'b1 :  // R-type
                         (id_opcode == OPCODE_I    ) ? 1'b1 :  // I-type (ALU)
                         (id_opcode == OPCODE_L    ) ? 1'b1 :  // I-type (Load)
                         (id_opcode == OPCODE_JAL  ) ? 1'b1 :  // J-type (JAL)
                         (id_opcode == OPCODE_JALR ) ? 1'b1 :  // I-type (JALR)
                         (id_opcode == OPCODE_LUI  ) ? 1'b1 :  // U-type (LUI)
                         (id_opcode == OPCODE_AUIPC) ? 1'b1 :  // U-type (AUIPC)
                         (id_csr_we && (id_instr[11:7] != 5'd0)) ? 1'b1 :  // CSR instructions (if rd != 0)
                         1'b0; // default (Store, Branch, and others don't write to registers)

    // Memory interface
    assign o_mem_addr = mem_alu_result;
    assign o_mem_wdata = mem_rs2_data;
    assign o_mem_flag = mem_funct3;
    // Only access memory when instruction is ready
    assign o_mem_we = mem_mem_we;
    assign o_mem_re = mem_mem_re;
    
    assign mem_value = (mem_funct3 == 3'b000) ? {{24{i_mem_data[7]}}, i_mem_data[7:0]} :   // LB
                       (mem_funct3 == 3'b001) ? {{16{i_mem_data[15]}}, i_mem_data[15:0]} : // LH
                       (mem_funct3 == 3'b010) ? i_mem_data :                               // LW
                       (mem_funct3 == 3'b100) ? {{24'b0}, i_mem_data[7:0]} :               // LBU
                       (mem_funct3 == 3'b101) ? {{16'b0}, i_mem_data[15:0]} :              // LHU
                       0;

    // CSR write data selection (rs1 for register-based, immediate for immediate-based)
    // Note: For CSR instructions, rs1 is in bits [19:15], and for immediate versions, this is the immediate value
    assign mem_csr_wdata = (mem_csr_op[2]) ? {27'd0, mem_instr[19:15]} :  // Immediate versions (CSRRWI, CSRRSI, CSRRCI)
                            mem_rs1_data;  // Register versions (CSRRW, CSRRS, CSRRC) - uses rs1, not rs2
    
    assign mem_reg_wdata = (mem_opcode == OPCODE_L    ) ? mem_value :          // Load: use memory data
                            (mem_opcode == OPCODE_JAL ) ? mem_alu_result :     // JAL: return address
                            (mem_opcode == OPCODE_JALR) ? mem_alu_result :     // JALR: return address
                            (mem_opcode == OPCODE_LUI ) ? mem_alu_result :     // LUI: ALU result (immediate)
                            (mem_csr_we) ? csr_rdata :                         // CSR: use CSR read data
                            mem_alu_result;                                    // Others: ALU result

    // Branch hazard detection
    assign ex_is_branch = (ex_opcode == OPCODE_B) ||       // B-Type (BEQ, BNE, BLT, BGE)
                          (ex_opcode == OPCODE_JAL) ||     // JAL
                          (ex_opcode == OPCODE_JALR);      // JALR


    wire        id_sign_rs1 = id_rs1_data[31];
    wire        id_sign_rs2 = id_rs2_data[31];
    wire [31:0] id_diff     = id_rs1_data - id_rs2_data;

    wire        id_lt_s = (id_sign_rs1 ^ id_sign_rs2) ? id_sign_rs1 : id_diff[31]; // rs1 < rs2 (signed)
    wire        id_ge_s = ~id_lt_s;                                                // rs1 >= rs2 (signed)

    wire id_eq = (id_rs1_data == id_rs2_data);
    wire id_ne = ~id_eq;
    wire id_lt = (id_rs1_data < id_rs2_data);
    wire id_ge = ~id_lt;

    wire [31:0] pc_branch_taken = id_pc + id_imm;
    wire [31:0] pc_branch_not_taken = id_pc + 4;

    reg [31:0] ex_branch_target;
    // PC update logic
    wire [31:0] id_branch_target = (id_opcode == OPCODE_B) ? ( // Branch
                        (id_funct3 == 3'b000) ? ((id_eq) ? pc_branch_taken : pc_branch_not_taken) :   // BEQ
                        (id_funct3 == 3'b001) ? ((id_ne) ? pc_branch_taken : pc_branch_not_taken) :   // BNE
                        (id_funct3 == 3'b100) ? ((id_lt_s) ? pc_branch_taken : pc_branch_not_taken) : // BLT
                        (id_funct3 == 3'b101) ? ((id_ge_s) ? pc_branch_taken : pc_branch_not_taken) : // BGE
                        (id_funct3 == 3'b110) ? ((id_lt) ? pc_branch_taken : pc_branch_not_taken) :   // BLTU
                        (id_funct3 == 3'b111) ? ((id_ge) ? pc_branch_taken : pc_branch_not_taken) :   // BGEU
                        pc_branch_not_taken // default
                     ) :
                     (id_opcode == OPCODE_JAL) ? pc_branch_taken : // JAL
                     (id_opcode == OPCODE_JALR) ? (id_rs1_data + id_imm) & ~1 : // JALR
                     32'd0;
    wire [31:0] pc_target = ex_is_branch ? ex_branch_target : pc + 4;

    // Exception handling logic
    // Priority: misaligned address > ECALL > MRET

    // Check for instruction address misalignment
    // Instruction addresses must be aligned (divisible by 4, i.e., bits [1:0] must be 00)

    wire ex_is_misaligned = ex_is_branch && ex_branch_target[1:0] != 2'b00;

    // Check for load/store address misalignment in EX stage
    // Alignment requirements:
    // - LW/SW: address[1:0] must be 00 (4-byte aligned)
    // - LH/SH: address[0] must be 0 (2-byte aligned)
    // - LB/SB: no alignment requirement
    wire ex_is_load = (ex_opcode == OPCODE_L);
    wire ex_is_store = (ex_opcode == OPCODE_S);

    // Check alignment for load instructions
    wire ex_load_misaligned = ex_is_load && (
        (ex_funct3 == 3'b010 && ex_alu_result[1:0] != 2'b00) ||  // LW: must be 4-byte aligned
        (ex_funct3 == 3'b001 && ex_alu_result[0] != 1'b0) ||     // LH: must be 2-byte aligned
        (ex_funct3 == 3'b101 && ex_alu_result[0] != 1'b0)        // LHU: must be 2-byte aligned
    );
    
    // Check alignment for store instructions
    wire ex_store_misaligned = ex_is_store && (
        (ex_funct3 == 3'b010 && ex_alu_result[1:0] != 2'b00) ||  // SW: must be 4-byte aligned
        (ex_funct3 == 3'b001 && ex_alu_result[0] != 1'b0)        // SH: must be 2-byte aligned
    );

    wire ex_is_illegal_instruction = !ex_is_valid_opcode;
    // Exception priority: misaligned address > illegal instruction > ECALL > EBREAK
    assign ex_is_exception = ex_is_misaligned || ex_is_illegal_instruction || ex_load_misaligned || ex_store_misaligned || ex_is_ecall || ex_is_ebreak;

    assign ex_exception_cause = ex_is_misaligned ? 32'd0 :             // CAUSE_INSTRUCTION_ADDRESS_MISALIGNED = 0
                                  ex_load_misaligned ? 32'd4 :         // CAUSE_LOAD_ADDRESS_MISALIGNED = 4
                                  ex_store_misaligned ? 32'd6 :        // CAUSE_STORE_ADDRESS_MISALIGNED = 6
                                  ex_is_illegal_instruction ? 32'd2 :  // CAUSE_ILLEGAL_INSTRUCTION = 2
                                  ex_is_ecall ? 32'd11 :               // CAUSE_MACHINE_ECALL = 11
                                  ex_is_ebreak ? 32'd3 :               // CAUSE_BREAKPOINT = 3
                                  32'd0;
    assign ex_exception_pc = ex_is_exception ? ex_pc : 32'd0;
    assign ex_exception_value = ex_is_misaligned ? pc_target :          // mtval = misaligned target address
                                  ex_is_illegal_instruction ? ex_instr :  // mtval = instruction code for illegal instruction
                                  ex_load_misaligned ? ex_alu_result :    // mtval = misaligned effective address for load
                                  ex_store_misaligned ? ex_alu_result :   // mtval = misaligned effective address for store
                                  ex_is_ecall ? 32'd0 :                   // mtval is 0 for ECALL
                                  ex_is_ebreak ? ex_pc :                  // mtval is pc for EBREAK
                                  32'd0;

    assign exception_trigger = ex_is_exception || id_int_is_interrupt;
    assign exception_cause = (ex_is_exception ? ex_exception_cause : INT_CAUSE_TIMER) & MASK_MCAUSE;
    assign exception_pc = ex_is_exception ? ex_exception_pc : int_pc_next;
    assign exception_value = ex_is_exception ? ex_exception_value : 32'd0;
    assign mret_trigger = ex_is_mret;

    // Exception handling takes priority - redirect to mtvec when exception occurs
    // MRET takes priority - redirect to mepc when mret occurs
    assign pc_next = (ex_is_mret) ? mepc :                            // MRET: jump to mepc
                     (ex_is_exception || id_int_is_interrupt) ? mtvec :  // jump to exception handler
                     pc_target;


    // Pipeline stages
    /* verilator lint_off SYNCASYNCNET */
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all pipeline registers
            pc <= RESET_ADDR & MASK_ADDR;
            if_instr <= INSTR_NOP;
            if_pc <= RESET_ADDR & MASK_ADDR;

            id_instr <= INSTR_NOP;
            id_pc <= RESET_ADDR & MASK_ADDR;
            id_rs1_data <= 32'd0;
            id_rs2_data <= 32'd0;
            id_imm <= 32'd0;
            id_alu_op <= 4'b0000;
            id_alu_a <= 32'd0;
            id_alu_b <= 32'd0;
            id_int_is_interrupt <= 1'b0;

            ex_instr <= INSTR_NOP;
            ex_rs1_data <= 32'd0;
            ex_rs2_data <= 32'd0;
            ex_alu_result <= 32'd0;
            ex_pc <= RESET_ADDR & MASK_ADDR;
            ex_mem_we <= 1'b0;
            ex_mem_re <= 1'b0;
            ex_reg_we <= 1'b0;
            ex_is_ecall <= 1'b0;
            ex_is_ebreak <= 1'b0;
            ex_is_mret <= 1'b0;
            ex_branch_target <= 32'd0;

            mem_alu_result <= 32'd0;
            mem_rs1_data <= 32'd0;
            mem_rs2_data <= 32'd0;
            mem_instr <= INSTR_NOP;
            mem_rd_addr <= 5'd0;
            mem_mem_we <= 1'b0;
            mem_mem_re <= 1'b0;
            mem_reg_we <= 1'b0;
            mem_stall <= 1'b0;

            error_flag_reg <= 1'b0;

            // Counters
            mtime_counter <= 48'd0;
            
            `DEBUG_PRINT(("=== RV32I Core Reset ==="));
        end else begin
            mtime_counter <= mtime_counter + 1;

            // Hazard handling logic:
            // * Data memory stall
            //     + Stall pipeline at memory stage when data memory is not ready
            // * Branch hazard
            // * Data hazard
            // * Instruction memory not ready
            //     This core is designed to use with qspi instruction memory, so each instruction takes at least 8 cycles to be fetched
            //     So we don't neet to handle data hazard and branch hazard,
            //     because all instructions will finish executing before the next instruction is fetched

            if (mem_stall) begin
                `DEBUG_PRINT(("Time %0t: MEM_STALL, mem_stall=%b", $time, mem_stall));
                // Stall pipeline
                if (mem_stall) begin
                    // Only keep we and re signals for 1 cycle
                    // When the instruction is ready, we start accessing memory (above code) and clear these signals here
                    mem_mem_we <= 1'b0;
                    mem_mem_re <= 1'b0;
                end
                if (i_mem_ready) begin
                    mem_stall <= 1'b0;
                end
            end else begin
                // Pipeline stage 1: Instruction Fetch
                if (!i_instr_ready || ex_is_branch || ex_is_exception || id_int_is_interrupt || ex_is_mret) begin
                    // If instruction is not ready or ex_is_branch is detected or exception or interrupt or mret is detected,
                    // keep the same instruction in IF/ID stage, don't increment PC
                    // `DEBUG_PRINT(("Time %0t: Keep current IF/ID stage, i_instr_ready=%b, ex_is_branch=%b, ex_is_exception=%b, id_int_is_interrupt=%b, ex_is_mret=%b",
                    //             $time, i_instr_ready, ex_is_branch, ex_is_exception, id_int_is_interrupt, ex_is_mret));
                    if_instr <= INSTR_NOP;
                    if_pc <= PC_FLUSH_ADDR & MASK_ADDR;

                    if (ex_is_branch || ex_is_exception || id_int_is_interrupt || ex_is_mret) begin
                        `DEBUG_PRINT(("Time %0t: Update pc to branch target pc=0x%h", $time, pc_next));
                        pc <= pc_next & MASK_ADDR;
                    end
                end else begin
                    // Normal execution: update pc and instruction
                    pc <= pc_next & MASK_ADDR;
                    if_instr <= i_instr_data;
                    if_pc <= pc & MASK_ADDR;
                end

                if (!error_flag_reg) begin
                    if (ex_is_valid_opcode == 1'b0) begin
                        `DEBUG_PRINT(("Time %0t: Invalid if_opcode: %b, instr=0x%h, pc=0x%h", $time, ex_opcode, ex_instr, pc - 8));
                    end
                    error_flag_reg <= !ex_is_valid_opcode;
                end

                // Pipeline stage 2: Instruction Decode
                id_instr <= if_instr;
                id_pc <= if_pc & MASK_ADDR;
                id_rs1_data <= if_rs1_data;
                id_rs2_data <= if_rs2_data;
                id_imm <= if_imm;
                id_alu_op <= if_alu_op;
                id_alu_a <= if_alu_a;
                id_alu_b <= if_alu_b;
                id_int_is_interrupt <= int_is_interrupt;

                // If exception, interrupt, or mret is detected, flush ID/EX stage with NOP
                if (int_is_interrupt) begin
                    `DEBUG_PRINT(("Time %0t: ID - Flushing with NOP, int_is_interrupt=%b", $time, int_is_interrupt));
                    id_instr <= INSTR_NOP;
                    // Don't flush PC here, because it is used as exception PC
                    // It will be flushed in the Execute stage
                    // id_pc <= PC_FLUSH_ADDR;
                    id_rs1_data <= 32'd0;
                    id_rs2_data <= 32'd0;
                    id_imm <= 32'd0;
                    id_alu_op <= 4'b0000;
                    id_alu_a <= 32'd0;
                    id_alu_b <= 32'd0;
                end

                // Pipeline stage 3: Execute
                ex_instr <= id_instr;
                ex_rs1_data <= id_rs1_data;
                ex_rs2_data <= id_rs2_data;
                ex_alu_result <= alu_result;
                ex_pc <= id_pc & MASK_ADDR;
                ex_mem_we <= id_mem_we;
                ex_mem_re <= id_mem_re;
                ex_reg_we <= id_reg_we;
                ex_is_ecall <= id_is_ecall;
                ex_is_ebreak <= id_is_ebreak;
                ex_is_mret <= id_is_mret;
                ex_branch_target <= id_branch_target;

                if (id_int_is_interrupt) begin
                    ex_pc <= PC_FLUSH_ADDR & MASK_ADDR;
                end

                // Pipeline stage 4: Memory
                mem_alu_result <= ex_alu_result;
                mem_rs1_data <= ex_rs1_data;
                mem_rs2_data <= ex_rs2_data;
                mem_instr <= ex_instr;
                mem_rd_addr <= ex_rd_addr;
                // Disable memory write/read when exception occurs (for store/load misalignment)
                mem_mem_we <= ex_mem_we && !ex_is_exception;
                mem_mem_re <= ex_mem_re && !ex_is_exception;
                // Disable register write when exception occurs
                mem_reg_we <= ex_reg_we && !ex_is_exception;

                // Only set mem_stall if memory access is needed and no exception occurred
                if ((ex_mem_we || ex_mem_re) && !ex_is_exception) begin
                    mem_stall <= 1'b1;
                end


            end // !mem_stall
        end // rst_n
    end // always block

`ifdef SIMULATION
    // Function to decode instruction and return human-readable string
    function automatic string decode_instruction(input [31:0] instr);
        reg [6:0] opcode;
        reg [2:0] funct3;
        reg [6:0] funct7;
        reg [4:0] rd, rs1, rs2;
        reg [11:0] imm12;
        reg [31:0] imm_i, imm_s, imm_b, imm_u, imm_j;
        string result;
        
        // Extract instruction fields
        opcode = instr[6:0];
        rd = instr[11:7];
        funct3 = instr[14:12];
        rs1 = instr[19:15];
        rs2 = instr[24:20];
        funct7 = instr[31:25];
        imm12 = instr[31:20];
        
        // Generate immediate values
        imm_i = {{20{imm12[11]}}, imm12};
        imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};
        imm_b = {{20{instr[31]}}, instr[7], instr[30:25], instr[11:8], 1'b0};
        imm_u = {instr[31:12], 12'b0};
        imm_j = {{12{instr[31]}}, instr[19:12], instr[20], instr[30:21], 1'b0};
        
        // Decode based on opcode
        case (opcode)
            OPCODE_R: begin // R-type instructions
                case ({funct7[5], funct3})
                    4'b0000: result = $sformatf("ADD x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b1000: result = $sformatf("SUB x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b0001: result = $sformatf("SLL x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b0010: result = $sformatf("SLT x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b0011: result = $sformatf("SLTU x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b0100: result = $sformatf("XOR x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b0101: result = $sformatf("SRL x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b1101: result = $sformatf("SRA x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b0110: result = $sformatf("OR x%0d, x%0d, x%0d", rd, rs1, rs2);
                    4'b0111: result = $sformatf("AND x%0d, x%0d, x%0d", rd, rs1, rs2);
                    default: result = $sformatf("UNKNOWN_R x%0d, x%0d, x%0d (funct3=%b, funct7=%b)", rd, rs1, rs2, funct3, funct7);
                endcase
            end
            
            OPCODE_I: begin // I-type ALU instructions
                case (funct3)
                    3'b000: result = $sformatf("ADDI x%0d, x%0d, 0x%0h", rd, rs1, $signed(imm_i));
                    3'b001: result = $sformatf("SLLI x%0d, x%0d, 0x%0h", rd, rs1, imm_i[4:0]);
                    3'b010: result = $sformatf("SLTI x%0d, x%0d, 0x%0h", rd, rs1, $signed(imm_i));
                    3'b011: result = $sformatf("SLTIU x%0d, x%0d, 0x%0h", rd, rs1, imm_i);
                    3'b100: result = $sformatf("XORI x%0d, x%0d, 0x%0h", rd, rs1, $signed(imm_i));
                    3'b101: begin
                        if (funct7[5]) 
                            result = $sformatf("SRAI x%0d, x%0d, 0x%0h", rd, rs1, imm_i[4:0]);
                        else 
                            result = $sformatf("SRLI x%0d, x%0d, 0x%0h", rd, rs1, imm_i[4:0]);
                    end
                    3'b110: result = $sformatf("ORI x%0d, x%0d, 0x%0h", rd, rs1, $signed(imm_i));
                    3'b111: result = $sformatf("ANDI x%0d, x%0d, 0x%0h", rd, rs1, $signed(imm_i));
                    default: result = $sformatf("UNKNOWN_I_ALU x%0d, x%0d, 0x%0h (funct3=%b)", rd, rs1, $signed(imm_i), funct3);
                endcase
            end
            
            OPCODE_L: begin // Load instructions
                case (funct3)
                    3'b000: result = $sformatf("LB x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    3'b001: result = $sformatf("LH x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    3'b010: result = $sformatf("LW x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    3'b100: result = $sformatf("LBU x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    3'b101: result = $sformatf("LHU x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    default: result = $sformatf("UNKNOWN_LOAD x%0d, 0x%0h(x%0d) (funct3=%b)", rd, $signed(imm_i), rs1, funct3);
                endcase
            end
            
            OPCODE_S: begin // Store instructions
                case (funct3)
                    3'b000: result = $sformatf("SB x%0d, 0x%0h(x%0d)", rs2, $signed(imm_s), rs1);
                    3'b001: result = $sformatf("SH x%0d, 0x%0h(x%0d)", rs2, $signed(imm_s), rs1);
                    3'b010: result = $sformatf("SW x%0d, 0x%0h(x%0d)", rs2, $signed(imm_s), rs1);
                    default: result = $sformatf("UNKNOWN_STORE x%0d, 0x%0h(x%0d) (funct3=%b)", rs2, $signed(imm_s), rs1, funct3);
                endcase
            end
            
            OPCODE_B: begin // Branch instructions
                case (funct3)
                    3'b000: result = $sformatf("BEQ x%0d, x%0d, 0x%0h", rs1, rs2, $signed(imm_b));
                    3'b001: result = $sformatf("BNE x%0d, x%0d, 0x%0h", rs1, rs2, $signed(imm_b));
                    3'b100: result = $sformatf("BLT x%0d, x%0d, 0x%0h", rs1, rs2, $signed(imm_b));
                    3'b101: result = $sformatf("BGE x%0d, x%0d, 0x%0h", rs1, rs2, $signed(imm_b));
                    3'b110: result = $sformatf("BLTU x%0d, x%0d, 0x%0h", rs1, rs2, $signed(imm_b));
                    3'b111: result = $sformatf("BGEU x%0d, x%0d, 0x%0h", rs1, rs2, $signed(imm_b));
                    default: result = $sformatf("UNKNOWN_BRANCH x%0d, x%0d, 0x%0h (funct3=%b)", rs1, rs2, $signed(imm_b), funct3);
                endcase
            end
            
            OPCODE_JAL: begin // JAL
                result = $sformatf("JAL x%0d, 0x%0h", rd, $signed(imm_j));
            end
            
            OPCODE_JALR: begin // JALR
                result = $sformatf("JALR x%0d, x%0d, 0x%0h", rd, rs1, $signed(imm_i));
            end
            
            OPCODE_LUI: begin // LUI
                result = $sformatf("LUI x%0d, 0x%h", rd, imm_u);
            end
            
            OPCODE_AUIPC: begin // AUIPC
                result = $sformatf("AUIPC x%0d, 0x%h", rd, imm_u);
            end
            
            OPCODE_SYSTEM: begin // System instructions
                case (funct3)
                    3'b000: begin
                        case (imm12)
                            12'h000: result = "ECALL";
                            12'h001: result = "EBREAK";
                            12'h302: result = "MRET";
                            default: result = $sformatf("UNKNOWN_SYSTEM (imm12=0x%h)", imm12);
                        endcase
                    end
                    3'b001: begin // CSRRW
                        result = $sformatf("CSRRW x%0d, 0x%h, x%0d", rd, instr[31:20], rs1);
                    end
                    3'b010: begin // CSRRS
                        result = $sformatf("CSRRS x%0d, 0x%h, x%0d", rd, instr[31:20], rs1);
                    end
                    3'b011: begin // CSRRC
                        result = $sformatf("CSRRC x%0d, 0x%h, x%0d", rd, instr[31:20], rs1);
                    end
                    3'b101: begin // CSRRWI
                        result = $sformatf("CSRRWI x%0d, 0x%h, 0x%h", rd, instr[31:20], rs1);
                    end
                    3'b110: begin // CSRRSI
                        result = $sformatf("CSRRSI x%0d, 0x%h, 0x%h", rd, instr[31:20], rs1);
                    end
                    3'b111: begin // CSRRCI
                        result = $sformatf("CSRRCI x%0d, 0x%h, 0x%h", rd, instr[31:20], rs1);
                    end
                    default: result = $sformatf("UNKNOWN_SYSTEM (funct3=%b)", funct3);
                endcase
            end
            
            OPCODE_FENCE: begin // FENCE
                result = "FENCE";
            end
            
            default: result = $sformatf("UNKNOWN_OPCODE 0x%h (opcode=%b)", instr, opcode);
        endcase
        
        return result;
    endfunction

    // Debug logging with $display statements
    always @(posedge clk) begin
        string if_instr_str, id_instr_str, ex_instr_str, mem_instr_str;
        if_instr_str = decode_instruction(if_instr);
        id_instr_str = decode_instruction(id_instr);
        ex_instr_str = decode_instruction(ex_instr);
        mem_instr_str = decode_instruction(mem_instr);

        // if (!mem_stall) begin
        if (if_pc != PC_FLUSH_ADDR || id_pc != PC_FLUSH_ADDR || ex_pc != PC_FLUSH_ADDR || mem_instr != INSTR_NOP) begin

        if (if_pc != PC_FLUSH_ADDR) begin
            // Log instruction fetch
            `DEBUG_PRINT(("Time %0t: IF - PC=0x%h, Instr=0x%h (%s), rs1=0x%d(0x%h), rs2=0x%d(0x%h), i_instr_ready=%b, PC_next=0x%h",
                        $time, if_pc, if_instr, if_instr_str, if_rs1_addr, if_rs1_data, if_rs2_addr, if_rs2_data, i_instr_ready, pc_next));
        end

        if (id_pc != PC_FLUSH_ADDR) begin
            // Log instruction decode and register reads
            `DEBUG_PRINT(("Time %0t: ID - PC=0x%h, Instr=0x%h (%s), rs1=0x%h, rs2=0x%h",
                        $time, id_pc, id_instr, id_instr_str, id_rs1_data, id_rs2_data));

            // Log ALU operations
            if (id_alu_op != 4'b1111 && (id_instr != 32'h00000013)) begin
                `DEBUG_PRINT(("Time %0t: ALU - ID: op=0x%h, a=0x%h, b=0x%h, result=0x%h, rs1=0x%h, rs2=0x%h", 
                            $time, id_alu_op, id_alu_a, id_alu_b, alu_result, id_rs1_data, id_rs2_data));
            end else begin
                `DEBUG_PRINT(("Time %0t: ALU - NOP", $time));
            end
        end

        if (ex_pc != PC_FLUSH_ADDR) begin
            `DEBUG_PRINT(("Time %0t: EX - PC=0x%h, Instr=0x%h (%s)", 
                        $time, ex_pc, ex_instr, ex_instr_str));
        end

        if (mem_instr != INSTR_NOP) begin
            `DEBUG_PRINT(("Time %0t: MEM - PC=0x________, Instr=0x%h (%s)", 
                        $time, mem_instr, mem_instr_str));

            // Log memory operations
            if (mem_mem_we) begin
                `DEBUG_PRINT(("Time %0t: MEM - Store: addr=0x%h, data=0x%h", 
                        $time, mem_alu_result, mem_rs2_data));
            end
            if (mem_mem_re) begin
                `DEBUG_PRINT(("Time %0t: MEM - Load: addr=0x%h, i_mem_data=0x%h, mem_reg_wdata=0x%h", 
                        $time, mem_alu_result, i_mem_data, mem_reg_wdata));
            end
            if (!mem_mem_we && !mem_mem_re) begin
                `DEBUG_PRINT(("Time %0t: MEM - Non-Memory Operation", $time));
            end
            // Log register writes
            if (mem_reg_we) begin
                if (mem_rd_addr != 5'd0) begin
                    `DEBUG_PRINT(("Time %0t: MEM - Reg Write: x%d = 0x%h", 
                                $time, mem_rd_addr, mem_reg_wdata));
                end
            end
        end
        
        // Log branches and jumps
        if (ex_opcode == OPCODE_B) begin
            case (ex_funct3)
                3'b000: `DEBUG_PRINT(("Time %0t: BRANCH - BEQ: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_rs1_data, id_rs2_data, id_eq));
                3'b001: `DEBUG_PRINT(("Time %0t: BRANCH - BNE: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_rs1_data, id_rs2_data, id_ne));
                3'b100: `DEBUG_PRINT(("Time %0t: BRANCH - BLT: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_rs1_data, id_rs2_data, id_lt_s));
                3'b101: `DEBUG_PRINT(("Time %0t: BRANCH - BGE: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_rs1_data, id_rs2_data, id_ge_s));
                3'b110: `DEBUG_PRINT(("Time %0t: BRANCH - BLTU: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_rs1_data, id_rs2_data, id_lt));
                3'b111: `DEBUG_PRINT(("Time %0t: BRANCH - BGEU: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_rs1_data, id_rs2_data, id_ge));
            endcase
        end

        `DEBUG_PRINT(("--------------------------------"));

        end
    end
`endif

endmodule

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
    parameter RESET_ADDR = 32'h80000000  // Configurable reset address
) (
    input wire clk,
    input wire rst_n,
    
    // Memory interface
    input wire [31:0] instr_data,    // Instruction from memory
    input wire [31:0] mem_data,      // Data from memory
    input wire instr_ready,          // Instruction memory ready signal
    input wire mem_ready,            // Data memory ready signal
    output wire [31:0] instr_addr,   // Instruction address
    output wire [31:0] mem_addr,     // Memory address
    output wire [31:0] mem_wdata,    // Data to write to memory
    output wire [2:0] mem_flag,      // funct3 from store instruction: 000=SB, 001=SH, 010=SW
    output wire mem_we,              // Memory write enable
    output wire mem_re,              // Memory read enable

    output wire error_flag            // Error flag
);

    // Pipeline registers
    reg [31:0] if_id_instr, if_id_pc;

    reg [31:0] id_ex_instr, id_ex_pc, id_ex_imm;
    reg [4:0] id_ex_rs1_addr, id_ex_rs2_addr, id_ex_rd_addr;
    reg [3:0] id_ex_alu_op;
    reg id_ex_mem_we, id_ex_mem_re, id_ex_reg_we;
    reg id_ex_alu_a_forward_ex, id_ex_alu_b_forward_ex;
    reg [31:0] id_ex_alu_a_forwarded, id_ex_alu_b_forwarded;

    reg [31:0] pc;
    wire [31:0] pc_next;
    reg [31:0] pc_branch_taken, pc_branch_not_taken;
    reg [2:0] pc_id_ex_funct3;
    reg id_ex_rs1_forward_ex, id_ex_rs2_forward_ex;
    reg [31:0] id_ex_rs1_data_forwarded, id_ex_rs2_data_forwarded;


    reg [31:0] ex_mem_instr, ex_mem_result, ex_mem_rs2_data, ex_mem_pc;
    reg [4:0] ex_mem_rd_addr;
    reg ex_mem_mem_we, ex_mem_mem_re, ex_mem_reg_we;

    reg [31:0] mem_wb_result;
    reg [4:0] mem_wb_rd_addr;
    reg mem_wb_reg_we;

    reg [31:0] wb___result;
    reg [4:0] wb___rd_addr;
    reg wb___reg_we;

    reg error_flag_reg;

    // Instruction type signals
    wire if_id_is_r_type, if_id_is_i_type, if_id_is_s_type, if_id_is_b_type, if_id_is_j_type, if_id_is_u_type, if_id_is_risb_type, if_id_is_rsb_type;

    // Branch hazard signals
    wire branch_hazard;

    // Data hazard and forwarding signals
    wire [31:0] if_id_rs1_data_forwarded, if_id_rs2_data_forwarded;
    wire if_id_rs1_forward_id, if_id_rs2_forward_id, if_id_alu_b_forward_id, if_id_rs1_forward_ex, if_id_rs2_forward_ex;
    wire [31:0] if_id_alu_a_forwarded, if_id_alu_b_forwarded;

    // Load-use hazard signals
    wire load_use_hazard;

    // Memory stall signals
    reg mem_stall;

    // Instruction fields
    wire [6:0] if_id_opcode;
    wire [2:0] funct3;
    wire [6:0] funct7;
    wire [4:0] rd, if_id_rs1, if_id_rs2;
    wire [11:0] imm12;
    wire [31:0] if_id_imm, imm_i, imm_s, imm_b, imm_u, imm_j;
    wire [31:0] if_id_pc_branch_taken, if_id_pc_branch_not_taken;

    // Use to check data hazard
    wire [6:0] id_opcode;
    wire [4:0] id_rs1, id_rs2;
    wire is_valid_opcode;

    // Control signals
    wire [3:0] if_id_alu_op;
    wire [31:0] if_id_fixed_alu_a, if_id_fixed_alu_b;
    wire if_id_is_alu_a_fixed, if_id_is_alu_b_fixed;

    wire mem_we_ctrl, mem_re_ctrl, reg_we_ctrl;
    wire [31:0] alu_result;
    wire alu_zero, alu_negative, alu_overflow;

    // Register file connections
    wire [31:0] if_id_rs1_data, if_id_rs2_data;

    // ALU operand selection
    wire [31:0] id_ex_alu_a, id_ex_alu_b;

    // Instruction decoding
    assign if_id_opcode = if_id_instr[6:0];
    assign rd = if_id_instr[11:7];
    assign funct3 = if_id_instr[14:12];
    assign if_id_rs1 = if_id_instr[19:15];
    assign if_id_rs2 = if_id_instr[24:20];
    assign funct7 = if_id_instr[31:25];

    // Immediate generation
    assign imm12 = if_id_instr[31:20];
    assign imm_i = {{20{imm12[11]}}, imm12};
    assign imm_s = {{20{if_id_instr[31]}}, if_id_instr[31:25], if_id_instr[11:7]};
    assign imm_b = {{20{if_id_instr[31]}}, if_id_instr[7], if_id_instr[30:25], if_id_instr[11:8], 1'b0};
    assign imm_u = {if_id_instr[31:12], 12'b0};
    assign imm_j = {{12{if_id_instr[31]}}, if_id_instr[19:12], if_id_instr[20], if_id_instr[30:21], 1'b0};

    assign if_id_imm = (if_id_opcode == 7'b0010011) || (if_id_opcode == 7'b0000011) || (if_id_opcode == 7'b1100111) ? imm_i :
                    (if_id_opcode == 7'b0100011) ? imm_s :
                    (if_id_opcode == 7'b1100011) ? imm_b :
                    (if_id_opcode == 7'b1101111) ? imm_j :
                    (if_id_opcode == 7'b0110111) || (if_id_opcode == 7'b0010111) ? imm_u :
                    32'd0;
    assign if_id_pc_branch_taken = if_id_pc + if_id_imm;
    assign if_id_pc_branch_not_taken = if_id_pc + 4;

    assign id_opcode = id_ex_instr[6:0];
    assign id_rs1 = id_ex_instr[19:15];
    assign id_rs2 = id_ex_instr[24:20];

    // Instruction address
    assign instr_addr = pc;

    // Register file instantiation
    rv32i_register register_file (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(if_id_rs1),
        .rs2_addr(if_id_rs2),
        .rs1_data(if_id_rs1_data),
        .rs2_data(if_id_rs2_data),
        .rd_addr(mem_wb_rd_addr),
        .rd_data(mem_wb_result),
        .rd_we(mem_wb_reg_we)
    );

    // ALU instantiation
    rv32i_alu alu (
        .op(id_ex_alu_op),
        .a(id_ex_alu_a),
        .b(id_ex_alu_b),
        .result(alu_result)
        // .zero_flag(alu_zero),
        // .negative_flag(alu_negative),
        // .overflow_flag(alu_overflow)
    );

    assign is_valid_opcode = (id_opcode == 7'b0110011)
                            || (id_opcode == 7'b0010011)
                            || (id_opcode == 7'b0000011)
                            || (id_opcode == 7'b0100011)
                            || (id_opcode == 7'b1100011)
                            || (id_opcode == 7'b1101111)
                            || (id_opcode == 7'b1100111)
                            || (id_opcode == 7'b0110111)
                            || (id_opcode == 7'b0010111)
                            || (id_opcode == 7'b1110011);

    assign error_flag = error_flag_reg;

    assign if_id_is_r_type = (if_id_opcode == 7'b0110011);
    assign if_id_is_i_type = (if_id_opcode == 7'b0010011) || (if_id_opcode == 7'b0000011) || (if_id_opcode == 7'b1100111);
    assign if_id_is_s_type = (if_id_opcode == 7'b0100011);
    assign if_id_is_b_type = (if_id_opcode == 7'b1100011);
    assign if_id_is_j_type = (if_id_opcode == 7'b1101111);
    assign if_id_is_u_type = (if_id_opcode == 7'b0110111) || (if_id_opcode == 7'b0010111);
    assign if_id_is_risb_type = if_id_is_r_type || if_id_is_i_type || if_id_is_s_type || if_id_is_b_type;
    assign if_id_is_rsb_type = if_id_is_r_type || if_id_is_s_type || if_id_is_b_type;

    // Control unit
    wire alu_i_type_bit;
    assign alu_i_type_bit = (funct3 == 3'b101) ? funct7[5] : 1'b0;
    assign if_id_alu_op = (if_id_opcode == 7'b0110011) ? {funct7[5], funct3} :      // R-type
                    (if_id_opcode == 7'b0010011) ? {alu_i_type_bit, funct3} : // I-type (ALU)
                    (if_id_opcode == 7'b0000011) ? 4'b0000 :                       // I-type (Load) - ADD for address
                    (if_id_opcode == 7'b0100011) ? 4'b0000 :                       // S-type (Store) - ADD for address
                    (if_id_opcode == 7'b0110111) ? 4'b0000 :                       // U-type (LUI)
                    (if_id_opcode == 7'b0010111) ? 4'b0000 :                       // U-type (AUIPC) - ADD
                    4'b0000; // default (NOP)

    assign if_id_is_alu_a_fixed = (if_id_instr[6:0] == 7'b0010111)     // AUIPC
                            || (if_id_instr[6:0] == 7'b0110111);    // LUI
    assign if_id_fixed_alu_a = (if_id_instr[6:0] == 7'b0010111) ? if_id_pc : // AUIPC uses PC
                         (if_id_instr[6:0] == 7'b0110111) ? 0 :        // LUI uses 0
                         0;

    assign if_id_is_alu_b_fixed = (if_id_instr[6:0] == 7'b0010011)                  // I-type (ALU): use immediate
                            || (if_id_instr[6:0] == 7'b0000011)                  // I-type (Load): use immediate for address
                            || (if_id_instr[6:0] == 7'b0100011)                  // S-type (Store): use immediate for address
                            || (if_id_instr[6:0] == 7'b1101111)                  // J-type (JAL): use immediate
                            || (if_id_instr[6:0] == 7'b1100111)                  // I-type (JALR): use immediate
                            || (if_id_instr[6:0] == 7'b0110111)                  // U-type (LUI): use immediate
                            || (if_id_instr[6:0] == 7'b0010111);                  // U-type (AUIPC): use immediate
    assign if_id_fixed_alu_b = if_id_is_alu_b_fixed ? if_id_imm : 0;

    // ALU operand A selection - use forwarded data
    assign id_ex_alu_a = id_ex_alu_a_forward_ex ? ex_mem_result :
                        id_ex_alu_a_forwarded;
    
    // ALU operand B selection - use forwarded data
    assign id_ex_alu_b = id_ex_alu_b_forward_ex ? ex_mem_result :
                        id_ex_alu_b_forwarded;

    assign mem_we_ctrl = (if_id_opcode == 7'b0100011) ? 1'b1 : 1'b0; // Only Store instructions write to memory

    assign mem_re_ctrl = (if_id_opcode == 7'b0000011) ? 1'b1 : 1'b0; // Only Load instructions read from memory

    assign reg_we_ctrl = (if_id_opcode == 7'b0110011) ? 1'b1 :  // R-type
                         (if_id_opcode == 7'b0010011) ? 1'b1 :  // I-type (ALU)
                         (if_id_opcode == 7'b0000011) ? 1'b1 :  // I-type (Load)
                         (if_id_opcode == 7'b1101111) ? 1'b1 :  // J-type (JAL)
                         (if_id_opcode == 7'b1100111) ? 1'b1 :  // I-type (JALR)
                         (if_id_opcode == 7'b0110111) ? 1'b1 :  // U-type (LUI)
                         (if_id_opcode == 7'b0010111) ? 1'b1 :  // U-type (AUIPC)
                         1'b0; // default (Store, Branch, and others don't write to registers)

    // Memory interface
    assign mem_addr = ex_mem_result;
    assign mem_wdata = ex_mem_rs2_data;
    assign mem_flag = ex_mem_instr[14:12];
    // Only access memory when instruction is ready
    assign mem_we = instr_ready && ex_mem_mem_we;
    assign mem_re = instr_ready && ex_mem_mem_re;

    // Writeback result selection
    wire [31:0] wb_result;
    wire [31:0] mem_value;
    
    assign mem_value = (ex_mem_instr[14:12] == 3'b000) ? {{24{mem_data[7]}}, mem_data[7:0]} :   // LB
                       (ex_mem_instr[14:12] == 3'b001) ? {{16{mem_data[15]}}, mem_data[15:0]} : // LH
                       (ex_mem_instr[14:12] == 3'b010) ? mem_data :                             // LW
                       (ex_mem_instr[14:12] == 3'b100) ? {{24'b0}, mem_data[7:0]} :             // LBU
                       (ex_mem_instr[14:12] == 3'b101) ? {{16'b0}, mem_data[15:0]} :            // LHU
                       0;
    assign wb_result = (ex_mem_instr[6:0] == 7'b0000011) ? mem_value :          // Load: use memory data
                       (ex_mem_instr[6:0] == 7'b1101111) ? ex_mem_pc + 4 :      // JAL: return address
                       (ex_mem_instr[6:0] == 7'b1100111) ? ex_mem_pc + 4 :      // JALR: return address
                       (ex_mem_instr[6:0] == 7'b0110111) ? ex_mem_result :      // LUI: ALU result (immediate)
                       ex_mem_result;                                           // Others: ALU result

    // Branch hazard detection
    assign branch_hazard = (id_ex_instr[6:0] == 7'b1100011) ||     // B-Type (BEQ, BNE, BLT, BGE)
                          (id_ex_instr[6:0] == 7'b1101111) ||     // JAL
                          (id_ex_instr[6:0] == 7'b1100111);       // JALR

    // Data hazard detection and forwarding logic in IF/ID stage
    // Check if we need to forward from ID/EX stage
    assign if_id_rs1_forward_id = if_id_is_risb_type && (if_id_rs1 != 0) && (if_id_rs1 == id_ex_rd_addr) && id_ex_reg_we && 
                            !(id_ex_instr[6:0] == 7'b0000011); // Don't forward from load in EX/MEM
    assign if_id_rs2_forward_id = if_id_is_rsb_type && (if_id_rs2 != 0) && (if_id_rs2 == id_ex_rd_addr) && id_ex_reg_we && 
                            !(id_ex_instr[6:0] == 7'b0000011); // Don't forward from load in EX/MEM
    assign if_id_alu_b_forward_id = !if_id_is_alu_b_fixed && if_id_rs2_forward_id;

    // Check if we need to forward from EX/MEM stage
    assign if_id_rs1_forward_ex = if_id_is_risb_type && (if_id_rs1 != 0) && (if_id_rs1 == ex_mem_rd_addr) && ex_mem_reg_we && 
                             !if_id_rs1_forward_id; // Only if not already forwarding from EX/MEM
    assign if_id_rs2_forward_ex = if_id_is_rsb_type && (if_id_rs2 != 0) && (if_id_rs2 == ex_mem_rd_addr) && ex_mem_reg_we && 
                             !if_id_rs2_forward_id; // Only if not already forwarding from EX/MEM

    // Select forwarded data
    assign if_id_rs1_data_forwarded = if_id_rs1_forward_ex ? wb_result :
                                if_id_rs1_data;
    assign if_id_rs2_data_forwarded = if_id_rs2_forward_ex ? wb_result :
                                if_id_rs2_data;

    assign if_id_alu_a_forwarded = if_id_is_alu_a_fixed ? if_id_fixed_alu_a :
                                if_id_rs1_data_forwarded;
    assign if_id_alu_b_forwarded = if_id_is_alu_b_fixed ? if_id_fixed_alu_b :
                                if_id_rs2_data_forwarded;

    // Load-use hazard detection
    // Detect when current instruction in ID/EX is a load and next instruction in IF/ID uses the loaded register
    assign load_use_hazard = (id_ex_instr[6:0] == 7'b0000011) && // Current instruction is a load
                             (id_ex_rd_addr != 0) &&              // Load writes to a register
                             ((if_id_rs1 == id_ex_rd_addr) || // Next instruction uses rs1
                              (if_id_rs2 == id_ex_rd_addr));  // Next instruction uses rs2

    // Pipeline stages
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all pipeline registers
            pc <= RESET_ADDR;
            if_id_instr <= 32'h00000013; // NOP instruction
            if_id_pc <= RESET_ADDR;

            id_ex_instr <= 32'h00000013;
            id_ex_pc <= RESET_ADDR;
            id_ex_imm <= 32'd0;
            id_ex_rs1_addr <= 5'd0;
            id_ex_rs2_addr <= 5'd0;
            id_ex_rd_addr <= 5'd0;
            id_ex_alu_op <= 4'd0;
            id_ex_mem_we <= 1'b0;
            id_ex_mem_re <= 1'b0;
            id_ex_reg_we <= 1'b0;
            id_ex_rs1_forward_ex <= 1'b0;
            id_ex_rs2_forward_ex <= 1'b0;
            id_ex_alu_a_forward_ex <= 1'b0;
            id_ex_alu_b_forward_ex <= 1'b0;
            id_ex_rs1_data_forwarded <= 32'd0;
            id_ex_rs2_data_forwarded <= 32'd0;
            id_ex_alu_a_forwarded <= 32'd0;
            id_ex_alu_b_forwarded <= 32'd0;

            pc_branch_taken <= 32'd0;
            pc_branch_not_taken <= 32'd0;
            pc_id_ex_funct3 <= 3'd0;

            ex_mem_result <= 32'd0;
            ex_mem_rs2_data <= 32'd0;
            ex_mem_pc <= 32'd0;
            ex_mem_instr <= 32'h00000013;
            ex_mem_rd_addr <= 5'd0;
            ex_mem_mem_we <= 1'b0;
            ex_mem_mem_re <= 1'b0;
            ex_mem_reg_we <= 1'b0;
            mem_stall <= 1'b0;
            mem_wb_result <= 32'd0;
            mem_wb_rd_addr <= 5'd0;
            mem_wb_reg_we <= 1'b0;
            wb___result <= 32'd0;
            wb___rd_addr <= 5'd0;
            wb___reg_we <= 1'b0;

            error_flag_reg <= 1'b0;
            
            `DEBUG_PRINT(("=== RV32I Core Reset ==="));
        end else begin

            // Hazard handling logic:
            // * Branch hazard
            //     + Insert NOP to both IF/ID and ID/EX stages
            // * Data hazard
            //     + Forwarding from EX/MEM MEM/WB, and WB/_ stages
            // * Load-use hazard
            //     + Keep the same instruction in IF/ID stage, don't increment PC
            //     + Insert NOP to ID/EX stage
            // * Instruction memory not ready
            //     + Stall pipeline at instruction fetch stage when instruction memory is not ready
            // * Data memory stall
            //     + Stall pipeline at memory stage when data memory is not ready

            if (mem_stall || !instr_ready) begin
                // Stall pipeline
                if (mem_stall && instr_ready) begin
                    // Only keep we and re signals for 1 cycle
                    // When the instruction is ready, we start accessing memory (above code) and clear these signals here
                    ex_mem_mem_we <= 1'b0;
                    ex_mem_mem_re <= 1'b0;
                end
                if (mem_ready) begin
                    mem_stall <= 1'b0;
                end
            end else begin
                // Pipeline stage 1: Instruction Fetch
                // If load_use_hazard is detected, keep the same instruction in IF/ID stage, don't increment PC
                if (!load_use_hazard) begin
                    pc <= pc_next;
                    if_id_instr <= instr_data;
                    if_id_pc <= pc;
                end

                if (!error_flag_reg) begin
                    if (is_valid_opcode == 1'b0) begin
                        `DEBUG_PRINT(("Time %0t: Invalid if_id_opcode: %b, instr=0x%h, pc=0x%h", $time, id_opcode, id_ex_instr, pc - 8));
                    end
                    error_flag_reg <= !is_valid_opcode;
                end

                // Pipeline stage 2: Instruction Decode
                id_ex_instr <= if_id_instr;
                id_ex_pc <= if_id_pc;
                id_ex_rs1_addr <= if_id_rs1;
                id_ex_rs2_addr <= if_id_rs2;
                id_ex_rd_addr <= rd;
                id_ex_alu_op <= if_id_alu_op;
                id_ex_mem_we <= mem_we_ctrl;
                id_ex_mem_re <= mem_re_ctrl;
                id_ex_reg_we <= reg_we_ctrl;
                id_ex_imm <= if_id_imm;

                id_ex_rs1_forward_ex <= if_id_rs1_forward_id;
                id_ex_rs2_forward_ex <= if_id_rs2_forward_id;
                id_ex_alu_a_forward_ex <= if_id_rs1_forward_id;
                id_ex_alu_b_forward_ex <= if_id_alu_b_forward_id;
                id_ex_rs1_data_forwarded <= if_id_rs1_data_forwarded;
                id_ex_rs2_data_forwarded <= if_id_rs2_data_forwarded;
                id_ex_alu_a_forwarded <= if_id_alu_a_forwarded;
                id_ex_alu_b_forwarded <= if_id_alu_b_forwarded;

                pc_branch_taken <= if_id_pc_branch_taken;
                pc_branch_not_taken <= if_id_pc_branch_not_taken;
                pc_id_ex_funct3 <= funct3;

                // If branch_hazard is detected, flush IF/ID stage with NOP
                if (branch_hazard) begin
                    `DEBUG_PRINT(("Time %0t: IF/ID - Flushing with NOP", $time));
                    if_id_instr <= 32'h00000013; // NOP instruction
                    if_id_pc <= 32'h00000000;    // Invalid PC
                    
                end
                // If load_use_hazard or branch_hazard is detected, flush ID/EX stage with NOP
                if (branch_hazard == 1'b1 || load_use_hazard == 1'b1) begin
                    id_ex_instr <= 32'h00000013;
                    id_ex_pc <= 32'h00000000;
                    id_ex_rs1_addr <= 5'd0;
                    id_ex_rs2_addr <= 5'd0;
                    id_ex_rd_addr <= 5'd0;
                    id_ex_alu_op <= 4'd0;
                    id_ex_mem_we <= 1'b0;
                    id_ex_mem_re <= 1'b0;
                    id_ex_reg_we <= 1'b0;
                    id_ex_imm <= 32'd0;
                    id_ex_rs1_forward_ex <= 1'b0;
                    id_ex_rs2_forward_ex <= 1'b0;
                    id_ex_alu_a_forward_ex <= 1'b0;
                    id_ex_alu_b_forward_ex <= 1'b0;
                    id_ex_rs1_data_forwarded <= 32'd0;
                    id_ex_rs2_data_forwarded <= 32'd0;
                    id_ex_alu_a_forwarded <= 32'd0;
                    id_ex_alu_b_forwarded <= 32'd0;

                    pc_branch_taken <= 32'd0;
                    pc_branch_not_taken <= 32'd0;
                    pc_id_ex_funct3 <= 3'd0;
                end

                // Pipeline stage 3: Execute
                ex_mem_result <= alu_result;
                ex_mem_rs2_data <= id_ex_rs2_final_data_forwarded;
                ex_mem_pc <= id_ex_pc;
                ex_mem_instr <= id_ex_instr;
                ex_mem_rd_addr <= id_ex_rd_addr;
                ex_mem_mem_we <= id_ex_mem_we;
                ex_mem_mem_re <= id_ex_mem_re;
                ex_mem_reg_we <= id_ex_reg_we;
                if (id_ex_mem_we || id_ex_mem_re) begin
                    mem_stall <= 1'b1;
                end

                // Pipeline stage 4: Memory
                mem_wb_result <= wb_result;
                mem_wb_rd_addr <= ex_mem_rd_addr;
                mem_wb_reg_we <= ex_mem_reg_we;

                // Pipeline stage 5: Writeback
                wb___result <= mem_wb_result;
                wb___rd_addr <= mem_wb_rd_addr;
                wb___reg_we <= mem_wb_reg_we;
            end // !mem_stall
        end // rst_n
    end // always block



    // Select forwarded data
    wire [31:0] id_ex_rs1_final_data_forwarded = id_ex_rs1_forward_ex ? ex_mem_result :
                                id_ex_rs1_data_forwarded;
    wire [31:0] id_ex_rs2_final_data_forwarded = id_ex_rs2_forward_ex ? ex_mem_result :
                                id_ex_rs2_data_forwarded;

    wire        id_ex_sign_rs1 = id_ex_rs1_final_data_forwarded[31];
    wire        id_ex_sign_rs2 = id_ex_rs2_final_data_forwarded[31];
    wire [31:0] id_ex_diff     = id_ex_rs1_final_data_forwarded - id_ex_rs2_final_data_forwarded;

    wire        id_ex_lt_s = (id_ex_sign_rs1 ^ id_ex_sign_rs2) ? id_ex_sign_rs1 : id_ex_diff[31]; // rs1 < rs2 (signed)
    wire        id_ex_ge_s = ~id_ex_lt_s;                                                          // rs1 >= rs2 (signed)

    wire id_ex_eq = (id_ex_rs1_final_data_forwarded == id_ex_rs2_final_data_forwarded);
    wire id_ex_ne = ~id_ex_eq;
    wire id_ex_lt = (id_ex_rs1_final_data_forwarded < id_ex_rs2_final_data_forwarded);
    wire id_ex_ge = ~id_ex_lt;
    // PC update logic
    assign pc_next = (id_opcode == 7'b1100011) ? ( // Branch
                        (pc_id_ex_funct3 == 3'b000) ? ((id_ex_eq) ? pc_branch_taken : pc_branch_not_taken) : // BEQ
                        (pc_id_ex_funct3 == 3'b001) ? ((id_ex_ne) ? pc_branch_taken : pc_branch_not_taken) : // BNE
                        (pc_id_ex_funct3 == 3'b100) ? ((id_ex_lt_s) ? pc_branch_taken : pc_branch_not_taken) : // BLT
                        (pc_id_ex_funct3 == 3'b101) ? ((id_ex_ge_s) ? pc_branch_taken : pc_branch_not_taken) : // BGE
                        (pc_id_ex_funct3 == 3'b110) ? ((id_ex_lt) ? pc_branch_taken : pc_branch_not_taken) : // BLTU
                        (pc_id_ex_funct3 == 3'b111) ? ((id_ex_ge) ? pc_branch_taken : pc_branch_not_taken) : // BGEU
                        pc_branch_not_taken // default
                     ) :
                     (id_opcode == 7'b1101111) ? pc_branch_taken : // JAL
                     (id_opcode == 7'b1100111) ? ((id_ex_rs1_final_data_forwarded + id_ex_imm) & ~1) : // JALR
                     pc + 4; // default: sequential execution

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
            7'b0110011: begin // R-type instructions
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
            
            7'b0010011: begin // I-type ALU instructions
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
            
            7'b0000011: begin // Load instructions
                case (funct3)
                    3'b000: result = $sformatf("LB x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    3'b001: result = $sformatf("LH x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    3'b010: result = $sformatf("LW x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    3'b100: result = $sformatf("LBU x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    3'b101: result = $sformatf("LHU x%0d, 0x%0h(x%0d)", rd, $signed(imm_i), rs1);
                    default: result = $sformatf("UNKNOWN_LOAD x%0d, 0x%0h(x%0d) (funct3=%b)", rd, $signed(imm_i), rs1, funct3);
                endcase
            end
            
            7'b0100011: begin // Store instructions
                case (funct3)
                    3'b000: result = $sformatf("SB x%0d, 0x%0h(x%0d)", rs2, $signed(imm_s), rs1);
                    3'b001: result = $sformatf("SH x%0d, 0x%0h(x%0d)", rs2, $signed(imm_s), rs1);
                    3'b010: result = $sformatf("SW x%0d, 0x%0h(x%0d)", rs2, $signed(imm_s), rs1);
                    default: result = $sformatf("UNKNOWN_STORE x%0d, 0x%0h(x%0d) (funct3=%b)", rs2, $signed(imm_s), rs1, funct3);
                endcase
            end
            
            7'b1100011: begin // Branch instructions
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
            
            7'b1101111: begin // JAL
                result = $sformatf("JAL x%0d, 0x%0h", rd, $signed(imm_j));
            end
            
            7'b1100111: begin // JALR
                result = $sformatf("JALR x%0d, x%0d, 0x%0h", rd, rs1, $signed(imm_i));
            end
            
            7'b0110111: begin // LUI
                result = $sformatf("LUI x%0d, 0x%h", rd, imm_u);
            end
            
            7'b0010111: begin // AUIPC
                result = $sformatf("AUIPC x%0d, 0x%h", rd, imm_u);
            end
            
            7'b1110011: begin // System instructions
                case (funct3)
                    3'b000: begin
                        case (imm12)
                            12'h000: result = "ECALL";
                            12'h001: result = "EBREAK";
                            default: result = $sformatf("UNKNOWN_SYSTEM (imm12=0x%h)", imm12);
                        endcase
                    end
                    default: result = $sformatf("UNKNOWN_SYSTEM (funct3=%b)", funct3);
                endcase
            end
            
            7'b0001111: begin // FENCE
                result = "FENCE";
            end
            
            default: result = $sformatf("UNKNOWN_OPCODE 0x%h (opcode=%b)", instr, opcode);
        endcase
        
        return result;
    endfunction

    // Debug logging with $display statements
    always @(posedge clk) begin
        string if_id_instr_str, id_ex_instr_str, ex_mem_instr_str;
        if_id_instr_str = decode_instruction(if_id_instr);
        id_ex_instr_str = decode_instruction(id_ex_instr);
        ex_mem_instr_str = decode_instruction(ex_mem_instr);

        // Log instruction fetch
        `DEBUG_PRINT(("Time %0t: IF - PC=0x%h, Instr=0x%h (%s), instr_ready=%b, PC_next=0x%h", $time, if_id_pc, if_id_instr, if_id_instr_str, instr_ready, pc_next));
        
        // Log instruction decode and register reads
        `DEBUG_PRINT(("Time %0t: ID - PC=0x%h, Instr=0x%h (%s), alu_a=x%0d(0x%h), alu_b=x%0d(0x%h), rd=x%0d, rs1=0x%h, rs2=0x%h", 
                    $time, id_ex_pc, id_ex_instr, id_ex_instr_str, id_ex_rs1_addr, id_ex_alu_a_forwarded,
                    id_ex_rs2_addr, id_ex_alu_b_forwarded, id_ex_rd_addr, id_ex_rs1_data_forwarded, id_ex_rs2_data_forwarded));

        if (id_ex_alu_a_forward_ex) begin
            `DEBUG_PRINT(("Time %0t: FORWARD - alu_a forwarding: rs1=x%0d, id_ex_alu_a_forward_ex=%b, data=0x%h", 
                     $time, id_ex_rs1_addr, id_ex_alu_a_forward_ex, id_ex_alu_a));
        end
        if (id_ex_alu_b_forward_ex) begin
            `DEBUG_PRINT(("Time %0t: FORWARD - alu_b forwarding: rs2=x%0d, id_ex_alu_b_forward_ex=%b, data=0x%h", 
                     $time, id_ex_rs2_addr, id_ex_alu_b_forward_ex, id_ex_alu_b));
        end

        if (id_ex_rs1_forward_ex) begin
            `DEBUG_PRINT(("Time %0t: FORWARD - rs1 forwarding: rs1=x%0d, id_ex_rs1_forward_ex=%b, data=0x%h", 
                     $time, id_ex_rs1_addr, id_ex_rs1_forward_ex, id_ex_rs1_final_data_forwarded));
        end
        if (id_ex_rs2_forward_ex) begin
            `DEBUG_PRINT(("Time %0t: FORWARD - rs2 forwarding: rs2=x%0d, id_ex_rs2_forward_ex=%b, data=0x%h", 
                     $time, id_ex_rs2_addr, id_ex_rs2_forward_ex, id_ex_rs2_final_data_forwarded));
        end
        
        // Log data hazard detection
        if ((id_rs1 != 0 && id_rs1 == ex_mem_rd_addr && ex_mem_reg_we) ||
            (id_rs2 != 0 && id_rs2 == ex_mem_rd_addr && ex_mem_reg_we) ||
            (id_rs1 != 0 && id_rs1 == mem_wb_rd_addr && mem_wb_reg_we) ||
            (id_rs2 != 0 && id_rs2 == mem_wb_rd_addr && mem_wb_reg_we) ||
            (id_rs1 != 0 && id_rs1 == wb___rd_addr && wb___reg_we) ||
            (id_rs2 != 0 && id_rs2 == wb___rd_addr && wb___reg_we)) begin
            `DEBUG_PRINT(("Time %0t: HAZARD - Data hazard detected: rs1=x%0d, rs2=x%0d, ex_mem_rd=x%0d, mem_wb_rd=x%0d, wb___rd=x%0d", 
                     $time, id_rs1, id_rs2, ex_mem_rd_addr, mem_wb_rd_addr, wb___rd_addr));
        end

        // Log load-use hazard detection
        if (load_use_hazard) begin
            `DEBUG_PRINT(("Time %0t: HAZARD - Load-use hazard detected: load_rd=x%0d, next_rs1=x%0d, next_rs2=x%0d", 
                     $time, id_ex_rd_addr, if_id_rs1, if_id_rs2));
        end

        // Log memory issues
        if (!instr_ready) begin
            `DEBUG_PRINT(("Time %0t: STALL - Instruction memory not ready, stalling pipeline", $time));
        end
        if (mem_stall) begin
            `DEBUG_PRINT(("Time %0t: STALL - Data memory not ready, stalling pipeline", $time));
        end

        // Log ALU operations
        `DEBUG_PRINT(("Time %0t: ALU - ALU: op=0x%h, a=0x%h, b=0x%h, result=0x%h, rd=x%0d", 
                    $time, id_ex_alu_op, id_ex_alu_a, id_ex_alu_b, alu_result, id_ex_rd_addr));

        `DEBUG_PRINT(("Time %0t: EX - PC=0x%h, Instr=0x%h (%s)", 
                    $time, ex_mem_pc, ex_mem_instr, ex_mem_instr_str));

        // Log memory operations
        if (ex_mem_mem_we) begin
            `DEBUG_PRINT(("Time %0t: MEM - Store: addr=0x%h, data=0x%h", 
                     $time, ex_mem_result, ex_mem_rs2_data));
        end
        if (ex_mem_mem_re) begin
            `DEBUG_PRINT(("Time %0t: MEM - Load: addr=0x%h, mem_data=0x%h, wb_result=0x%h", 
                     $time, ex_mem_result, mem_data, wb_result));
        end
        if (!ex_mem_mem_we && !ex_mem_mem_re) begin
            `DEBUG_PRINT(("Time %0t: MEM - Non-Memory Operation", $time));
        end
        
        // Log register writes
        if (mem_wb_reg_we) begin
            `DEBUG_PRINT(("Time %0t: WB - Reg Write: x%d = 0x%h", 
                     $time, mem_wb_rd_addr, mem_wb_result));
        end
        else begin
            `DEBUG_PRINT(("Time %0t: WB - Non-Reg Write", $time));
        end
        
        // Log branches and jumps
        if (id_opcode == 7'b1100011) begin
            case (pc_id_ex_funct3)
                3'b000: `DEBUG_PRINT(("Time %0t: BRANCH - BEQ: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_ex_rs1_final_data_forwarded, id_ex_rs2_final_data_forwarded, id_ex_eq));
                3'b001: `DEBUG_PRINT(("Time %0t: BRANCH - BNE: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_ex_rs1_final_data_forwarded, id_ex_rs2_final_data_forwarded, id_ex_ne));
                3'b100: `DEBUG_PRINT(("Time %0t: BRANCH - BLT: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_ex_rs1_final_data_forwarded, id_ex_rs2_final_data_forwarded, id_ex_lt_s));
                3'b101: `DEBUG_PRINT(("Time %0t: BRANCH - BGE: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_ex_rs1_final_data_forwarded, id_ex_rs2_final_data_forwarded, id_ex_ge_s));
                3'b110: `DEBUG_PRINT(("Time %0t: BRANCH - BLTU: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_ex_rs1_final_data_forwarded, id_ex_rs2_final_data_forwarded, id_ex_lt));
                3'b111: `DEBUG_PRINT(("Time %0t: BRANCH - BGEU: rs1=0x%h, rs2=0x%h, taken=%b", 
                                  $time, id_ex_rs1_final_data_forwarded, id_ex_rs2_final_data_forwarded, id_ex_ge));
            endcase
        end

        `DEBUG_PRINT(("--------------------------------"));
    end
`endif

endmodule

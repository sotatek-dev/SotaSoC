/* RV32E Core - Main processor module */

/*
    5-Stage Pipeline
    IF (Instruction Fetch): Fetches instructions from memory
    ID (Instruction Decode): Decodes instructions and reads registers
    EX (Execute): Performs ALU operations
    MEM (Memory): Handles memory access
    WB (Writeback): Writes results back to registers
*/

module rv32e_core (
    input wire clk,
    input wire rst_n,
    
    // Memory interface
    input wire [31:0] instr_data,    // Instruction from memory
    input wire [31:0] mem_data,      // Data from memory
    output wire [31:0] instr_addr,   // Instruction address
    output wire [31:0] mem_addr,     // Memory address
    output wire [31:0] mem_wdata,    // Data to write to memory
    output wire mem_we,              // Memory write enable
    output wire mem_re               // Memory read enable
);

    // Pipeline registers
    reg [31:0] pc, pc_next;
    reg [31:0] if_id_instr, if_id_pc;
    reg [31:0] id_ex_instr, id_ex_pc, id_ex_rs1_data, id_ex_rs2_data, id_ex_imm;
    reg [3:0] id_ex_rs1_addr, id_ex_rs2_addr, id_ex_rd_addr;
    reg [3:0] id_ex_alu_op;
    reg id_ex_mem_we, id_ex_mem_re, id_ex_reg_we;
    reg [31:0] ex_mem_result, ex_mem_rs2_data, ex_mem_pc, ex_mem_instr;
    reg [3:0] ex_mem_rd_addr;
    reg ex_mem_mem_we, ex_mem_mem_re, ex_mem_reg_we;
    reg [31:0] mem_wb_result, mem_wb_pc;
    reg [3:0] mem_wb_rd_addr;
    reg mem_wb_reg_we;

    // Pipeline control signals
    wire branch_taken;
    reg flush_if_id;

    // Instruction fields
    wire [6:0] opcode;
    wire [2:0] funct3;
    wire [6:0] funct7;
    wire [4:0] rd, rs1, rs2;
    wire [11:0] imm12;
    wire [31:0] imm_i, imm_s, imm_b, imm_u, imm_j;

    // Control signals
    wire [3:0] alu_op;
    wire mem_we_ctrl, mem_re_ctrl, reg_we_ctrl;
    wire [31:0] alu_result;
    wire alu_zero, alu_negative, alu_overflow;

    // Register file connections
    wire [31:0] rs1_data, rs2_data;

    // ALU operand selection
    wire [31:0] alu_a, alu_b;
    
    // ALU operand A selection
    assign alu_a = (id_ex_instr[6:0] == 7'b0010111) ? id_ex_pc : id_ex_rs1_data; // AUIPC uses PC
    
    // ALU operand B selection
    assign alu_b = (id_ex_instr[6:0] == 7'b0110011) ? id_ex_rs2_data :  // R-type: use rs2
                   (id_ex_instr[6:0] == 7'b0010011) ? id_ex_imm :       // I-type (ALU): use immediate
                   (id_ex_instr[6:0] == 7'b0000011) ? id_ex_imm :       // I-type (Load): use immediate for address
                   (id_ex_instr[6:0] == 7'b0100011) ? id_ex_imm :       // S-type (Store): use immediate for address
                   (id_ex_instr[6:0] == 7'b1100011) ? id_ex_rs2_data :  // B-type: use rs2 for comparison
                   (id_ex_instr[6:0] == 7'b1101111) ? id_ex_imm :       // J-type (JAL): use immediate
                   (id_ex_instr[6:0] == 7'b1100111) ? id_ex_imm :       // I-type (JALR): use immediate
                   (id_ex_instr[6:0] == 7'b0110111) ? id_ex_imm :       // U-type (LUI): use immediate
                   (id_ex_instr[6:0] == 7'b0010111) ? id_ex_imm :       // U-type (AUIPC): use immediate
                   id_ex_rs2_data; // default

    // Instruction decoding
    assign opcode = if_id_instr[6:0];
    assign rd = if_id_instr[11:7];
    assign funct3 = if_id_instr[14:12];
    assign rs1 = if_id_instr[19:15];
    assign rs2 = if_id_instr[24:20];
    assign funct7 = if_id_instr[31:25];

    // Immediate generation
    assign imm12 = if_id_instr[31:20];
    assign imm_i = {{20{imm12[11]}}, imm12};
    assign imm_s = {{20{if_id_instr[31]}}, if_id_instr[31:25], if_id_instr[11:7]};
    assign imm_b = {{20{if_id_instr[31]}}, if_id_instr[7], if_id_instr[30:25], if_id_instr[11:8], 1'b0};
    assign imm_u = {if_id_instr[31:12], 12'b0};
    assign imm_j = {{12{if_id_instr[31]}}, if_id_instr[19:12], if_id_instr[20], if_id_instr[30:21], 1'b0};

    // Instruction address
    assign instr_addr = pc;

    // Register file instantiation
    rv32e_register register_file (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(rs1[3:0]),      // RV32E uses only 4 bits for register addresses
        .rs2_addr(rs2[3:0]),
        .rs1_data(rs1_data),
        .rs2_data(rs2_data),
        .rd_addr(mem_wb_rd_addr),
        .rd_data(mem_wb_result),
        .rd_we(mem_wb_reg_we)
    );

    // ALU instantiation
    rv32e_alu alu (
        .op(id_ex_alu_op),
        .a(alu_a),
        .b(alu_b),
        .result(alu_result),
        .zero_flag(alu_zero),
        .negative_flag(alu_negative),
        .overflow_flag(alu_overflow)
    );

    // Control unit
    assign alu_op = (opcode == 7'b0110011) ? {funct7[5], funct3} :     // R-type
                    (opcode == 7'b0010011) ? {1'b0, funct3} :           // I-type (ALU)
                    (opcode == 7'b0000011) ? 4'b0000 :                  // I-type (Load) - ADD for address
                    (opcode == 7'b0100011) ? 4'b0000 :                  // S-type (Store) - ADD for address
                    (opcode == 7'b1100011) ? {1'b1, funct3} :           // B-type (Branch) - Comparison operations
                    (opcode == 7'b1101111) ? 4'b0000 :                  // J-type (JAL)
                    (opcode == 7'b1100111) ? 4'b0000 :                  // I-type (JALR)
                    (opcode == 7'b0110111) ? 4'b0000 :                  // U-type (LUI)
                    (opcode == 7'b0010111) ? 4'b0000 :                  // U-type (AUIPC) - ADD
                    4'b0000; // default

    assign mem_we_ctrl = (opcode == 7'b0100011) ? 1'b1 : 1'b0; // Only Store instructions write to memory

    assign mem_re_ctrl = (opcode == 7'b0000011) ? 1'b1 : 1'b0; // Only Load instructions read from memory

    assign reg_we_ctrl = (opcode == 7'b0110011) ? 1'b1 :  // R-type
                         (opcode == 7'b0010011) ? 1'b1 :  // I-type (ALU)
                         (opcode == 7'b0000011) ? 1'b1 :  // I-type (Load)
                         (opcode == 7'b1101111) ? 1'b1 :  // J-type (JAL)
                         (opcode == 7'b1100111) ? 1'b1 :  // I-type (JALR)
                         (opcode == 7'b0110111) ? 1'b1 :  // U-type (LUI)
                         (opcode == 7'b0010111) ? 1'b1 :  // U-type (AUIPC)
                         1'b0; // default (Store, Branch, and others don't write to registers)

    // Memory interface
    assign mem_addr = ex_mem_result;
    assign mem_wdata = ex_mem_rs2_data;
    assign mem_we = ex_mem_mem_we;
    assign mem_re = ex_mem_mem_re;

    // Writeback result selection
    wire [31:0] wb_result;
    
    assign wb_result = (ex_mem_instr[6:0] == 7'b0000011) ? mem_data :           // Load: use memory data
                       (ex_mem_instr[6:0] == 7'b1101111) ? ex_mem_pc + 4 :      // JAL: return address
                       (ex_mem_instr[6:0] == 7'b1100111) ? ex_mem_pc + 4 :      // JALR: return address
                       (ex_mem_instr[6:0] == 7'b0110111) ? ex_mem_result :      // LUI: ALU result (immediate)
                       ex_mem_result;                                           // Others: ALU result

    // Branch detection logic
    assign branch_taken = (id_ex_instr[6:0] == 7'b1100011) ||     // B-Type (BEQ, BNE, BLT, BGE)
                          (id_ex_instr[6:0] == 7'b1101111) ||     // JAL
                          (id_ex_instr[6:0] == 7'b1100111);       // JALR

    // Pipeline stages
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all pipeline registers
            pc <= 32'h80000000; // Start at typical RISC-V reset address
            flush_if_id <= 1'b0;
            if_id_instr <= 32'h00000013; // NOP instruction
            if_id_pc <= 32'h80000000;
            id_ex_instr <= 32'h00000013;
            id_ex_pc <= 32'h80000000;
            id_ex_rs1_data <= 32'd0;
            id_ex_rs2_data <= 32'd0;
            id_ex_imm <= 32'd0;
            id_ex_rs1_addr <= 4'd0;
            id_ex_rs2_addr <= 4'd0;
            id_ex_rd_addr <= 4'd0;
            id_ex_alu_op <= 4'd0;
            id_ex_mem_we <= 1'b0;
            id_ex_mem_re <= 1'b0;
            id_ex_reg_we <= 1'b0;
            ex_mem_result <= 32'd0;
            ex_mem_rs2_data <= 32'd0;
            ex_mem_pc <= 32'd0;
            ex_mem_instr <= 32'h00000013;
            ex_mem_rd_addr <= 4'd0;
            ex_mem_mem_we <= 1'b0;
            ex_mem_mem_re <= 1'b0;
            ex_mem_reg_we <= 1'b0;
            mem_wb_result <= 32'd0;
            mem_wb_pc <= 32'd0;
            mem_wb_rd_addr <= 4'd0;
            mem_wb_reg_we <= 1'b0;
            
            $display("=== RV32E Core Reset ===");
        end else begin
            // Pipeline stage 1: Instruction Fetch
            pc <= pc_next;
            if_id_instr <= instr_data;
            if_id_pc <= pc;

            // Pipeline stage 2: Instruction Decode
            id_ex_instr <= if_id_instr;
            id_ex_pc <= if_id_pc;
            id_ex_rs1_data <= rs1_data;
            id_ex_rs2_data <= rs2_data;
            id_ex_rs1_addr <= rs1[3:0];
            id_ex_rs2_addr <= rs2[3:0];
            id_ex_rd_addr <= rd[3:0];
            id_ex_alu_op <= alu_op;
            id_ex_mem_we <= mem_we_ctrl;
            id_ex_mem_re <= mem_re_ctrl;
            id_ex_reg_we <= reg_we_ctrl;

            // Select immediate value based on instruction type
            case (opcode)
                7'b0010011, 7'b0000011, 7'b1100111: id_ex_imm <= imm_i; // I-type
                7'b0100011: id_ex_imm <= imm_s; // S-type
                7'b1100011: id_ex_imm <= imm_b; // B-type
                7'b1101111: id_ex_imm <= imm_j; // J-type
                7'b0110111, 7'b0010111: id_ex_imm <= imm_u; // U-type
                default: id_ex_imm <= 32'd0;
            endcase

            // Pipeline: Flush with NOP if branch taken
            flush_if_id <= !flush_if_id && branch_taken;
            if (branch_taken == 1'b1 || flush_if_id == 1'b1) begin
                $display("Time %0t: IF/ID - Flushing with NOP", $time);
                if_id_instr <= 32'h00000013; // NOP instruction
                if_id_pc <= 32'h00000000;    // Invalid PC

                id_ex_instr <= 32'h00000013;
                id_ex_pc <= 32'h00000000;
                id_ex_rs1_data <= 32'd0;
                id_ex_rs2_data <= 32'd0;
                id_ex_rs1_addr <= 4'd0;
                id_ex_rs2_addr <= 4'd0;
                id_ex_rd_addr <= 4'd0;
                id_ex_alu_op <= 4'd0;
                id_ex_mem_we <= 1'b0;
                id_ex_mem_re <= 1'b0;
                id_ex_reg_we <= 1'b0;
                id_ex_imm <= 32'd0;
            end

            // Pipeline stage 3: Execute
            ex_mem_result <= alu_result;
            ex_mem_rs2_data <= id_ex_rs2_data;
            ex_mem_pc <= id_ex_pc;
            ex_mem_instr <= id_ex_instr;
            ex_mem_rd_addr <= id_ex_rd_addr;
            ex_mem_mem_we <= id_ex_mem_we;
            ex_mem_mem_re <= id_ex_mem_re;
            ex_mem_reg_we <= id_ex_reg_we;

            // Pipeline stage 4: Memory
            mem_wb_result <= wb_result;
            mem_wb_pc <= ex_mem_pc;
            mem_wb_rd_addr <= ex_mem_rd_addr;
            mem_wb_reg_we <= ex_mem_reg_we;
        end
    end

    // PC update logic
    always @(*) begin
        pc_next = pc + 4; // Default: next instruction
        
        // Handle branches and jumps
        if (id_ex_instr[6:0] == 7'b1100011) begin // Branch
            case (id_ex_alu_op)
                4'b1000: pc_next = (alu_zero) ? ex_mem_pc + id_ex_imm * 2 : pc + 4; // BEQ
                4'b1001: pc_next = (!alu_zero) ? ex_mem_pc + id_ex_imm * 2 : pc + 4; // BNE
                4'b1100: pc_next = (alu_negative == 1'b0) ? ex_mem_pc + id_ex_imm * 2 : pc + 4; // BLT
                4'b1110: pc_next = (alu_negative == 1'b0 && !alu_zero) ? ex_mem_pc + id_ex_imm * 2 : pc + 4; // BGT
                default: pc_next = pc + 4;
            endcase
        end else if (id_ex_instr[6:0] == 7'b1101111) begin // JAL
            pc_next = ex_mem_pc + id_ex_imm * 2;
        end else if (id_ex_instr[6:0] == 7'b1100111) begin // JALR
            pc_next = id_ex_rs1_data + id_ex_imm * 2;
        end
    end

    // Debug logging with $display statements
    always @(posedge clk) begin
        // Log instruction fetch
        $display("Time %0t: IF - PC=0x%h, Instr=0x%h, PC_next=0x%h", $time, if_id_pc, if_id_instr, pc_next);
        
        // Log instruction decode and register reads
        $display("Time %0t: ID - PC=0x%h, Instr=0x%h, rs1=x%d(0x%h), rs2=x%d(0x%h), rd=x%d", 
                    $time, id_ex_pc, id_ex_instr, id_ex_rs1_addr, id_ex_rs1_data, 
                    id_ex_rs2_addr, id_ex_rs2_data, id_ex_rd_addr);
        
        // Log ALU operations
        if (id_ex_reg_we && id_ex_instr != 32'h00000013) begin
            $display("Time %0t: EX - ALU: a=0x%h, b=0x%h, result=0x%h, rd=x%d", 
                     $time, alu_a, alu_b, alu_result, id_ex_rd_addr);
        end
        
        // Log memory operations
        if (ex_mem_mem_we) begin
            $display("Time %0t: MEM - Store: addr=0x%h, data=0x%h", 
                     $time, ex_mem_result, ex_mem_rs2_data);
        end
        if (ex_mem_mem_re) begin
            $display("Time %0t: MEM - Load: addr=0x%h, data=0x%h", 
                     $time, ex_mem_result, mem_data);
        end
        
        // Log register writes
        if (mem_wb_reg_we) begin
            $display("Time %0t: WB - Reg Write: x%d = 0x%h", 
                     $time, mem_wb_rd_addr, mem_wb_result);
        end
        
        // Log branches and jumps
        if (id_ex_instr[6:0] == 7'b1100011 && id_ex_instr != 32'h00000013) begin
            case (id_ex_alu_op)
                4'b1000: $display("Time %0t: BRANCH - BEQ: rs1=0x%h, rs2=0x%h, zero=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_zero, alu_zero);
                4'b1001: $display("Time %0t: BRANCH - BNE: rs1=0x%h, rs2=0x%h, zero=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_zero, !alu_zero);
                4'b1100: $display("Time %0t: BRANCH - BLT: rs1=0x%h, rs2=0x%h, negative=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_negative, !alu_negative);
                4'b1110: $display("Time %0t: BRANCH - BGE: rs1=0x%h, rs2=0x%h, negative=%b, zero=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_negative, alu_zero, (!alu_negative || alu_zero));
            endcase
        end
    end

endmodule

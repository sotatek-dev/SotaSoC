/* RV32I Core - Main processor module */

/*
    5-Stage Pipeline
    IF (Instruction Fetch): Fetches instructions from memory
    ID (Instruction Decode): Decodes instructions and reads registers
    EX (Execute): Performs ALU operations
    MEM (Memory): Handles memory access
    WB (Writeback): Writes results back to registers
*/

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
    reg [31:0] pc, pc_next;
    reg [31:0] if_id_instr, if_id_pc;
    reg [31:0] id_ex_instr, id_ex_pc, id_ex_rs1_data, id_ex_rs2_data, id_ex_imm;
    reg [4:0] id_ex_rs1_addr, id_ex_rs2_addr, id_ex_rd_addr;
    reg [4:0] id_ex_alu_op;
    reg id_ex_mem_we, id_ex_mem_re, id_ex_reg_we;
    reg [31:0] ex_mem_result, ex_mem_rs2_data, ex_mem_pc, ex_mem_instr;
    reg [4:0] ex_mem_rd_addr;
    reg ex_mem_mem_we, ex_mem_mem_re, ex_mem_reg_we;
    reg [31:0] mem_wb_result, mem_wb_pc;
    reg [4:0] mem_wb_rd_addr;
    reg mem_wb_reg_we;
    reg [31:0] wb___result;
    reg [4:0] wb___rd_addr;
    reg wb___reg_we;

    reg error_flag_reg;

    // Instruction type signals
    wire is_r_type, is_i_type, is_s_type, is_b_type, is_j_type, is_u_type, is_risb_type, is_rsb_type;

    // Branch hazard signals
    wire branch_hazard;

    // Data hazard and forwarding signals
    wire [31:0] id_ex_rs1_data_forwarded, id_ex_rs2_data_forwarded;
    wire rs1_forward_ex, rs1_forward_mem, rs2_forward_ex, rs2_forward_mem, rs1_forward_wb, rs2_forward_wb;

    // Load-use hazard signals
    wire load_use_hazard;

    // Memory stall signals
    reg mem_stall;

    // Instruction fields
    wire [6:0] opcode;
    wire [2:0] funct3;
    wire [6:0] funct7;
    wire [4:0] rd, rs1, rs2;
    wire [11:0] imm12;
    wire [31:0] imm_i, imm_s, imm_b, imm_u, imm_j;

    // Use to check data hazard
    wire [6:0] id_opcode;
    wire [4:0] id_rs1, id_rs2;

    // Control signals
    wire [4:0] alu_op;
    wire mem_we_ctrl, mem_re_ctrl, reg_we_ctrl;
    wire [31:0] alu_result;
    wire alu_zero, alu_negative, alu_overflow;

    // Register file connections
    wire [31:0] rs1_data, rs2_data;

    // ALU operand selection
    wire [31:0] alu_a, alu_b;

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

    assign id_opcode = id_ex_instr[6:0];
    assign id_rs1 = id_ex_instr[19:15];
    assign id_rs2 = id_ex_instr[24:20];

    // Instruction address
    assign instr_addr = pc;

    // Register file instantiation
    rv32i_register register_file (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(rs1),
        .rs2_addr(rs2),
        .rs1_data(rs1_data),
        .rs2_data(rs2_data),
        .rd_addr(mem_wb_rd_addr),
        .rd_data(mem_wb_result),
        .rd_we(mem_wb_reg_we)
    );

    // ALU instantiation
    rv32i_alu alu (
        .op(id_ex_alu_op),
        .a(alu_a),
        .b(alu_b),
        .result(alu_result),
        .zero_flag(alu_zero),
        .negative_flag(alu_negative),
        .overflow_flag(alu_overflow)
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

    assign is_r_type = (id_opcode == 7'b0110011);
    assign is_i_type = (id_opcode == 7'b0010011) || (id_opcode == 7'b0000011) || (id_opcode == 7'b1100111);
    assign is_s_type = (id_opcode == 7'b0100011);
    assign is_b_type = (id_opcode == 7'b1100011);
    assign is_j_type = (id_opcode == 7'b1101111);
    assign is_u_type = (id_opcode == 7'b0110111) || (id_opcode == 7'b0010111);
    assign is_risb_type = is_r_type || is_i_type || is_s_type || is_b_type;
    assign is_rsb_type = is_r_type || is_s_type || is_b_type;

    // Control unit
    wire alu_i_type_bit;
    assign alu_i_type_bit = (funct3 == 3'b101) ? funct7[5] : 1'b0;
    assign alu_op = (opcode == 7'b0110011) ? {1'b0, funct7[5], funct3} :      // R-type
                    (opcode == 7'b0010011) ? {1'b0, alu_i_type_bit, funct3} : // I-type (ALU)
                    (opcode == 7'b0000011) ? 5'b00000 :                       // I-type (Load) - ADD for address
                    (opcode == 7'b0100011) ? 5'b00000 :                       // S-type (Store) - ADD for address
                    (opcode == 7'b1100011) ? {2'b10, funct3} :                // B-type (Branch) - Comparison operations
                    (opcode == 7'b1101111) ? 5'b00000 :                       // J-type (JAL)
                    (opcode == 7'b1100111) ? 5'b00000 :                       // I-type (JALR)
                    (opcode == 7'b0110111) ? 5'b00000 :                       // U-type (LUI)
                    (opcode == 7'b0010111) ? 5'b00000 :                       // U-type (AUIPC) - ADD
                    5'b00000; // default (NOP)

    // ALU operand A selection - use forwarded data
    assign alu_a = (id_ex_instr[6:0] == 7'b0010111) ? id_ex_pc : // AUIPC uses PC
                   (id_ex_instr[6:0] == 7'b0110111) ? 0 :        // LUI uses 0
                   id_ex_rs1_data_forwarded;
    
    // ALU operand B selection - use forwarded data
    assign alu_b = (id_ex_instr[6:0] == 7'b0110011) ? id_ex_rs2_data_forwarded :  // R-type: use rs2
                   (id_ex_instr[6:0] == 7'b0010011) ? id_ex_imm :                 // I-type (ALU): use immediate
                   (id_ex_instr[6:0] == 7'b0000011) ? id_ex_imm :                 // I-type (Load): use immediate for address
                   (id_ex_instr[6:0] == 7'b0100011) ? id_ex_imm :                 // S-type (Store): use immediate for address
                   (id_ex_instr[6:0] == 7'b1100011) ? id_ex_rs2_data_forwarded :  // B-type: use rs2 for comparison
                   (id_ex_instr[6:0] == 7'b1101111) ? id_ex_imm :                 // J-type (JAL): use immediate
                   (id_ex_instr[6:0] == 7'b1100111) ? id_ex_imm :                 // I-type (JALR): use immediate
                   (id_ex_instr[6:0] == 7'b0110111) ? id_ex_imm :                 // U-type (LUI): use immediate
                   (id_ex_instr[6:0] == 7'b0010111) ? id_ex_imm :                 // U-type (AUIPC): use immediate
                   id_ex_rs2_data_forwarded; // default

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

    // Data hazard detection and forwarding logic
    // Check if we need to forward from EX/MEM stage
    // Don't forward from EX stage if there's a load-use hazard (load data not available yet)
    assign rs1_forward_ex = is_risb_type && (id_rs1 != 0) && (id_rs1 == ex_mem_rd_addr) && ex_mem_reg_we && 
                            !(ex_mem_instr[6:0] == 7'b0000011); // Don't forward from load in EX/MEM
    assign rs2_forward_ex = is_rsb_type && (id_rs2 != 0) && (id_rs2 == ex_mem_rd_addr) && ex_mem_reg_we && 
                            !(ex_mem_instr[6:0] == 7'b0000011); // Don't forward from load in EX/MEM
    
    // Check if we need to forward from MEM/WB stage
    assign rs1_forward_mem = is_risb_type && (id_rs1 != 0) && (id_rs1 == mem_wb_rd_addr) && mem_wb_reg_we && 
                             !rs1_forward_ex; // Only if not already forwarding from EX/MEM
    assign rs2_forward_mem = is_rsb_type && (id_rs2 != 0) && (id_rs2 == mem_wb_rd_addr) && mem_wb_reg_we && 
                             !rs2_forward_ex; // Only if not already forwarding from EX/MEM

    // Check if we need to forward from WB stage
    assign rs1_forward_wb = is_risb_type && (id_rs1 != 0) && (id_rs1 == wb___rd_addr) && wb___reg_we && 
                             !rs1_forward_ex && !rs1_forward_mem;
    assign rs2_forward_wb = is_rsb_type && (id_rs2 != 0) && (id_rs2 == wb___rd_addr) && wb___reg_we && 
                             !rs2_forward_ex && !rs2_forward_mem;

    // Select forwarded data
    assign id_ex_rs1_data_forwarded = rs1_forward_ex ? ex_mem_result :
                                rs1_forward_mem ? mem_wb_result :
                                rs1_forward_wb ? wb___result :
                                id_ex_rs1_data;

    assign id_ex_rs2_data_forwarded = rs2_forward_ex ? ex_mem_result :
                                rs2_forward_mem ? mem_wb_result :
                                rs2_forward_wb ? wb___result :
                                id_ex_rs2_data;

    // Load-use hazard detection
    // Detect when current instruction in ID/EX is a load and next instruction in IF/ID uses the loaded register
    assign load_use_hazard = (id_ex_instr[6:0] == 7'b0000011) && // Current instruction is a load
                             (id_ex_rd_addr != 0) &&              // Load writes to a register
                             ((rs1 == id_ex_rd_addr) || // Next instruction uses rs1
                              (rs2 == id_ex_rd_addr));  // Next instruction uses rs2

    // Pipeline stages
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all pipeline registers
            pc <= RESET_ADDR;
            if_id_instr <= 32'h00000013; // NOP instruction
            if_id_pc <= RESET_ADDR;
            id_ex_instr <= 32'h00000013;
            id_ex_pc <= RESET_ADDR;
            id_ex_rs1_data <= 32'd0;
            id_ex_rs2_data <= 32'd0;
            id_ex_imm <= 32'd0;
            id_ex_rs1_addr <= 5'd0;
            id_ex_rs2_addr <= 5'd0;
            id_ex_rd_addr <= 5'd0;
            id_ex_alu_op <= 5'd0;
            id_ex_mem_we <= 1'b0;
            id_ex_mem_re <= 1'b0;
            id_ex_reg_we <= 1'b0;
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
            mem_wb_pc <= 32'd0;
            mem_wb_rd_addr <= 5'd0;
            mem_wb_reg_we <= 1'b0;
            wb___result <= 32'd0;
            wb___rd_addr <= 5'd0;
            wb___reg_we <= 1'b0;

            error_flag_reg <= 1'b0;
            
            $display("=== RV32I Core Reset ===");
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
                        $display("Time %0t: Invalid opcode: %b, instr=0x%h, pc=0x%h", $time, id_opcode, id_ex_instr, pc - 8);
                    end
                    error_flag_reg <= !is_valid_opcode;
                end

                // Pipeline stage 2: Instruction Decode
                id_ex_instr <= if_id_instr;
                id_ex_pc <= if_id_pc;
                id_ex_rs1_data <= rs1_data;
                id_ex_rs2_data <= rs2_data;
                id_ex_rs1_addr <= rs1;
                id_ex_rs2_addr <= rs2;
                id_ex_rd_addr <= rd;
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

                // If branch_hazard is detected, flush IF/ID stage with NOP
                if (branch_hazard) begin
                    $display("Time %0t: IF/ID - Flushing with NOP", $time);
                    if_id_instr <= 32'h00000013; // NOP instruction
                    if_id_pc <= 32'h00000000;    // Invalid PC
                    
                end
                // If load_use_hazard or branch_hazard is detected, flush ID/EX stage with NOP
                if (branch_hazard == 1'b1 || load_use_hazard == 1'b1) begin
                    id_ex_instr <= 32'h00000013;
                    id_ex_pc <= 32'h00000000;
                    id_ex_rs1_data <= 32'd0;
                    id_ex_rs2_data <= 32'd0;
                    id_ex_rs1_addr <= 5'd0;
                    id_ex_rs2_addr <= 5'd0;
                    id_ex_rd_addr <= 5'd0;
                    id_ex_alu_op <= 5'd0;
                    id_ex_mem_we <= 1'b0;
                    id_ex_mem_re <= 1'b0;
                    id_ex_reg_we <= 1'b0;
                    id_ex_imm <= 32'd0;
                end

                // Pipeline stage 3: Execute
                ex_mem_result <= alu_result;
                ex_mem_rs2_data <= id_ex_rs2_data_forwarded;
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
                mem_wb_pc <= ex_mem_pc;
                mem_wb_rd_addr <= ex_mem_rd_addr;
                mem_wb_reg_we <= ex_mem_reg_we;

                // Pipeline stage 5: Writeback
                wb___result <= mem_wb_result;
                wb___rd_addr <= mem_wb_rd_addr;
                wb___reg_we <= mem_wb_reg_we;
            end // !mem_stall
        end // rst_n
    end // always block

    // PC update logic
    always @(*) begin
        pc_next = pc + 4; // Default: next instruction

        // Handle branches and jumps
        if (id_ex_instr[6:0] == 7'b1100011) begin // Branch
            case (id_ex_alu_op)
                5'b10000: pc_next = (alu_result == 1'b1) ? id_ex_pc + id_ex_imm : id_ex_pc + 4; // BEQ
                5'b10001: pc_next = (alu_result == 1'b1) ? id_ex_pc + id_ex_imm : id_ex_pc + 4; // BNE
                5'b10100: pc_next = (alu_result == 1'b1) ? id_ex_pc + id_ex_imm : id_ex_pc + 4; // BLT
                5'b10101: pc_next = (alu_result == 1'b1) ? id_ex_pc + id_ex_imm : id_ex_pc + 4; // BGE
                5'b10110: pc_next = (alu_result == 1'b1) ? id_ex_pc + id_ex_imm : id_ex_pc + 4; // BLTU
                5'b10111: pc_next = (alu_result == 1'b1) ? id_ex_pc + id_ex_imm : id_ex_pc + 4; // BGTU
                default: pc_next = id_ex_pc + 4;
            endcase
        end else if (id_ex_instr[6:0] == 7'b1101111) begin // JAL
            pc_next = id_ex_pc + id_ex_imm;
        end else if (id_ex_instr[6:0] == 7'b1100111) begin // JALR
            pc_next = (id_ex_rs1_data_forwarded + id_ex_imm) & ~1;
        end
    end

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

`ifndef SYNTHESIS
    // Debug logging with $display statements
    always @(posedge clk) begin
        string if_id_instr_str, id_ex_instr_str, ex_mem_instr_str;
        if_id_instr_str = decode_instruction(if_id_instr);
        id_ex_instr_str = decode_instruction(id_ex_instr);
        ex_mem_instr_str = decode_instruction(ex_mem_instr);

        // Log instruction fetch
        $display("Time %0t: IF - PC=0x%h, Instr=0x%h (%s), instr_ready=%b, PC_next=0x%h", $time, if_id_pc, if_id_instr, if_id_instr_str, instr_ready, pc_next);
        
        // Log instruction decode and register reads
        $display("Time %0t: ID - PC=0x%h, Instr=0x%h (%s), rs1=x%0d(0x%h), rs2=x%0d(0x%h), rd=x%0d", 
                    $time, id_ex_pc, id_ex_instr, id_ex_instr_str, id_ex_rs1_addr, id_ex_rs1_data, 
                    id_ex_rs2_addr, id_ex_rs2_data, id_ex_rd_addr);

        // Log data forwarding
        if (rs1_forward_ex || rs1_forward_mem || rs1_forward_wb) begin
            $display("Time %0t: FORWARD - rs1 forwarding: rs1=x%0d, forward_ex=%b, forward_mem=%b, forward_wb=%b, data=0x%h", 
                     $time, rs1, rs1_forward_ex, rs1_forward_mem, rs1_forward_wb, id_ex_rs1_data_forwarded);
        end
        if (rs2_forward_ex || rs2_forward_mem || rs2_forward_wb) begin
            $display("Time %0t: FORWARD - rs2 forwarding: rs2=x%0d, forward_ex=%b, forward_mem=%b, forward_wb=%b, data=0x%h", 
                     $time, rs2, rs2_forward_ex, rs2_forward_mem, rs2_forward_wb, id_ex_rs2_data_forwarded);
        end
        
        // Log data hazard detection
        if ((id_rs1 != 0 && id_rs1 == ex_mem_rd_addr && ex_mem_reg_we) ||
            (id_rs2 != 0 && id_rs2 == ex_mem_rd_addr && ex_mem_reg_we) ||
            (id_rs1 != 0 && id_rs1 == mem_wb_rd_addr && mem_wb_reg_we) ||
            (id_rs2 != 0 && id_rs2 == mem_wb_rd_addr && mem_wb_reg_we) ||
            (id_rs1 != 0 && id_rs1 == wb___rd_addr && wb___reg_we) ||
            (id_rs2 != 0 && id_rs2 == wb___rd_addr && wb___reg_we)) begin
            $display("Time %0t: HAZARD - Data hazard detected: rs1=x%0d, rs2=x%0d, ex_mem_rd=x%0d, mem_wb_rd=x%0d, wb___rd=x%0d", 
                     $time, id_rs1, id_rs2, ex_mem_rd_addr, mem_wb_rd_addr, wb___rd_addr);
        end

        // Log load-use hazard detection
        if (load_use_hazard) begin
            $display("Time %0t: HAZARD - Load-use hazard detected: load_rd=x%0d, next_rs1=x%0d, next_rs2=x%0d", 
                     $time, id_ex_rd_addr, rs1, rs2);
        end

        // Log memory issues
        if (!instr_ready) begin
            $display("Time %0t: STALL - Instruction memory not ready, stalling pipeline", $time);
        end
        if (mem_stall) begin
            $display("Time %0t: STALL - Data memory not ready, stalling pipeline", $time);
        end

        // Log ALU operations
        $display("Time %0t: EX - PC=0x%h, Instr=0x%h (%s) - ALU: op=0x%h, a=0x%h, b=0x%h, result=0x%h, rd=x%0d", 
                    $time, ex_mem_pc, ex_mem_instr, ex_mem_instr_str, alu_op, alu_a, alu_b, alu_result, id_ex_rd_addr);

        // Log memory operations
        if (ex_mem_mem_we) begin
            $display("Time %0t: MEM - Store: addr=0x%h, data=0x%h", 
                     $time, ex_mem_result, ex_mem_rs2_data);
        end
        if (ex_mem_mem_re) begin
            $display("Time %0t: MEM - Load: addr=0x%h, mem_data=0x%h, wb_result=0x%h", 
                     $time, ex_mem_result, mem_data, wb_result);
        end
        if (!ex_mem_mem_we && !ex_mem_mem_re) begin
            $display("Time %0t: MEM - Non-Memory Operation", $time);
        end
        
        // Log register writes
        if (mem_wb_reg_we) begin
            $display("Time %0t: WB - Reg Write: x%d = 0x%h", 
                     $time, mem_wb_rd_addr, mem_wb_result);
        end
        else begin
            $display("Time %0t: WB - Non-Reg Write", $time);
        end
        
        // Log branches and jumps
        if (id_ex_instr[6:0] == 7'b1100011) begin
            case (id_ex_alu_op)
                5'b10000: $display("Time %0t: BRANCH - BEQ: rs1=0x%h, rs2=0x%h, zero=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_zero, alu_zero);
                5'b10001: $display("Time %0t: BRANCH - BNE: rs1=0x%h, rs2=0x%h, zero=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_zero, !alu_zero);
                5'b10100: $display("Time %0t: BRANCH - BLT: rs1=0x%h, rs2=0x%h, negative=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_negative, !alu_negative);
                5'b10101: $display("Time %0t: BRANCH - BGE: rs1=0x%h, rs2=0x%h, negative=%b, zero=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_negative, alu_zero, (!alu_negative || alu_zero));
                5'b10110: $display("Time %0t: BRANCH - BLTU: rs1=0x%h, rs2=0x%h, negative=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_negative, !alu_negative);
                5'b10111: $display("Time %0t: BRANCH - BGEU: rs1=0x%h, rs2=0x%h, negative=%b, zero=%b, taken=%b", 
                                  $time, id_ex_rs1_data, id_ex_rs2_data, alu_negative, alu_zero, (!alu_negative || alu_zero));
            endcase
        end

        $display("--------------------------------");
    end
`endif

endmodule

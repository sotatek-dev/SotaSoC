/* RV32E ALU - Comprehensive implementation */

module rv32e_alu (
    input [4:0] op,
    input [31:0] a,
    input [31:0] b,
    output reg [31:0] result,
    output reg zero_flag,
    output reg negative_flag,
    output reg overflow_flag
);

    // ALU operation codes
    localparam ADD  = 5'b00000;  // Addition
    localparam SLL  = 5'b00001;  // Logical left shift
    localparam SLT  = 5'b00010;  // Set if less than (signed)
    localparam SLTU = 5'b00011;  // Set if less than (unsigned)
    localparam XOR  = 5'b00100;  // Bitwise XOR
    localparam SRL  = 5'b00101;  // Logical right shift
    localparam OR   = 5'b00110;  // Bitwise OR
    localparam AND  = 5'b00111;  // Bitwise AND
    localparam SUB  = 5'b01000;  // Subtraction
    localparam SRA  = 5'b01101;  // Arithmetic right shift
    localparam BEQ  = 5'b10000;  // Set if equal
    localparam BNE  = 5'b10001;  // Set if not equal
    localparam BLT  = 5'b10100;  // Set if less than (signed)
    localparam BGE  = 5'b10101;  // Set if greater than or equal (signed)
    localparam BLTU = 5'b10110;  // Set if less than (unsigned)
    localparam BGEU = 5'b10111;  // Set if greater than or equal (unsigned)

    // Internal signals
    wire [31:0] add_result, sub_result;
    wire [31:0] shift_amount;
    wire [31:0] sll_result, srl_result, sra_result;
    wire add_overflow, sub_overflow;
    
    // Shift amount (only use lower 5 bits for 32-bit shifts)
    assign shift_amount = b[4:0];
    
    // Addition and subtraction
    assign add_result = a + b;
    assign sub_result = a - b;
    
    // Overflow detection for addition and subtraction
    assign add_overflow = (a[31] == 0 && b[31] == 0 && add_result[31] == 1) ||
                         (a[31] == 1 && b[31] == 1 && add_result[31] == 0);
    assign sub_overflow = (a[31] == 0 && b[31] == 1 && sub_result[31] == 1) ||
                         (a[31] == 1 && b[31] == 0 && sub_result[31] == 0);
    
    // Shift operations
    assign sll_result = a << shift_amount;
    assign srl_result = a >> shift_amount;
    assign sra_result = $signed(a) >>> shift_amount;

    always @(*) begin
        case (op)
            ADD:  result = add_result;
            SUB:  result = sub_result;
            AND:  result = a & b;
            OR:   result = a | b;
            XOR:  result = a ^ b;
            SLL:  result = sll_result;
            SRL:  result = srl_result;
            SRA:  result = sra_result;
            SLT:  result = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            SLTU: result = (a < b) ? 32'd1 : 32'd0;
            BEQ:  result = (a == b) ? 32'd1 : 32'd0;
            BNE:  result = (a != b) ? 32'd1 : 32'd0;
            BLT:  result = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            BGE:  result = ($signed(a) >= $signed(b)) ? 32'd1 : 32'd0;
            BLTU: result = (a < b) ? 32'd1 : 32'd0;
            BGEU: result = (a >= b) ? 32'd1 : 32'd0;
            default: result = 32'd0;
        endcase
        
        // Flag generation
        zero_flag = (result == 32'd0);
        negative_flag = result[31];
        overflow_flag = (op == ADD) ? add_overflow : 
                       (op == SUB) ? sub_overflow : 1'b0;
    end

    // Debug logging for ALU operations
    always @(*) begin
        case (op)
            ADD:  $display("Time %0t: ALU - ADD: 0x%h + 0x%h = 0x%h, zero=%b, neg=%b, ovf=%b", 
                          $time, a, b, result, zero_flag, negative_flag, overflow_flag);
            SUB:  $display("Time %0t: ALU - SUB: 0x%h - 0x%h = 0x%h, zero=%b, neg=%b, ovf=%b", 
                          $time, a, b, result, zero_flag, negative_flag, overflow_flag);
            AND:  $display("Time %0t: ALU - AND: 0x%h & 0x%h = 0x%h, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            OR:   $display("Time %0t: ALU - OR:  0x%h | 0x%h = 0x%h, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            XOR:  $display("Time %0t: ALU - XOR: 0x%h ^ 0x%h = 0x%h, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            SLL:  $display("Time %0t: ALU - SLL: 0x%h << %d = 0x%h, zero=%b, neg=%b", 
                          $time, a, shift_amount, result, zero_flag, negative_flag);
            SRL:  $display("Time %0t: ALU - SRL: 0x%h >> %d = 0x%h, zero=%b, neg=%b", 
                          $time, a, shift_amount, result, zero_flag, negative_flag);
            SRA:  $display("Time %0t: ALU - SRA: 0x%h >>> %d = 0x%h, zero=%b, neg=%b", 
                          $time, a, shift_amount, result, zero_flag, negative_flag);
            SLT:  $display("Time %0t: ALU - SLT: 0x%h < 0x%h = %0d, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            SLTU: $display("Time %0t: ALU - SLTU: 0x%h < 0x%h = %0d, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            BEQ:  $display("Time %0t: ALU - BEQ: 0x%h == 0x%h = %0d, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            BNE:  $display("Time %0t: ALU - BNE: 0x%h != 0x%h = %0d, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            BLT:  $display("Time %0t: ALU - BLT: 0x%h < 0x%h = %0d, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            BGE: $display("Time %0t: ALU - BGE: 0x%h >= 0x%h = %0d, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            BLTU:  $display("Time %0t: ALU - SGT: 0x%h < 0x%h = %0d, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            BGEU: $display("Time %0t: ALU - BGEU: 0x%h >= 0x%h = %0d, zero=%b, neg=%b", 
                          $time, a, b, result, zero_flag, negative_flag);
            default: $display("Time %0t: ALU - UNKNOWN OP: %b, a=0x%h, b=0x%h, result=0x%h", 
                             $time, op, a, b, result);
        endcase
    end

endmodule 
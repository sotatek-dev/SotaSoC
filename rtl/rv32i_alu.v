/* RV32I ALU - Comprehensive implementation */

module rv32i_alu (
    input [3:0] op,
    input [31:0] a,
    input [31:0] b,
    output reg [31:0] result
    // output reg zero_flag,
    // output reg negative_flag,
    // output reg overflow_flag
);

    // ALU operation codes
    localparam ADD  = 4'b0000;  // Addition
    localparam SLL  = 4'b0001;  // Logical left shift
    localparam SLT  = 4'b0010;  // Set if less than (signed)
    localparam SLTU = 4'b0011;  // Set if less than (unsigned)
    localparam XOR  = 4'b0100;  // Bitwise XOR
    localparam SRL  = 4'b0101;  // Logical right shift
    localparam OR   = 4'b0110;  // Bitwise OR
    localparam AND  = 4'b0111;  // BitwFise AND
    localparam SUB  = 4'b1000;  // Subtraction
    localparam SRA  = 4'b1101;  // Arithmetic right shift

    // Internal signals
    wire [31:0] add_result, sub_result;
    wire [31:0] shift_amount;
    wire [31:0] sll_result, srl_result, sra_result;
    // wire add_overflow, sub_overflow;
    
    // Shift amount (only use lower 5 bits for 32-bit shifts)
    assign shift_amount = b[4:0];
    
    // Addition and subtraction
    assign add_result = a + b;
    assign sub_result = a - b;
    
    // // Overflow detection for addition and subtraction
    // assign add_overflow = (a[31] == 0 && b[31] == 0 && add_result[31] == 1) ||
    //                      (a[31] == 1 && b[31] == 1 && add_result[31] == 0);
    // assign sub_overflow = (a[31] == 0 && b[31] == 1 && sub_result[31] == 1) ||
    //                      (a[31] == 1 && b[31] == 0 && sub_result[31] == 0);
    
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
            default: result = 32'd0;
        endcase
        
        // Flag generation
        // zero_flag = (result == 32'd0);
        // negative_flag = result[31];
        // overflow_flag = (op == ADD) ? add_overflow : 
        //                (op == SUB) ? sub_overflow : 1'b0;
    end

    // Debug logging for ALU operations
    always @(*) begin
        case (op)
            ADD:  $display("Time %0t: ALU - ADD: 0x%h + 0x%h = 0x%h", 
                          $time, a, b, result);
            SUB:  $display("Time %0t: ALU - SUB: 0x%h - 0x%h = 0x%h", 
                          $time, a, b, result);
            AND:  $display("Time %0t: ALU - AND: 0x%h & 0x%h = 0x%h", 
                          $time, a, b, result);
            OR:   $display("Time %0t: ALU - OR:  0x%h | 0x%h = 0x%h", 
                          $time, a, b, result);
            XOR:  $display("Time %0t: ALU - XOR: 0x%h ^ 0x%h = 0x%h", 
                          $time, a, b, result);
            SLL:  $display("Time %0t: ALU - SLL: 0x%h << %d = 0x%h", 
                          $time, a, shift_amount, result);
            SRL:  $display("Time %0t: ALU - SRL: 0x%h >> %d = 0x%h", 
                          $time, a, shift_amount, result);
            SRA:  $display("Time %0t: ALU - SRA: 0x%h >>> %d = 0x%h", 
                          $time, a, shift_amount, result);
            SLT:  $display("Time %0t: ALU - SLT: 0x%h < 0x%h = %0d", 
                          $time, a, b, result);
            SLTU: $display("Time %0t: ALU - SLTU: 0x%h < 0x%h = %0d", 
                          $time, a, b, result);
            default: $display("Time %0t: ALU - UNKNOWN OP: %b, a=0x%h, b=0x%h, result=0x%h", 
                             $time, op, a, b, result);
        endcase
    end

endmodule 
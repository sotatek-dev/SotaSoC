/* RV32I ALU - Optimized implementation for reduced delay */

module rv32i_alu (
    input [4:0] op,
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
    localparam AND  = 4'b0111;  // Bitwise AND
    localparam SUB  = 4'b1000;  // Subtraction
    localparam SRA  = 4'b1101;  // Arithmetic right shift

    // Operation type detection (pre-computed for faster routing)
    wire is_bitwise = (op == AND) || (op == OR) || (op == XOR);
    wire is_arithmetic = (op == ADD) || (op == SUB);
    wire is_comparison = (op == SLT) || (op == SLTU);
    wire is_shift = (op == SLL) || (op == SRL) || (op == SRA);
    
    // Internal signals - only compute what's needed
    wire [31:0] add_result, sub_result;
    wire [31:0] shift_result;
    wire [31:0] comparison_result;
    wire [31:0] bitwise_result;
    wire add_overflow, sub_overflow;
    
    // Shift amount (only use lower 5 bits for 32-bit shifts)
    wire [4:0] shift_amount = b[4:0];
    
    // Conditional arithmetic computation
    assign add_result = is_arithmetic & (op == ADD) ? a + b : 32'd0;
    assign sub_result = is_arithmetic & (op == SUB) ? a - b : 32'd0;
    
    // // Simplified overflow detection (only for arithmetic operations)
    // assign add_overflow = is_arithmetic & (op == ADD) & 
    //                      ((a[31] == b[31]) & (add_result[31] != a[31]));
    // assign sub_overflow = is_arithmetic & (op == SUB) & 
    //                      ((a[31] != b[31]) & (sub_result[31] != a[31]));
    
    // Optimized shift implementation
    // Use conditional shifts to reduce logic depth
    // SRA must be in separate assignment to preserve signed context (nested ternary strips signedness)
    wire [31:0] sra_result;
    assign sra_result = $signed(a) >>> shift_amount;
    assign shift_result = (is_shift & (op == SLL)) ? a << shift_amount :
                         (is_shift & (op == SRL)) ? a >> shift_amount :
                         (is_shift & (op == SRA)) ? sra_result :
                         32'd0;
    
    // Optimized comparison operations
    assign comparison_result = (is_comparison & (op == SLT)) ? 
                              ($signed(a) < $signed(b)) ? 32'd1 : 32'd0 :
                              (is_comparison & (op == SLTU)) ? 
                              (a < b) ? 32'd1 : 32'd0 :
                              32'd0;
    
    // Optimized bitwise operations
    assign bitwise_result = (is_bitwise & (op == AND)) ? a & b :
                           (is_bitwise & (op == OR)) ? a | b :
                           (is_bitwise & (op == XOR)) ? a ^ b :
                           32'd0;

    // Result selection using hierarchical multiplexing
    always @(*) begin
        case (1'b1)  // Priority-based selection
            is_bitwise:    result = bitwise_result;
            is_arithmetic: result = (op == ADD) ? add_result : sub_result;
            is_comparison: result = comparison_result;
            is_shift:      result = shift_result;
            default:       result = 32'd0;
        endcase
        
        // Flag generation (optimized)
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


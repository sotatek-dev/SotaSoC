/* RV32E ALU - Comprehensive implementation */

module rv32e_alu (
    input [3:0] op,
    input [31:0] a,
    input [31:0] b,
    output reg [31:0] result,
    output reg zero_flag,
    output reg negative_flag,
    output reg overflow_flag
);

    // ALU operation codes
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
            SEQ:  result = (a == b) ? 32'd1 : 32'd0;
            SNE:  result = (a != b) ? 32'd1 : 32'd0;
            SGE:  result = ($signed(a) >= $signed(b)) ? 32'd1 : 32'd0;
            SGEU: result = (a >= b) ? 32'd1 : 32'd0;
            SGT:  result = ($signed(a) > $signed(b)) ? 32'd1 : 32'd0;
            SGTU: result = (a > b) ? 32'd1 : 32'd0;
            default: result = 32'd0;
        endcase
        
        // Flag generation
        zero_flag = (result == 32'd0);
        negative_flag = result[31];
        overflow_flag = (op == ADD) ? add_overflow : 
                       (op == SUB) ? sub_overflow : 1'b0;
    end

endmodule 
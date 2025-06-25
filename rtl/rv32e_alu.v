/* Simple ALU for testing */

module rv32e_alu (
    input [3:0] op,
    input [31:0] a,
    input [31:0] b,
    output reg [31:0] result
);

    // ALU operations
    localparam ADD = 4'b0000;
    localparam SUB = 4'b0001;
    localparam AND = 4'b0010;
    localparam OR  = 4'b0011;
    localparam XOR = 4'b0100;

    always @(*) begin
        case (op)
            ADD: result = a + b;
            SUB: result = a - b;
            AND: result = a & b;
            OR:  result = a | b;
            XOR: result = a ^ b;
            default: result = 32'd0;
        endcase
    end

endmodule 
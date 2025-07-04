/* Testbench wrapper for RV32I ALU with cocotb */

module test_rv32i_alu_tb;
    // Test signals
    reg [4:0] op;
    reg [31:0] a;
    reg [31:0] b;
    wire [31:0] result;
    wire zero_flag;
    wire negative_flag;
    wire overflow_flag;

    // Instantiate the ALU
    rv32i_alu dut (
        .op(op),
        .a(a),
        .b(b),
        .result(result),
        .zero_flag(zero_flag),
        .negative_flag(negative_flag),
        .overflow_flag(overflow_flag)
    );

    // Waveform dump for cocotb
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("vcd/test_rv32i_alu_tb.vcd");
        $dumpvars(0, test_rv32i_alu_tb);
    end
    `endif

endmodule 
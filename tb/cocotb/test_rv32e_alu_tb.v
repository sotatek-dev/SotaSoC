/* Simple testbench wrapper for cocotb */

module test_rv32e_alu_tb;
    // Test signals
    reg [3:0] op;
    reg [31:0] a;
    reg [31:0] b;
    wire [31:0] result;

    // Instantiate the ALU
    rv32e_alu dut (
        .op(op),
        .a(a),
        .b(b),
        .result(result)
    );

    // Waveform dump for cocotb
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("vcd/test_rv32e_alu_tb.vcd");
        $dumpvars(0, test_rv32e_alu_tb);
    end
    `endif

endmodule 
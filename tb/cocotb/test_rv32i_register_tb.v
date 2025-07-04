/* Testbench wrapper for RV32I Register File with cocotb */

module test_rv32i_register_tb;
    // Test signals
    reg clk;
    reg rst_n;
    reg [4:0] rs1_addr;
    reg [4:0] rs2_addr;
    wire [31:0] rs1_data;
    wire [31:0] rs2_data;
    reg [4:0] rd_addr;
    reg [31:0] rd_data;
    reg rd_we;

    // Instantiate the register file
    rv32i_register dut (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(rs1_addr),
        .rs2_addr(rs2_addr),
        .rs1_data(rs1_data),
        .rs2_data(rs2_data),
        .rd_addr(rd_addr),
        .rd_data(rd_data),
        .rd_we(rd_we)
    );

    // Waveform dump for cocotb
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("vcd/test_rv32i_register_tb.vcd");
        $dumpvars(0, test_rv32i_register_tb);
    end
    `endif

endmodule 
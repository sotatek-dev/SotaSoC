/* Testbench wrapper for RV32C Decompression Module with cocotb */

module test_rv32c_decompress_tb;
    // Test signals
    reg [15:0] instr_16bit;
    wire [31:0] instr_32bit;
    wire is_valid;

    // Instantiate the decompression module
    rv32c_decompress dut (
        .instr_16bit(instr_16bit),
        .instr_32bit(instr_32bit),
        .is_valid(is_valid)
    );

    // Waveform dump for cocotb
    initial begin
        $dumpfile("vcd/test_rv32c_decompress_tb.vcd");
        $dumpvars(0, test_rv32c_decompress_tb);
    end

endmodule

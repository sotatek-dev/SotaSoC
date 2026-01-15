/* RV32I Core Testbench - cocotb wrapper */

module test_rv32i_core_tb;
    // Clock and reset
    reg clk;
    reg rst_n;
    
    // Memory interface
    wire [31:0] instr_data;
    wire [31:0] mem_data;
    wire instr_ready;
    wire mem_ready;
    wire [31:0] instr_addr;
    wire [31:0] mem_addr;
    wire [31:0] mem_wdata;
    wire [2:0] mem_flag;
    wire mem_we;
    wire mem_re;
    
    // Instantiate the core
    rv32i_core core (
        .clk(clk),
        .rst_n(rst_n),
        .i_instr_data(instr_data),
        .i_mem_data(mem_data),
        .i_instr_ready(instr_ready),
        .i_mem_ready(mem_ready),
        .o_instr_addr(instr_addr),
        .o_mem_addr(mem_addr),
        .o_mem_wdata(mem_wdata),
        .o_mem_flag(mem_flag),
        .o_mem_we(mem_we),
        .o_mem_re(mem_re)
    );

    // Monitor signals
    // always @(posedge clk) begin
    //     string instr_str;
    //     instr_str = core.decode_instruction(instr_data);
    //     $display("Time %0t: TESTBENCH - PC=%h, Instr=%h (%s), Mem_Addr=%h, Mem_Data=%h, Mem_Wdata=%h, Mem_WE=%b, Mem_RE=%b", 
    //              $time, instr_addr, instr_data, instr_str, mem_addr, mem_data, mem_wdata, mem_we, mem_re);
    // end

    // Waveform dump for cocotb
    initial begin
        $dumpfile("vcd/test_rv32i_core_tb.vcd");
        $dumpvars(0, test_rv32i_core_tb);
    end

endmodule 
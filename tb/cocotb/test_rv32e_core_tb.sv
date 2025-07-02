/* RV32E Core Testbench - cocotb wrapper */

module test_rv32e_core_tb;
    // Clock and reset
    reg clk;
    reg rst_n;
    
    // Memory interface
    reg [31:0] instr_data;
    reg [31:0] mem_data;
    wire [31:0] instr_addr;
    wire [31:0] mem_addr;
    wire [31:0] mem_wdata;
    wire mem_we;
    wire mem_re;
    
    // Instantiate the core
    rv32e_core core (
        .clk(clk),
        .rst_n(rst_n),
        .instr_data(instr_data),
        .mem_data(mem_data),
        .instr_addr(instr_addr),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_we(mem_we),
        .mem_re(mem_re)
    );

    // Monitor signals
    // always @(posedge clk) begin
    //     string instr_str;
    //     instr_str = core.decode_instruction(instr_data);
    //     $display("Time %0t: TESTBENCH - PC=%h, Instr=%h (%s), Mem_Addr=%h, Mem_Data=%h, Mem_Wdata=%h, Mem_WE=%b, Mem_RE=%b", 
    //              $time, instr_addr, instr_data, instr_str, mem_addr, mem_data, mem_wdata, mem_we, mem_re);
    // end

    // Waveform dump for cocotb
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("vcd/test_rv32e_core_tb.vcd");
        $dumpvars(0, test_rv32e_core_tb);
    end
    `endif

endmodule 
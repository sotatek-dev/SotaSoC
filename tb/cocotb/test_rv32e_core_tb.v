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
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    // Test stimulus
    initial begin
        // Initialize signals
        rst_n = 0;
        instr_data = 32'h00000013; // NOP
        mem_data = 32'h00000000;
        
        // Reset
        #20;
        rst_n = 1;
        
        // Let the simulation run
        #1000;
        $finish;
    end
    
    // Monitor signals
    always @(posedge clk) begin
        $display("Time %0t: TESTBENCH - PC=%h, Instr=%h, Mem_Addr=%h, Mem_Data=%h, Mem_Wdata=%h, Mem_WE=%b, Mem_RE=%b", 
                 $time, instr_addr, instr_data, mem_addr, mem_data, mem_wdata, mem_we, mem_re);
    end

endmodule 
/* Simple ALU testbench */

module tb_rv32e_alu;

    // Clock and reset
    reg clk;
    reg rst_n;
    
    // Test signals
    reg [3:0] op;
    reg [31:0] a;
    reg [31:0] b;
    wire [31:0] result;

    // Instantiate the ALU
    rv32e_alu alu_inst (
        .op(op),
        .a(a),
        .b(b),
        .result(result)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset generation
    initial begin
        rst_n = 0;
        #20;
        rst_n = 1;
    end

    // Waveform dump for cocotb
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("rv32e_alu.vcd");
        $dumpvars(0, tb_rv32e_alu);
    end
    `endif

    // Simple test stimulus
    initial begin
        // Initialize signals
        op = 4'b0000;
        a = 32'd0;
        b = 32'd0;
        
        // Wait for reset
        @(posedge clk);
        @(posedge clk);
        
        // Test addition
        op = 4'b0000;
        a = 32'd10;
        b = 32'd20;
        @(posedge clk);
        $display("ADD: %d + %d = %d", a, b, result);
        
        // Test AND
        op = 4'b0010;
        a = 32'h0F0F0F0F;
        b = 32'h00FF00FF;
        @(posedge clk);
        $display("AND: %h & %h = %h", a, b, result);
        
        // Test OR
        op = 4'b0011;
        a = 32'h0F0F0F0F;
        b = 32'h00FF00FF;
        @(posedge clk);
        $display("OR:  %h | %h = %h", a, b, result);
        
        // Test XOR
        op = 4'b0100;
        a = 32'h0F0F0F0F;
        b = 32'h00FF00FF;
        @(posedge clk);
        $display("XOR: %h ^ %h = %h", a, b, result);
        
        // Test subtraction
        op = 4'b0001;
        a = 32'd30;
        b = 32'd10;
        @(posedge clk);
        $display("SUB: %d - %d = %d", a, b, result);
        
        $display("All tests completed!");
        $finish;
    end

endmodule 
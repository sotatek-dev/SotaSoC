/* Testbench for RV32I Register File */

`timescale 1ns/1ps

module tb_rv32i_register;
    
    // Testbench signals
    reg clk;
    reg rst_n;
    reg [3:0] rs1_addr, rs2_addr, rd_addr;
    reg [31:0] rd_data;
    reg rd_we;
    wire [31:0] rs1_data, rs2_data;
    
    // Instantiate the register file
    rv32i_register reg_file (
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
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    // Test stimulus
    initial begin
        // Initialize signals
        rst_n = 1;
        rs1_addr = 0;
        rs2_addr = 0;
        rd_addr = 0;
        rd_data = 0;
        rd_we = 0;
        
        // Wait a few clock cycles
        #20;
        
        // Test 1: Reset functionality
        $display("Test 1: Reset functionality");
        rst_n = 0;
        #10;
        rst_n = 1;
        #10;
        
        // Verify all registers are zero after reset
        for (int i = 0; i < 16; i = i + 1) begin
            rs1_addr = i;
            #1;
            if (rs1_data !== 32'd0) begin
                $display("ERROR: Register %0d not zero after reset, got %h", i, rs1_data);
            end else begin
                $display("Register %0d correctly reset to zero", i);
            end
        end
        
        // Test 2: Write to registers
        $display("\nTest 2: Write to registers");
        rd_we = 1;
        
        // Write test data to registers 1-15
        for (int i = 1; i < 16; i = i + 1) begin
            rd_addr = i;
            rd_data = 32'h1000 + i;
            #10;
        end
        
        rd_we = 0;
        
        // Test 3: Read from registers
        $display("\nTest 3: Read from registers");
        for (int i = 0; i < 16; i = i + 1) begin
            rs1_addr = i;
            #1;
            if (i == 0) begin
                if (rs1_data !== 32'd0) begin
                    $display("ERROR: Register x0 should always be zero, got %h", rs1_data);
                end else begin
                    $display("Register x0 correctly reads as zero");
                end
            end else begin
                if (rs1_data !== (32'h1000 + i)) begin
                    $display("ERROR: Register %0d expected %h, got %h", i, 32'h1000 + i, rs1_data);
                end else begin
                    $display("Register %0d correctly reads %h", i, rs1_data);
                end
            end
        end
        
        // Test 4: Dual read ports
        $display("\nTest 4: Dual read ports");
        rs1_addr = 5;
        rs2_addr = 10;
        #1;
        if (rs1_data !== 32'h1005) begin
            $display("ERROR: rs1_data expected %h, got %h", 32'h1005, rs1_data);
        end else begin
            $display("rs1_data correctly reads %h", rs1_data);
        end
        if (rs2_data !== 32'h100A) begin
            $display("ERROR: rs2_data expected %h, got %h", 32'h100A, rs2_data);
        end else begin
            $display("rs2_data correctly reads %h", rs2_data);
        end
        
        // Test 5: Write to x0 (should be ignored)
        $display("\nTest 5: Write to x0 (should be ignored)");
        rd_we = 1;
        rd_addr = 0;
        rd_data = 32'hDEADBEEF;
        #10;
        rd_we = 0;
        
        rs1_addr = 0;
        #1;
        if (rs1_data !== 32'd0) begin
            $display("ERROR: Register x0 should still be zero after write attempt, got %h", rs1_data);
        end else begin
            $display("Register x0 correctly remains zero after write attempt");
        end
        
        // Test 6: Update existing register
        $display("\nTest 6: Update existing register");
        rd_we = 1;
        rd_addr = 7;
        rd_data = 32'hCAFEBABE;
        #10;
        rd_we = 0;
        
        rs1_addr = 7;
        #1;
        if (rs1_data !== 32'hCAFEBABE) begin
            $display("ERROR: Register 7 expected %h, got %h", 32'hCAFEBABE, rs1_data);
        end else begin
            $display("Register 7 correctly updated to %h", rs1_data);
        end
        
        // Test 7: Read from x0 with different addresses
        $display("\nTest 7: Read from x0 with different addresses");
        rs1_addr = 0;
        rs2_addr = 0;
        #1;
        if (rs1_data !== 32'd0 || rs2_data !== 32'd0) begin
            $display("ERROR: Both read ports should return zero for x0");
        end else begin
            $display("Both read ports correctly return zero for x0");
        end
        
        $display("\nAll tests completed!");
        $finish;
    end
    
    // Optional: Generate VCD file for waveform viewing
    initial begin
        $dumpfile("tb_rv32i_register.vcd");
        $dumpvars(0, tb_rv32i_register);
    end

endmodule 
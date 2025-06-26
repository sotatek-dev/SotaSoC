/* RV32E Register File - 16 registers (x0-x15) */

module rv32e_register (
    input wire clk,
    input wire rst_n,
    
    // Read ports
    input wire [3:0] rs1_addr,    // Source register 1 address
    input wire [3:0] rs2_addr,    // Source register 2 address
    output wire [31:0] rs1_data,  // Source register 1 data
    output wire [31:0] rs2_data,  // Source register 2 data
    
    // Write port
    input wire [3:0] rd_addr,     // Destination register address
    input wire [31:0] rd_data,    // Data to write
    input wire rd_we              // Write enable
);

    // Register file storage - 16 registers of 32 bits each
    reg [31:0] registers [0:15];
    
    // Read operations (asynchronous)
    assign rs1_data = (rs1_addr == 4'd0) ? 32'd0 : registers[rs1_addr];
    assign rs2_data = (rs2_addr == 4'd0) ? 32'd0 : registers[rs2_addr];
    
    // Write operation (synchronous)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all registers to zero
            registers[0] <= 32'd0;
            registers[1] <= 32'd0;
            registers[2] <= 32'd0;
            registers[3] <= 32'd0;
            registers[4] <= 32'd0;
            registers[5] <= 32'd0;
            registers[6] <= 32'd0;
            registers[7] <= 32'd0;
            registers[8] <= 32'd0;
            registers[9] <= 32'd0;
            registers[10] <= 32'd0;
            registers[11] <= 32'd0;
            registers[12] <= 32'd0;
            registers[13] <= 32'd0;
            registers[14] <= 32'd0;
            registers[15] <= 32'd0;
            
            $display("Time %0t: REG - Register file reset", $time);
        end else if (rd_we && rd_addr != 4'd0) begin
            // Write to register (x0 is always zero, so don't write to it)
            registers[rd_addr] <= rd_data;
            $display("Time %0t: REG - Write: x%d = 0x%h (was 0x%h)", 
                     $time, rd_addr, rd_data, registers[rd_addr]);
        end
    end

endmodule

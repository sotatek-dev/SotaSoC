/* RV32I Register File - 16 registers (x0-x15) */

`include "debug_defines.vh"

module rv32i_register #(
    parameter REG_NUM = 16
) (
    input wire clk,
    input wire rst_n,

    // Read ports
    input wire [4:0] rs1_addr,    // Source register 1 address
    input wire [4:0] rs2_addr,    // Source register 2 address
    output wire [31:0] rs1_data,  // Source register 1 data
    output wire [31:0] rs2_data,  // Source register 2 data

    // Write port
    input wire [4:0] rd_addr,     // Destination register address
    input wire [31:0] rd_data,    // Data to write
    input wire rd_we              // Write enable
);

    wire [4:0] rs1_addr_internal = REG_NUM == 16 ? {1'b0, rs1_addr[3:0]} : rs1_addr;
    wire [4:0] rs2_addr_internal = REG_NUM == 16 ? {1'b0, rs2_addr[3:0]} : rs2_addr;
    wire [4:0] rd_addr_internal = REG_NUM == 16 ? {1'b0, rd_addr[3:0]} : rd_addr;

    // Register file storage - 32 registers of 32 bits each
    // We define 32 registers here, but only use REG_NUM registers.
    // The synthesis tool will optimize the unused registers.
    reg [31:0] registers [0:31];

    // Read operations (asynchronous)
    assign rs1_data = (rs1_addr_internal == 5'd0) ? 32'd0 : registers[rs1_addr_internal];
    assign rs2_data = (rs2_addr_internal == 5'd0) ? 32'd0 : registers[rs2_addr_internal];

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
            registers[16] <= 32'd0;
            registers[17] <= 32'd0;
            registers[18] <= 32'd0;
            registers[19] <= 32'd0;
            registers[20] <= 32'd0;
            registers[21] <= 32'd0;
            registers[22] <= 32'd0;
            registers[23] <= 32'd0;
            registers[24] <= 32'd0;
            registers[25] <= 32'd0;
            registers[26] <= 32'd0;
            registers[27] <= 32'd0;
            registers[28] <= 32'd0;
            registers[29] <= 32'd0;
            registers[30] <= 32'd0;
            registers[31] <= 32'd0;
            `DEBUG_PRINT(("Time %0t: REG - Register file reset", $time));
        end else if (rd_we && rd_addr_internal != 5'd0) begin
            // Write to register (x0 is always zero, so don't write to it)
            registers[rd_addr_internal] <= rd_data;
            if (rd_data != registers[rd_addr]) begin
                `DEBUG_PRINT(("Time %0t: REG - Write: x%0d = 0x%h (was 0x%h)", 
                         $time, rd_addr_internal, rd_data, registers[rd_addr_internal]));
            end
        end
    end

endmodule

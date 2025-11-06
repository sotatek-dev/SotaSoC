/* UART Controller
 * 
 * This controller handles memory-mapped UART register access:
 * - 0x0: TX Data (write-only)
 * - 0x4: Control (read/write)
 * - 0x8: RX Data (read-only)
 * - 0xC: RX Control (read/write)
 */

module uart_ctl (
    input wire clk,
    input wire rst_n,
    
    // Memory-mapped interface
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output reg [31:0] mem_rdata,
    
    // UART TX interface
    output wire uart_tx_en,
    output wire [7:0] uart_tx_data,
    input wire uart_tx_busy,
    
    // UART RX interface
    output wire uart_rx_en,
    input wire uart_rx_break,
    input wire uart_rx_valid,
    input wire [7:0] uart_rx_data
);

    // Internal registers used by macros
    reg [7:0] uart_tx_data_reg;
    reg uart_tx_en_reg;
    reg uart_rx_en_reg;
    reg uart_rx_break_reg;
    reg uart_rx_valid_reg;

    // Assign outputs from registers
    assign uart_tx_en = uart_tx_en_reg;
    assign uart_tx_data = uart_tx_data_reg;
    assign uart_rx_en = uart_rx_en_reg;

    // Include UART defines from shared header
    `include "uart_defines.vh"

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            uart_tx_data_reg <= 8'h0;
            uart_tx_en_reg <= 1'b0;
            uart_rx_en_reg <= 1'b0;
            uart_rx_break_reg <= 1'b0;
            uart_rx_valid_reg <= 1'b0;
            mem_rdata <= 32'h0;
        end else begin
            // Default values
            uart_tx_en_reg <= 1'b0;
            uart_rx_break_reg <= uart_rx_break;
            // This signal is only active for 1 cycle, so we need to latch it
            if (uart_rx_valid) begin
                uart_rx_valid_reg <= 1'b1;
            end
            
            // Handle memory requests
            if (mem_we || mem_re) begin
                if (mem_we) begin
                    // Write operations
                    case (mem_addr[3:0])
                        4'h0: `UART_WRITE_TX_DATA(mem_wdata)
                        4'h4: `UART_WRITE_CONTROL(mem_wdata)
                        4'h8: `UART_WRITE_RX_DATA_IGNORED(mem_wdata)
                        4'hC: `UART_WRITE_RX_CONTROL(mem_wdata)
                        default: `UART_WRITE_RESERVED(mem_addr, mem_wdata)
                    endcase
                end else begin
                    // Read operations
                    case (mem_addr[3:0])
                        4'h0: `UART_READ_TX_DATA(mem_rdata)
                        4'h4: `UART_READ_CONTROL(mem_rdata)
                        4'h8: `UART_READ_RX_DATA(mem_rdata)
                        4'hC: `UART_READ_RX_CONTROL(mem_rdata)
                        default: `UART_READ_RESERVED(mem_rdata, mem_addr)
                    endcase
                end
            end
        end
    end

endmodule


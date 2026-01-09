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

    input wire uart_request,

    // Memory-mapped interface
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output wire [31:0] mem_rdata,
    
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

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            uart_tx_data_reg <= 8'h0;
            uart_tx_en_reg <= 1'b0;
            uart_rx_en_reg <= 1'b0;
            uart_rx_break_reg <= 1'b0;
            uart_rx_valid_reg <= 1'b0;
        end else begin
            // Default values
            uart_tx_en_reg <= 1'b0;
            uart_rx_break_reg <= uart_rx_break;
            // This signal is only active for 1 cycle, so we need to latch it
            if (uart_rx_valid) begin
                uart_rx_valid_reg <= 1'b1;
            end
            
            // Handle memory requests
            if (uart_request && mem_we) begin
                // Write operations
                case (mem_addr[3:0])
                    4'h0: uart_tx_data_reg <= mem_wdata[7:0];
                    4'h4: uart_tx_en_reg <= mem_wdata[1];
                    4'h8: ;
                    4'hC: begin
                            uart_rx_valid_reg <= mem_wdata[0];
                            uart_rx_en_reg <= mem_wdata[1];
                            uart_rx_break_reg <= mem_wdata[2];
                            
                        end
                    default: ;
                endcase

                case (mem_addr[3:0])
                    4'h0: `DEBUG_PRINT(("Time %0t: UART_MEM - TX Data Write: data=0x%02h (%c)",
                                $time, mem_wdata[7:0], mem_wdata[7:0]));
                    4'h4: `DEBUG_PRINT(("Time %0t: UART_MEM - Control Write: ctrl=0x%08h", $time, mem_wdata));
                    4'h8: `DEBUG_PRINT(("Time %0t: UART_MEM - Invalid write address: addr=0x%08h", $time, mem_addr));
                    4'hC: `DEBUG_PRINT(("Time %0t: UART_MEM - RX Control Write: ctrl=0x%08h", $time, mem_wdata));
                    default: `DEBUG_PRINT(("Time %0t: UART_MEM - Invalid write address: addr=0x%08h", $time, mem_addr));
                endcase
            end
        end
    end

    wire [31:0] uart_mem_rdata = (mem_addr[3:0] == 4'h0) ? 32'h00000000 :
                                (mem_addr[3:0] == 4'h4) ? {31'b0, uart_tx_busy} :
                                (mem_addr[3:0] == 4'h8) ? {24'b0, uart_rx_data} :
                                (mem_addr[3:0] == 4'hC) ? {29'b0, uart_rx_break_reg, uart_rx_en_reg, uart_rx_valid_reg} :
                                32'h00000000;
    assign mem_rdata = (uart_request && mem_re) ? uart_mem_rdata : 32'h00000000;

    always @(*) begin
        if (uart_request && mem_re) begin
            case (mem_addr[3:0])
                4'h0: `DEBUG_PRINT(("Time %0t: UART_MEM - TX Data Read (write-only): data=0x00000000", $time));
                4'h4: `DEBUG_PRINT(("Time %0t: UART_MEM - Control Read: ctrl=0x%08h, busy=%b",
                                    $time, {31'b0, uart_tx_busy}, uart_tx_busy));
                4'h8: `DEBUG_PRINT(("Time %0t: UART_MEM - RX Data Read: data=0x%08h",
                                    $time, {24'b0, uart_rx_data}));
                4'hC: `DEBUG_PRINT(("Time %0t: UART_MEM - RX Control Read: ctrl=0x%08h",
                                    $time, {29'b0, uart_rx_break_reg, uart_rx_en_reg, uart_rx_valid_reg}));
                default: `DEBUG_PRINT(("Time %0t: UART_MEM - Invalid read address: addr=0x%08h", $time, mem_addr));
            endcase
        end
    end
endmodule


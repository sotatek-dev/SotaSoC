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

    // UART Register Write Macros
    `define UART_WRITE_TX_DATA(wdata) \
        begin \
            uart_tx_data_reg <= wdata[7:0]; \
            `DEBUG_PRINT(("Time %0t: UART_MEM - TX Data Write: data=0x%02h (%c)", \
                    $time, wdata[7:0], wdata[7:0])); \
        end

    `define UART_WRITE_CONTROL(wdata) \
        begin \
            uart_tx_en_reg <= wdata[1]; \
            `DEBUG_PRINT(("Time %0t: UART_MEM - Control Write: ctrl=0x%08h", \
                    $time, wdata)); \
        end

    `define UART_WRITE_RX_DATA_IGNORED(wdata) \
        begin \
            `DEBUG_PRINT(("Time %0t: UART_MEM - RX Data Write: ignored", $time)); \
        end

    `define UART_WRITE_RX_CONTROL(wdata) \
        begin \
            uart_rx_valid_reg <= wdata[0]; \
            uart_rx_en_reg <= wdata[1]; \
            uart_rx_break_reg <= wdata[2]; \
            `DEBUG_PRINT(("Time %0t: UART_MEM - RX Control Write: ctrl=0x%08h", \
                    $time, wdata)); \
        end

    `define UART_WRITE_RESERVED(addr, wdata) \
        begin \
            `DEBUG_PRINT(("Time %0t: UART_MEM - Reserved register write: addr=0x%08h, data=0x%08h", \
                    $time, addr, wdata)); \
        end

    // UART Register Read Macros
    `define UART_READ_TX_DATA(rdata) \
        begin \
            rdata <= 32'h00000000; \
            `DEBUG_PRINT(("Time %0t: UART_MEM - TX Data Read (write-only): data=0x00000000", $time)); \
        end

    `define UART_READ_CONTROL(rdata) \
        begin \
            rdata <= {31'b0, uart_tx_busy}; \
            `DEBUG_PRINT(("Time %0t: UART_MEM - Control Read: ctrl=0x%08h, busy=%b", \
                    $time, {31'b0, uart_tx_busy}, uart_tx_busy)); \
        end

    `define UART_READ_RX_DATA(rdata) \
        begin \
            rdata <= {24'b0, uart_rx_data}; \
            `DEBUG_PRINT(("Time %0t: UART_MEM - RX Data Read: data=0x%08h", \
                    $time, {24'b0, uart_rx_data})); \
        end

    `define UART_READ_RX_CONTROL(rdata) \
        begin \
            rdata <= {29'b0, uart_rx_break_reg, uart_rx_en_reg, uart_rx_valid_reg}; \
            `DEBUG_PRINT(("Time %0t: UART_MEM - RX Control Read: ctrl=0x%08h", \
                    $time, {29'b0, uart_rx_break_reg, uart_rx_en_reg, uart_rx_valid_reg})); \
        end

    `define UART_READ_RESERVED(rdata, addr) \
        begin \
            rdata <= 32'h00000000; \
            `DEBUG_PRINT(("Time %0t: UART_MEM - Reserved register read: addr=0x%08h, data=0x00000000", \
                    $time, addr)); \
        end

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


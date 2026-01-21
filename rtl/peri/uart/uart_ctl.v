/* UART Controller
 * 
 * This controller handles memory-mapped UART register access:
 * - 0x0: TX Data (write-only)
 * - 0x4: Control (read/write)
 * - 0x8: RX Data (read-only)
 * - 0xC: RX Control (read/write)
 * - 0x10: Clock Divider (read/write) - 10 bits, divider = CLK_HZ / BIT_RATE
 *         Default: 556 (for 64MHz clock and 115200 baud rate)
 */

module uart_ctl #(
    parameter UART_BASE_ADDR   = 32'h40000000,
    parameter PAYLOAD_BITS     = 8,
    parameter STOP_BITS        = 1
) (
    input wire clk,
    input wire rst_n,

    // Memory-mapped interface
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output wire [31:0] mem_rdata,
    
    // UART physical interface
    output wire uart_tx,
    input wire uart_rx
);

    wire [21:0] _unused_mem_wdata = mem_wdata[31:10];

    // Internal registers used by macros
    reg [7:0] uart_tx_data_reg;
    reg uart_tx_en_reg;
    reg uart_rx_en_reg;
    reg uart_rx_break_reg;
    reg uart_rx_valid_reg;

    // Clock divider register (10 bits)
    // Default value: 556 for 64MHz clock and 115200 baud rate
    // divider = 64,000,000 / 115200 = 555.5... ≈ 556
    localparam DEFAULT_DIVIDER = 10'd556;
    reg [9:0] uart_divider_reg;

    // UART TX/RX internal signals
    wire uart_tx_en;
    wire [7:0] uart_tx_data;
    wire uart_tx_busy;
    wire uart_rx_en;
    wire uart_rx_break;
    wire uart_rx_valid;
    wire [7:0] uart_rx_data;

    // Address offsets
    localparam [7:0] ADDR_TX_DATA   = 8'h00;  // TX Data (write-only)
    localparam [7:0] ADDR_TX_CTRL   = 8'h04;  // TX Control (read/write)
    localparam [7:0] ADDR_RX_DATA   = 8'h08;  // RX Data (read-only)
    localparam [7:0] ADDR_RX_CTRL   = 8'h0C;  // RX Control (read/write)
    localparam [7:0] ADDR_DIVIDER  = 8'h10;  // Clock Divider (read/write)

    // UART request signal - calculated internally
    wire uart_request = mem_addr[31:8] == UART_BASE_ADDR[31:8];

    // Calculate offset from base address
    wire [7:0] addr_offset = mem_addr[7:0];

    // Assign outputs from registers
    assign uart_tx_en = uart_tx_en_reg;
    assign uart_tx_data = uart_tx_data_reg;
    assign uart_rx_en = uart_rx_en_reg;

    // UART TX module instantiation
    uart_tx #(
        .PAYLOAD_BITS(PAYLOAD_BITS),
        .STOP_BITS(STOP_BITS)
    ) uart_transmitter (
        .clk(clk),
        .resetn(rst_n),
        .divider(uart_divider_reg),
        .uart_txd(uart_tx),
        .uart_tx_busy(uart_tx_busy),
        .uart_tx_en(uart_tx_en),
        .uart_tx_data(uart_tx_data)
    );

    // UART RX module instantiation
    uart_rx #(
        .PAYLOAD_BITS(PAYLOAD_BITS)
    ) uart_receiver (
        .clk(clk),
        .resetn(rst_n),
        .divider(uart_divider_reg),
        .uart_rxd(uart_rx),
        .uart_rx_en(uart_rx_en),
        .uart_rx_break(uart_rx_break),
        .uart_rx_valid(uart_rx_valid),
        .uart_rx_data(uart_rx_data)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            uart_tx_data_reg <= 8'h0;
            uart_tx_en_reg <= 1'b0;
            uart_rx_en_reg <= 1'b0;
            uart_rx_break_reg <= 1'b0;
            uart_rx_valid_reg <= 1'b0;
            uart_divider_reg <= DEFAULT_DIVIDER;
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
                case (addr_offset)
                    ADDR_TX_DATA: uart_tx_data_reg <= mem_wdata[7:0];
                    ADDR_TX_CTRL: uart_tx_en_reg <= mem_wdata[1];
                    ADDR_RX_DATA: ;  // Read-only
                    ADDR_RX_CTRL: begin
                            uart_rx_valid_reg <= mem_wdata[0];
                            uart_rx_en_reg <= mem_wdata[1];
                            uart_rx_break_reg <= mem_wdata[2];
                        end
                    ADDR_DIVIDER: uart_divider_reg <= mem_wdata[9:0];
                    default: ;
                endcase

                case (addr_offset)
                    ADDR_TX_DATA: `DEBUG_PRINT(("Time %0t: UART_MEM - TX Data Write: data=0x%02h (%c)",
                                $time, mem_wdata[7:0], mem_wdata[7:0]));
                    ADDR_TX_CTRL: `DEBUG_PRINT(("Time %0t: UART_MEM - Control Write: ctrl=0x%08h", $time, mem_wdata));
                    ADDR_RX_DATA: `DEBUG_PRINT(("Time %0t: UART_MEM - Invalid write address: addr=0x%08h", $time, mem_addr));
                    ADDR_RX_CTRL: `DEBUG_PRINT(("Time %0t: UART_MEM - RX Control Write: ctrl=0x%08h", $time, mem_wdata));
                    ADDR_DIVIDER: `DEBUG_PRINT(("Time %0t: UART_MEM - Divider Write: divider=0x%03h (%0d)",
                                $time, mem_wdata[9:0], mem_wdata[9:0]));
                    default: `DEBUG_PRINT(("Time %0t: UART_MEM - Invalid write address: addr=0x%08h", $time, mem_addr));
                endcase
            end
        end
    end

    wire [31:0] uart_mem_rdata = (addr_offset == ADDR_TX_DATA) ? 32'h00000000 :
                                (addr_offset == ADDR_TX_CTRL) ? {31'b0, uart_tx_busy} :
                                (addr_offset == ADDR_RX_DATA) ? {24'b0, uart_rx_data} :
                                (addr_offset == ADDR_RX_CTRL) ? {29'b0, uart_rx_break_reg, uart_rx_en_reg, uart_rx_valid_reg} :
                                (addr_offset == ADDR_DIVIDER) ? {22'b0, uart_divider_reg} :
                                32'h00000000;
    assign mem_rdata = (uart_request && mem_re) ? uart_mem_rdata : 32'h00000000;

    always @(*) begin
        if (uart_request && mem_re) begin
            case (addr_offset)
                ADDR_TX_DATA: `DEBUG_PRINT(("Time %0t: UART_MEM - TX Data Read (write-only): data=0x00000000", $time));
                ADDR_TX_CTRL: `DEBUG_PRINT(("Time %0t: UART_MEM - Control Read: ctrl=0x%08h, busy=%b",
                                    $time, {31'b0, uart_tx_busy}, uart_tx_busy));
                ADDR_RX_DATA: `DEBUG_PRINT(("Time %0t: UART_MEM - RX Data Read: data=0x%08h",
                                    $time, {24'b0, uart_rx_data}));
                ADDR_RX_CTRL: `DEBUG_PRINT(("Time %0t: UART_MEM - RX Control Read: ctrl=0x%08h",
                                    $time, {29'b0, uart_rx_break_reg, uart_rx_en_reg, uart_rx_valid_reg}));
                ADDR_DIVIDER: `DEBUG_PRINT(("Time %0t: UART_MEM - Divider Read: divider=0x%03h (%0d)",
                                    $time, uart_divider_reg, uart_divider_reg));
                default: `DEBUG_PRINT(("Time %0t: UART_MEM - Invalid read address: addr=0x%08h", $time, mem_addr));
            endcase
        end
    end
endmodule


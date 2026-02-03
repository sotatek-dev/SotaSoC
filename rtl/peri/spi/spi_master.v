/* SPI Master Module
 * 
 * Implements an SPI master controller for peripheral devices.
 * Supports standard SPI mode only (no dual/quad mode).
 * 
 * Memory-mapped registers:
 * - ENABLE  (0x00): Enable register
 *                   bit 0: Enable module (1=enabled, 0=disabled; when disabled, start is ignored)
 *                   bits [31:1]: Reserved
 * - CTRL    (0x04): Control register
 *                   bit 0: Start transaction (write 1 to start, auto-clears; only when enabled)
 *                   bit 1: Length (0=1 byte, 1=2 bytes; applies to the transfer started by bit 0)
 *                   bits [31:2]: Reserved
 * - STATUS  (0x08): Status register (read-only)
 *                   bit 0: Busy (1=transfer in progress)
 *                   bit 1: Done (1=transfer complete, cleared on new transfer)
 *                   bits [31:2]: Reserved
 * - TX_DATA (0x0C): TX data register (write-only)
 *                   Write: Data to send; bits [7:0]=first byte, [15:8]=second byte (used when LEN=1)
 * - RX_DATA (0x10): RX data register (read-only)
 *                   Read: Data received; bits [7:0]=first byte, [15:8]=second byte
 * - CONFIG  (0x14): Configuration register
 *                   bits [7:0]: Clock divider (SPI_SCLK = clk / (2 * (divider + 1)))
 *                   bit 8: CPHA (0=sample first edge/change second, 1=change first/sample second)
 *                   bit 9: CPOL (0=idle low, 1=idle high)
 *                   bits [31:10]: Reserved
 * 
 * Usage (1 byte):
 * 1. Write ENABLE (bit 0 = 1); configure CONFIG
 * 2. Write TX_DATA [7:0] (or full 32-bit; [15:0] used)
 * 3. Write CTRL: bit 0 = 1 (START), bit 1 = 0 (1 byte)
 * 4. Wait for STATUS.DONE; read RX_DATA [7:0]
 *
 * Usage (2 bytes):
 * 1. Write ENABLE; configure CONFIG
 * 2. Write TX_DATA [15:0]: [7:0]=first byte, [15:8]=second byte
 * 3. Write CTRL: bit 0 = 1 (START), bit 1 = 1 (2 bytes)
 * 4. Wait for STATUS.DONE; read RX_DATA [15:0]
 *
 */

module spi_master #(
    parameter SPI_BASE_ADDR = 32'h40005000
) (
    input wire clk,
    input wire rst_n,

    // Memory-mapped interface
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output wire [31:0] mem_rdata,

    // SPI interface (standard SPI only)
    output wire ena,
    output reg spi_sclk,      // SPI clock
    output reg spi_mosi,      // Master Out Slave In
    input wire spi_miso       // Master In Slave Out
);

    // Address offsets
    localparam [7:0] ADDR_ENABLE   = 8'h0;
    localparam [7:0] ADDR_CTRL     = 8'h4;
    localparam [7:0] ADDR_STATUS   = 8'h8;
    localparam [7:0] ADDR_TX_DATA  = 8'hC;
    localparam [7:0] ADDR_RX_DATA  = 8'h10;
    localparam [7:0] ADDR_CONFIG   = 8'h14;

    // Enable register bits
    localparam ENABLE_BIT = 0;

    // Control register bits
    localparam CTRL_START = 0;
    localparam CTRL_LEN   = 1;   // 0=1 byte, 1=2 bytes

    // Config register bits
    localparam CONFIG_DIV_START = 0;
    localparam CONFIG_DIV_END = 7;
    localparam CONFIG_CPHA = 8;
    localparam CONFIG_CPOL = 9;

    // FSM states
    localparam [1:0] STATE_IDLE = 2'b00;
    localparam [1:0] STATE_START = 2'b01;
    localparam [1:0] STATE_TRANSFER = 2'b10;
    localparam [1:0] STATE_DONE = 2'b11;

    // Internal registers
    reg [1:0] state;
    reg [1:0] next_state;
    reg [4:0] bit_counter;       // Counts transferred bits
    reg [15:0] tx_shift_reg;     // TX shift register (first byte out MSB first = [15:8] of load, then [7:0])
    reg [15:0] rx_shift_reg;     // RX shift register (first byte in -> [7:0], second -> [15:8])

    reg ctrl_en;                 // Module enable from ENABLE register (1=enabled)
    reg [7:0] clock_divider;     // Clock divider value
    reg [7:0] clk_counter;       // Clock divider counter
    reg cpol;                    // Clock polarity (from CONFIG): 0=idle low, 1=idle high
    reg cpha;                    // Clock phase (from CONFIG): 0=sample first/change second, 1=change first/sample second
    reg spi_clk_en;              // Enable SPI clock generation
    reg busy;
    reg done;
    reg start_pending;
    reg len_2byte;              // 0=1 byte, 1=2 bytes (captured from CTRL bit 1 when START is written)

    assign ena = ctrl_en;

    // SPI request signal
    wire spi_request = mem_addr[31:8] == SPI_BASE_ADDR[31:8];
    wire [7:0] addr_offset = mem_addr[7:0];

    wire spi_clk_next = (spi_clk_en && (clk_counter == clock_divider)) ? ~spi_sclk : spi_sclk;

    wire [4:0] max_bit_counter = len_2byte ? 5'd16 : 5'd8;
    // After the last bit is received, wait for the clock divider to complete
    wire is_transaction_done = (bit_counter == max_bit_counter) && (clk_counter == clock_divider - 1);

    // SPI clock generation
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            spi_sclk <= 1'b0;
            clk_counter <= 8'b0;
        end else begin
            spi_sclk <= spi_clk_next;
            if (spi_clk_en) begin
                if (clk_counter == clock_divider) begin
                    clk_counter <= 8'b0;
                end else begin
                    clk_counter <= clk_counter + 1;
                end
            end else begin
                spi_sclk <= cpol;  // Idle state from CPOL (0=idle low, 1=idle high)
                clk_counter <= 8'b0;
            end
        end
    end

    // Edge detection
    wire spi_clk_rising = (spi_sclk == 1'b0) && (spi_clk_next == 1'b1);
    wire spi_clk_falling = (spi_sclk == 1'b1) && (spi_clk_next == 1'b0);

    // First edge = transition from idle (CPOL=0 -> rising, CPOL=1 -> falling); second = opposite.
    wire spi_clk_first  = cpol ? spi_clk_falling : spi_clk_rising;
    wire spi_clk_second = cpol ? spi_clk_rising  : spi_clk_falling;
    // CPHA=0: sample first edge, change second; CPHA=1: change first, sample second.
    wire sample_edge = cpha ? spi_clk_second : spi_clk_first;
    wire change_edge = cpha ? spi_clk_first  : spi_clk_second;

    // State machine
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= STATE_IDLE;
        end else begin
            state <= next_state;
        end
    end

    // Next state logic
    always @(*) begin
        case (state)
            STATE_IDLE: begin
                if (start_pending) begin
                    next_state = STATE_START;
                end else begin
                    next_state = STATE_IDLE;
                end
            end

            STATE_START: begin
                next_state = STATE_TRANSFER;
            end

            STATE_TRANSFER: begin
                if (is_transaction_done) begin
                    next_state = STATE_DONE;
                end else begin
                    next_state = STATE_TRANSFER;
                end
            end

            STATE_DONE: begin
                next_state = STATE_IDLE;
            end

            default: next_state = STATE_IDLE;
        endcase
    end

    // Control logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            spi_mosi <= 1'b0;
            bit_counter <= 5'b0;
            tx_shift_reg <= 16'b0;
            rx_shift_reg <= 16'b0;

            ctrl_en <= 1'b0;  // Disabled by default; must set ENABLE before start
            clock_divider <= 8'd31;  // Default: ~1MHz @ 64MHz system clock
            cpol <= 1'b0;
            cpha <= 1'b0;
            spi_clk_en <= 1'b0;
            busy <= 1'b0;
            done <= 1'b0;
            start_pending <= 1'b0;
            len_2byte <= 1'b0;
        end else begin
            // Default values
            start_pending <= 1'b0;

            // Handle memory writes
            if (spi_request && mem_we) begin
                case (addr_offset)
                    ADDR_ENABLE: begin
                        ctrl_en <= mem_wdata[ENABLE_BIT];
                    end
                    ADDR_CTRL: begin
                        if (mem_wdata[CTRL_START] && ctrl_en && !busy) begin
                            start_pending <= 1'b1;
                            len_2byte <= mem_wdata[CTRL_LEN];
                            done <= 1'b0;  // Clear done flag on new transfer
                        end
                    end
                    ADDR_TX_DATA: begin
                        // Load TX buffer: [7:0]=first byte, [15:8]=second byte; shift out order = first byte then second (MSB first each)
                        if (!busy) begin
                            tx_shift_reg <= {mem_wdata[7:0], mem_wdata[15:8]};
                        end
                    end
                    ADDR_CONFIG: begin
                        clock_divider <= mem_wdata[CONFIG_DIV_END:CONFIG_DIV_START];
                        cpha <= mem_wdata[CONFIG_CPHA];
                        cpol <= mem_wdata[CONFIG_CPOL];
                    end
                    default: ;
                endcase
            end

            // State machine control
            case (state)
                STATE_IDLE: begin
                    spi_clk_en <= 1'b0;
                    busy <= 1'b0;
                    bit_counter <= 5'b0;
                    spi_mosi <= 1'b0;
                end

                STATE_START: begin
                    busy <= 1'b1;
                    bit_counter <= 5'b0;
                    spi_clk_en <= 1'b1;
                    rx_shift_reg <= 16'b0;
                    // CPHA=0: data must be valid before first clock edge; output first bit now
                    // CPHA=1: data changes on first edge; do not drive first bit here (output on first change_edge in TRANSFER)
                    spi_mosi <= cpha ? 1'b0 : tx_shift_reg[15];
                end

                STATE_TRANSFER: begin
                    busy <= 1'b1;
                    spi_clk_en <= 1'b1;

                    if (sample_edge) begin
                        rx_shift_reg <= {rx_shift_reg[14:0], spi_miso};
                        tx_shift_reg <= {tx_shift_reg[14:0], 1'b0};
                        bit_counter <= bit_counter + 1;
                    end

                    if (change_edge) begin
                        spi_mosi <= tx_shift_reg[15];
                    end

                    if (is_transaction_done) begin
                        spi_clk_en <= 1'b0;
                    end
                end

                STATE_DONE: begin
                    spi_clk_en <= 1'b0;
                    busy <= 1'b0;
                    done <= 1'b1;
                    bit_counter <= 5'b0;
                    spi_mosi <= 1'b0;
                end

                default: ;
            endcase
        end
    end

    // Memory read logic
    wire [31:0] enable_reg = {31'b0, ctrl_en};

    wire [31:0] status_reg = {30'b0, done, busy};

    // RX data output - return 16-bit: [7:0]=first byte, [15:8]=second byte
    wire [15:0] rx_data = len_2byte ? {rx_shift_reg[7:0], rx_shift_reg[15:8]} : {8'b0, rx_shift_reg[7:0]};
    wire [31:0] rx_data_reg = {16'b0, rx_data};

    wire [31:0] config_reg = {22'b0, cpol, cpha, clock_divider};

    wire [31:0] spi_mem_rdata = (addr_offset == ADDR_ENABLE) ? enable_reg :
                      (addr_offset == ADDR_CTRL) ? 32'b0 :
                      (addr_offset == ADDR_STATUS) ? status_reg :
                      (addr_offset == ADDR_TX_DATA) ? 32'b0 :
                      (addr_offset == ADDR_RX_DATA) ? rx_data_reg :
                      (addr_offset == ADDR_CONFIG) ? config_reg :
                      32'h0;

    assign mem_rdata = (spi_request && mem_re) ? spi_mem_rdata : 32'h0;

endmodule

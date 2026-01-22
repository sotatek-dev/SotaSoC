/* I2C Master Module
 * 
 * Implements an I2C master controller with configurable clock speed.
 * Supports standard mode (100kHz) and fast mode (400kHz).
 * 
 * Memory-mapped registers:
 * - CTRL    (0x00): Control register
 *                   bit 0: Enable (1=enabled, 0=disabled)
 *                   bit 1: Start condition (write 1 to generate START)
 *                   bit 2: Stop condition (write 1 to generate STOP)
 *                   bit 3: Read mode (1=read, 0=write)
 *                   bit 4: ACK enable (1=send ACK after read, 0=send NACK)
 *                   bit 5: Reserved
 *                   bit 6: Reserved
 *                   bit 7: Reserved
 * - STATUS  (0x04): Status register (read-only)
 *                   bit 0: Busy (1=transfer in progress)
 *                   bit 1: ACK received (1=ACK, 0=NACK from last transfer)
 *                   bit 2: Arbitration lost
 *                   bit 3: Transfer complete (cleared on new transfer)
 *                   bit 4: Bus error
 * - DATA    (0x08): Data register
 *                   Write: TX data (8-bit)
 *                   Read: RX data (8-bit)
 * - PRESCALE(0x0C): Clock prescaler (8-bit)
 *                   I2C_SCL_freq = clk_freq / (4 * (prescale + 1))
 *                   For 100kHz @ 64MHz: prescale = 159
 *                   For 400kHz @ 64MHz: prescale = 39
 * 
 * Usage:
 * 1. Set prescaler for desired I2C clock speed
 * 2. Enable the module (CTRL bit 0 = 1)
 * 3. Write slave address + R/W bit to DATA, set START bit
 * 4. Wait for transfer complete (STATUS bit 3)
 * 5. Check ACK (STATUS bit 1)
 * 6. For write: Write data byte to DATA register
 * 7. For read: Set read mode and ACK/NACK, read from DATA register
 * 8. Repeat steps 4-7 for additional bytes
 * 9. Set STOP bit to release bus
 */

module i2c_master #(
    parameter I2C_BASE_ADDR = 32'h40004000
) (
    input wire clk,
    input wire rst_n,

    // Memory-mapped interface
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output wire [31:0] mem_rdata,

    // Module enable input
    output wire ena,

    // I2C SDA interface (bidirectional, open-drain)
    input  wire i2c_sda_in,   // SDA input
    output wire i2c_sda_out,  // SDA output (always 0 when driving)
    output wire i2c_sda_oe,   // SDA output enable (1=drive low, 0=release/high-z)
    
    // I2C SCL interface (bidirectional, open-drain, supports clock stretching)
    input  wire i2c_scl_in,   // SCL input (for clock stretching detection)
    output wire i2c_scl_out,  // SCL output (always 0 when driving)
    output wire i2c_scl_oe    // SCL output enable (1=drive low, 0=release/high-z)

);

    // Address offsets
    localparam [3:0] ADDR_CTRL     = 4'h0;
    localparam [3:0] ADDR_STATUS   = 4'h4;
    localparam [3:0] ADDR_DATA     = 4'h8;
    localparam [3:0] ADDR_PRESCALE = 4'hC;

    // Control register bits
    localparam CTRL_ENABLE    = 0;
    localparam CTRL_START     = 1;
    localparam CTRL_STOP      = 2;
    localparam CTRL_READ      = 3;
    localparam CTRL_ACK_EN    = 4;

    // Status register bits
    localparam STATUS_BUSY          = 0;
    localparam STATUS_ACK_RECEIVED  = 1;
    localparam STATUS_ARB_LOST      = 2;
    localparam STATUS_TRANSFER_DONE = 3;
    localparam STATUS_BUS_ERROR     = 4;

    // I2C state machine states
    localparam [3:0] STATE_IDLE       = 4'd0;
    localparam [3:0] STATE_START      = 4'd1;
    localparam [3:0] STATE_START2     = 4'd2;
    localparam [3:0] STATE_DATA_BIT   = 4'd3;
    localparam [3:0] STATE_DATA_SCL_H = 4'd4;
    localparam [3:0] STATE_DATA_SCL_L = 4'd5;
    localparam [3:0] STATE_ACK_BIT    = 4'd6;
    localparam [3:0] STATE_ACK_SCL_H  = 4'd7;
    localparam [3:0] STATE_ACK_SCL_L  = 4'd8;
    localparam [3:0] STATE_STOP       = 4'd9;
    localparam [3:0] STATE_STOP2      = 4'd10;
    localparam [3:0] STATE_STOP3      = 4'd11;

    // I2C request detection
    wire i2c_request = (mem_addr[31:8] == I2C_BASE_ADDR[31:8]);
    wire [3:0] reg_offset = mem_addr[3:0];

    // Registers
    reg [7:0] ctrl_reg;
    reg [7:0] status_reg;
    reg [7:0] data_reg;      // Shared TX/RX data register (saves 8 FFs)
    reg [7:0] prescale_reg;

    // State machine
    reg [3:0] state;
    reg [3:0] next_state;

    // Clock divider
    reg [7:0] clk_cnt;
    wire clk_tick = (clk_cnt == prescale_reg);

    // Bit counter (0-7 for data, 8 for ACK)
    reg [3:0] bit_cnt;

    // Shift register for TX/RX
    reg [7:0] shift_reg;

    // Internal SDA/SCL control
    reg sda_out_reg;
    reg scl_out_reg;

    // Flags
    reg ack_received;
    reg arb_lost;
    reg bus_error;
    reg transfer_done;

    // Start/stop command latches (cleared after processing)
    reg start_pending;
    reg stop_pending;

    // Read mode flag
    wire read_mode = ctrl_reg[CTRL_READ];
    wire ack_enable = ctrl_reg[CTRL_ACK_EN];
    wire module_enable = ctrl_reg[CTRL_ENABLE];

    // Unused bits
    wire [23:0] _unused_wdata_high = mem_wdata[31:8];
    wire [3:0] _unused_addr = mem_addr[7:4];

    // Clock divider
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clk_cnt <= 8'd0;
        end else if (!module_enable || state == STATE_IDLE) begin
            clk_cnt <= 8'd0;
        end else if (clk_tick) begin
            clk_cnt <= 8'd0;
        end else begin
            clk_cnt <= clk_cnt + 1'b1;
        end
    end

    // State machine - sequential logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= STATE_IDLE;
        end else begin
            state <= next_state;
        end
    end

    // State machine - combinational logic
    always @(*) begin
        next_state = state;
        
        case (state)
            STATE_IDLE: begin
                if (module_enable && start_pending) begin
                    next_state = STATE_START;
                end
            end

            STATE_START: begin
                // SDA goes low while SCL is high
                if (clk_tick) begin
                    next_state = STATE_START2;
                end
            end

            STATE_START2: begin
                // SCL goes low
                if (clk_tick) begin
                    next_state = STATE_DATA_BIT;
                end
            end

            STATE_DATA_BIT: begin
                // Set up data bit, SCL is low
                if (clk_tick) begin
                    next_state = STATE_DATA_SCL_H;
                end
            end

            STATE_DATA_SCL_H: begin
                // SCL goes high, data is sampled
                if (clk_tick) begin
                    // Check clock stretching
                    if (i2c_scl_in) begin
                        next_state = STATE_DATA_SCL_L;
                    end
                    // else stay in this state (clock stretching)
                end
            end

            STATE_DATA_SCL_L: begin
                // SCL goes low
                if (clk_tick) begin
                    if (bit_cnt == 4'd7) begin
                        next_state = STATE_ACK_BIT;
                    end else begin
                        next_state = STATE_DATA_BIT;
                    end
                end
            end

            STATE_ACK_BIT: begin
                // Set up ACK bit, SCL is low
                if (clk_tick) begin
                    next_state = STATE_ACK_SCL_H;
                end
            end

            STATE_ACK_SCL_H: begin
                // SCL goes high, ACK is sampled
                if (clk_tick) begin
                    if (i2c_scl_in) begin
                        next_state = STATE_ACK_SCL_L;
                    end
                end
            end

            STATE_ACK_SCL_L: begin
                // SCL goes low, transfer complete
                if (clk_tick) begin
                    if (stop_pending) begin
                        next_state = STATE_STOP;
                    end else if (start_pending) begin
                        // Repeated start
                        next_state = STATE_START;
                    end else begin
                        next_state = STATE_IDLE;
                    end
                end
            end

            STATE_STOP: begin
                // SDA low while SCL low
                if (clk_tick) begin
                    next_state = STATE_STOP2;
                end
            end

            STATE_STOP2: begin
                // SCL goes high
                if (clk_tick) begin
                    next_state = STATE_STOP3;
                end
            end

            STATE_STOP3: begin
                // SDA goes high while SCL is high
                if (clk_tick) begin
                    next_state = STATE_IDLE;
                end
            end

            default: begin
                next_state = STATE_IDLE;
            end
        endcase
    end

    // Data path and control signals
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sda_out_reg <= 1'b1;  // Released (high)
            scl_out_reg <= 1'b1;  // Released (high)
            bit_cnt <= 4'd0;
            shift_reg <= 8'd0;
            data_reg <= 8'd0;
            ack_received <= 1'b0;
            arb_lost <= 1'b0;
            bus_error <= 1'b0;
            transfer_done <= 1'b0;
            start_pending <= 1'b0;
            stop_pending <= 1'b0;
        end else begin
            // Handle register writes
            if (i2c_request && mem_we) begin
                case (reg_offset)
                    ADDR_CTRL: begin
                        if (mem_wdata[CTRL_START]) begin
                            start_pending <= 1'b1;
                            transfer_done <= 1'b0;  // Clear transfer done on new start
                        end
                        if (mem_wdata[CTRL_STOP]) begin
                            stop_pending <= 1'b1;
                        end
                    end
                    ADDR_DATA: begin
                        data_reg <= mem_wdata[7:0];
                        shift_reg <= mem_wdata[7:0];
                        transfer_done <= 1'b0;  // Clear transfer done on new data
                    end
                    default: ;
                endcase
            end

            // State machine data path
            case (state)
                STATE_IDLE: begin
                    sda_out_reg <= 1'b1;
                    scl_out_reg <= 1'b1;
                    bit_cnt <= 4'd0;
                    if (start_pending) begin
                        shift_reg <= data_reg;
                    end
                end

                STATE_START: begin
                    // SDA goes low while SCL is high (START condition)
                    if (clk_tick) begin
                        sda_out_reg <= 1'b0;
                        start_pending <= 1'b0;
                    end
                end

                STATE_START2: begin
                    // SCL goes low
                    if (clk_tick) begin
                        scl_out_reg <= 1'b0;
                        bit_cnt <= 4'd0;
                    end
                end

                STATE_DATA_BIT: begin
                    // Set up data bit (MSB first), SCL is low
                    if (clk_tick) begin
                        if (read_mode) begin
                            sda_out_reg <= 1'b1;  // Release SDA for reading
                        end else begin
                            sda_out_reg <= shift_reg[7];  // Output MSB
                        end
                    end
                end

                STATE_DATA_SCL_H: begin
                    // SCL goes high
                    scl_out_reg <= 1'b1;
                    
                    // Sample data on rising edge of SCL
                    if (clk_tick && i2c_scl_in) begin
                        if (read_mode) begin
                            shift_reg <= {shift_reg[6:0], i2c_sda_in};
                        end else begin
                            // Check for arbitration lost
                            if (sda_out_reg && !i2c_sda_in) begin
                                arb_lost <= 1'b1;
                            end
                        end
                    end
                end

                STATE_DATA_SCL_L: begin
                    // SCL goes low
                    if (clk_tick) begin
                        scl_out_reg <= 1'b0;
                        if (bit_cnt < 4'd7) begin
                            bit_cnt <= bit_cnt + 1'b1;
                            if (!read_mode) begin
                                shift_reg <= {shift_reg[6:0], 1'b0};  // Shift left for next bit
                            end
                        end
                    end
                end

                STATE_ACK_BIT: begin
                    // Set up ACK bit, SCL is low
                    if (clk_tick) begin
                        if (read_mode) begin
                            // Master sends ACK/NACK
                            sda_out_reg <= !ack_enable;  // ACK=0 (low), NACK=1 (high)
                        end else begin
                            // Release SDA to receive ACK from slave
                            sda_out_reg <= 1'b1;
                        end
                    end
                end

                STATE_ACK_SCL_H: begin
                    // SCL goes high, sample ACK
                    scl_out_reg <= 1'b1;
                    
                    if (clk_tick && i2c_scl_in) begin
                        if (!read_mode) begin
                            // Sample ACK from slave (ACK=0, NACK=1)
                            ack_received <= !i2c_sda_in;
                        end else begin
                            ack_received <= 1'b1;  // We sent the ACK
                        end
                    end
                end

                STATE_ACK_SCL_L: begin
                    // SCL goes low, transfer complete
                    if (clk_tick) begin
                        scl_out_reg <= 1'b0;
                        transfer_done <= 1'b1;
                        data_reg <= shift_reg;  // Store received data (or echo back TX data)
                        bit_cnt <= 4'd0;
                        
                        // Prepare for next byte if not stopping
                        if (!stop_pending && !start_pending) begin
                            shift_reg <= data_reg;
                        end
                    end
                end

                STATE_STOP: begin
                    // SDA low while SCL low
                    if (clk_tick) begin
                        sda_out_reg <= 1'b0;
                        stop_pending <= 1'b0;
                    end
                end

                STATE_STOP2: begin
                    // SCL goes high
                    if (clk_tick) begin
                        scl_out_reg <= 1'b1;
                    end
                end

                STATE_STOP3: begin
                    // SDA goes high while SCL is high (STOP condition)
                    if (clk_tick) begin
                        sda_out_reg <= 1'b1;
                    end
                end

                default: ;
            endcase
        end
    end

    // Control register write (separate from state machine)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ctrl_reg <= 8'h00;
            prescale_reg <= 8'd159;  // Default: 100kHz @ 64MHz
        end else begin
            if (i2c_request && mem_we) begin
                case (reg_offset)
                    ADDR_CTRL: begin
                        // Only store persistent bits (enable, read, ack_en)
                        ctrl_reg[CTRL_ENABLE] <= mem_wdata[CTRL_ENABLE];
                        ctrl_reg[CTRL_READ] <= mem_wdata[CTRL_READ];
                        ctrl_reg[CTRL_ACK_EN] <= mem_wdata[CTRL_ACK_EN];
                        // START and STOP are handled separately as commands
                    end
                    ADDR_PRESCALE: begin
                        prescale_reg <= mem_wdata[7:0];
                    end
                    default: ;
                endcase
            end
        end
    end

    // Status register (directly active: active high)
    wire busy = (state != STATE_IDLE);
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            status_reg <= 8'h00;
        end else begin
            status_reg[STATUS_BUSY] <= busy;
            status_reg[STATUS_ACK_RECEIVED] <= ack_received;
            status_reg[STATUS_ARB_LOST] <= arb_lost;
            status_reg[STATUS_TRANSFER_DONE] <= transfer_done;
            status_reg[STATUS_BUS_ERROR] <= bus_error;
        end
    end

    // Memory read multiplexer
    wire [31:0] i2c_mem_rdata = (reg_offset == ADDR_CTRL)     ? {24'b0, ctrl_reg} :
                                (reg_offset == ADDR_STATUS)   ? {24'b0, status_reg} :
                                (reg_offset == ADDR_DATA)     ? {24'b0, data_reg} :
                                (reg_offset == ADDR_PRESCALE) ? {24'b0, prescale_reg} :
                                32'h0;

    assign mem_rdata = (i2c_request && mem_re) ? i2c_mem_rdata : 32'h0;

    // I2C output signals
    // Open-drain: when we want to drive low, oe=1 and out=0
    //             when we want to release (high), oe=0
    assign i2c_sda_out = 1'b0;  // Always drive low when enabled
    assign i2c_sda_oe = !sda_out_reg;  // Enable driver when we want low
    
    assign i2c_scl_out = 1'b0;  // Always drive low when enabled
    assign i2c_scl_oe = !scl_out_reg;  // Enable driver when we want low

    // Module enable output for pin muxing
    assign ena = module_enable;

endmodule

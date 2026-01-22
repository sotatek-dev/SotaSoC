/* PWM (Pulse Width Modulation) Module
 * 
 * Implements multiple independent PWM channels with configurable period and duty cycle.
 * 
 * Memory-mapped registers (per channel, 16 bytes per channel):
 * - CTRL:     Control register (bit 0 = enable, bits 31:1 = reserved)
 * - PERIOD:   16-bit period value (number of clock cycles per PWM period)
 * - DUTY:     16-bit duty cycle value (number of clock cycles for HIGH state)
 * - COUNTER:  16-bit current counter value (read-only)
 * 
 * When enabled and counter < duty: output = HIGH (1)
 * When enabled and counter >= duty: output = LOW (0)
 * When disabled: output = LOW (0)
 */

module pwm #(
    parameter PWM_BASE_ADDR = 32'h40003000,
    parameter PWM_NUM = 2,
    parameter COUNTER_WIDTH = 16
) (
    input wire clk,
    input wire rst_n,

    // Memory-mapped interface
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output wire [31:0] mem_rdata,

    output wire [PWM_NUM-1:0] ena,

    // PWM outputs
    output wire [PWM_NUM-1:0] pwm_out
);

    // Address offsets per channel (16 bytes per channel)
    localparam [3:0] ADDR_CTRL     = 4'h0;  // Control register
    localparam [3:0] ADDR_PERIOD   = 4'h4;  // Period register
    localparam [3:0] ADDR_DUTY     = 4'h8;  // Duty cycle register
    localparam [3:0] ADDR_COUNTER  = 4'hC;  // Counter register (read-only)

    wire [15:0] _unused_mem_wdata = mem_wdata[31:16];

    // PWM request detection
    wire pwm_request = (mem_addr[31:8] == PWM_BASE_ADDR[31:8]);

    // Calculate which channel (0 to PWM_NUM-1)
    localparam CHANNEL_IDX_BITS = (PWM_NUM > 1) ? $clog2(PWM_NUM) : 1;
    wire [7:0] addr_offset = mem_addr[7:0];
    wire [3:0] channel_sel = addr_offset[7:4];  // Upper 4 bits select channel
    wire [CHANNEL_IDX_BITS-1:0] channel_idx = channel_sel[CHANNEL_IDX_BITS-1:0];
    wire [3:0] reg_offset = addr_offset[3:0];   // Lower 4 bits select register
    wire channel_valid = (channel_sel < PWM_NUM);

    // PWM channel registers
    reg [PWM_NUM-1:0] channel_enable;              // Enable bit for each channel
    reg [COUNTER_WIDTH-1:0] channel_period [PWM_NUM-1:0];  // Period for each channel
    reg [COUNTER_WIDTH-1:0] channel_duty [PWM_NUM-1:0];    // Duty cycle for each channel
    reg [COUNTER_WIDTH-1:0] channel_counter [PWM_NUM-1:0]; // Counter for each channel

    // Detect when period is being written (to reset counter)
    wire period_write = pwm_request && mem_we && channel_valid && (reg_offset == ADDR_PERIOD);
    wire [PWM_NUM-1:0] period_write_channel;
    genvar k;
    generate
        for (k = 0; k < PWM_NUM; k = k + 1) begin : period_write_detect
            assign period_write_channel[k] = period_write && (channel_sel == k);
        end
    endgenerate

    // PWM output generation
    genvar i;
    generate
        for (i = 0; i < PWM_NUM; i = i + 1) begin : pwm_channels
            // Counter logic
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    channel_counter[i] <= {COUNTER_WIDTH{1'b0}};
                end else begin
                    // Reset counter when period is written
                    if (period_write_channel[i]) begin
                        channel_counter[i] <= {COUNTER_WIDTH{1'b0}};
                    end else if (channel_enable[i]) begin
                        if (channel_counter[i] >= channel_period[i]) begin
                            // Reset counter when reaching period
                            channel_counter[i] <= {COUNTER_WIDTH{1'b0}};
                        end else begin
                            // Increment counter
                            channel_counter[i] <= channel_counter[i] + 1'b1;
                            // $display("Counter %d: %d", i, channel_counter[i]);
                        end
                    end else begin
                        // Reset counter when disabled
                        channel_counter[i] <= {COUNTER_WIDTH{1'b0}};
                    end
                end
            end

            // PWM output: HIGH when counter < duty, LOW otherwise
            assign pwm_out[i] = channel_enable[i] && (channel_counter[i] < channel_duty[i]);
        end
    endgenerate

    assign ena[PWM_NUM-1:0] = channel_enable[PWM_NUM-1:0];

    wire [31:0] pwm_mem_rdata = (reg_offset == ADDR_CTRL) ? {{31'b0}, channel_enable[channel_idx]} :
                                (reg_offset == ADDR_PERIOD) ? {{(32-COUNTER_WIDTH){1'b0}}, channel_period[channel_idx]} :
                                (reg_offset == ADDR_DUTY) ? {{(32-COUNTER_WIDTH){1'b0}}, channel_duty[channel_idx]} :
                                (reg_offset == ADDR_COUNTER) ? {{(32-COUNTER_WIDTH){1'b0}}, channel_counter[channel_idx]} :
                                32'h0;
    assign mem_rdata = (pwm_request && mem_re && channel_valid) ? pwm_mem_rdata : 32'h0;

    // Memory write logic
    integer j;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (j = 0; j < PWM_NUM; j = j + 1) begin
                channel_enable[j] <= 1'b0;
                channel_period[j] <= {COUNTER_WIDTH{1'b1}};  // Default period = max
                channel_duty[j] <= {COUNTER_WIDTH{1'b0}};    // Default duty = 0
            end
        end else begin
            if (pwm_request && mem_we && channel_valid) begin
                case (reg_offset)
                    ADDR_CTRL: begin
                        // Write enable bit (bit 0)
                        channel_enable[channel_idx] <= mem_wdata[0];
                    end
                    ADDR_PERIOD: begin
                        // Write period (16-bit)
                        channel_period[channel_idx] <= mem_wdata[COUNTER_WIDTH-1:0];
                    end
                    ADDR_DUTY: begin
                        // Write duty cycle (16-bit)
                        channel_duty[channel_idx] <= mem_wdata[COUNTER_WIDTH-1:0];
                    end
                    default: begin
                        // Read-only registers, do nothing
                    end
                endcase
            end
        end
    end

endmodule


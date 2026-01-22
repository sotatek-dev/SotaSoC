/* GPIO (General Purpose Input/Output) Module
 * 
 * Implements GPIO with different pin types:
 * - bidirectional pins (support both input and output)
 * - output-only pins
 * - input-only pins
 * 
 * Memory-mapped registers:
 * - DIR  (0x00): Direction for bidirectional pins (bit=1: output, bit=0: input)
 * - OUT  (0x04): Output data register
 * - IN   (0x08): Input data register
 * 
 */

module gpio #(
    parameter GPIO_BASE_ADDR = 32'h40001000,
    parameter NUM_BIDIR = 4,   // Bidirectional pins
    parameter NUM_OUT   = 3,   // Output-only pins
    parameter NUM_IN    = 6    // Input-only pins
) (
    input wire clk,
    input wire rst_n,

    // Memory-mapped interface
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output wire [31:0] mem_rdata,

    // GPIO bidirectional interface
    input  wire [NUM_BIDIR-1:0] gpio_bidir_in,   // Input data from bidirectional pins
    output wire [NUM_BIDIR-1:0] gpio_bidir_out,  // Output data to bidirectional pins
    output wire [NUM_BIDIR-1:0] gpio_bidir_oe,   // Output enable (1=output, 0=input/hi-z)

    // GPIO output-only interface
    output wire [NUM_OUT-1:0] gpio_out,

    // GPIO input-only interface
    input  wire [NUM_IN-1:0] gpio_in
);
    wire [3:0] _unused_mem_addr = mem_addr[7:4];

    // Address offsets
    localparam [3:0] ADDR_DIR  = 4'h0;  // Direction register
    localparam [3:0] ADDR_OUT  = 4'h4;  // Output register
    localparam [3:0] ADDR_IN   = 4'h8;  // Input register (read-only)

    // Total output/input bits
    localparam NUM_OUT_TOTAL = NUM_BIDIR + NUM_OUT;
    localparam NUM_IN_TOTAL  = NUM_BIDIR + NUM_IN;

    wire [31-NUM_OUT_TOTAL:0] _unused_mem_wdata = mem_wdata[31:NUM_OUT_TOTAL];

    // GPIO request detection
    wire gpio_request = (mem_addr[31:8] == GPIO_BASE_ADDR[31:8]);
    wire [3:0] reg_offset = mem_addr[3:0];

    // Registers
    reg [NUM_BIDIR-1:0] dir_reg;      // Direction: 1=output, 0=input
    reg [NUM_OUT_TOTAL-1:0] out_reg;

    // Output assignments
    assign gpio_bidir_out = out_reg[NUM_BIDIR-1:0];
    assign gpio_bidir_oe  = dir_reg;
    assign gpio_out       = out_reg[NUM_OUT_TOTAL-1:NUM_BIDIR];

    wire [NUM_IN_TOTAL-1:0] in_data = {gpio_in, gpio_bidir_in};

    wire [31:0] gpio_mem_rdata = (reg_offset == ADDR_DIR) ? {{(32-NUM_BIDIR){1'b0}}, dir_reg} :
                                (reg_offset == ADDR_OUT) ? {{(32-NUM_OUT_TOTAL){1'b0}}, out_reg} :
                                (reg_offset == ADDR_IN) ? {{(32-NUM_IN_TOTAL){1'b0}}, in_data} :
                                32'h0;
    assign mem_rdata = (gpio_request && mem_re) ? gpio_mem_rdata : 32'h0;

    // Memory write logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dir_reg <= {NUM_BIDIR{1'b0}};     // Default: all bidirectional pins as input
            out_reg <= {NUM_OUT_TOTAL{1'b0}}; // Default: all outputs LOW
        end else begin
            if (gpio_request && mem_we) begin
                case (reg_offset)
                    ADDR_DIR: begin
                        dir_reg <= mem_wdata[NUM_BIDIR-1:0];
                    end
                    ADDR_OUT: begin
                        out_reg <= mem_wdata[NUM_OUT_TOTAL-1:0];
                    end
                    // ADDR_IN is read-only, writes are ignored
                    default: begin
                        // Do nothing
                    end
                endcase
            end
        end
    end

endmodule

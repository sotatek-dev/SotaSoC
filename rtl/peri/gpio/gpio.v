/* GPIO (General Purpose Input/Output) Module
 * 
 * Implements GPIO with different pin types:
 * - bidirectional pins (support both input and output)
 * - output-only pins
 * - input-only pins
 * 
 * Memory-mapped registers:
 * - DIR      (0x00): Direction for bidirectional pins (bit=1: output, bit=0: input)
 * - OUT      (0x04): Output data register
 * - IN       (0x08): Input data register (read-only)
 * - INT_EN   (0x0C): Interrupt enable 
 * - INT_PEND (0x14): Interrupt pending (read-only)
 * - INT_CLR  (0x18): Interrupt clear (write 1 to clear)
 * 
 * Interrupt: rising edge only. gpio_interrupt = OR of (INT_EN & INT_PEND).
 */

module gpio #(
    parameter GPIO_BASE_ADDR = 32'h40001000,
    parameter NUM_BIDIR = 1,   // Bidirectional pins
    parameter NUM_OUT   = 6,   // Output-only pins
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
    input  wire [NUM_IN-1:0] gpio_in,

    // Interrupt output
    output wire gpio_interrupt
);

    // Address offsets
    localparam [7:0] ADDR_DIR      = 8'h00;  // Direction register
    localparam [7:0] ADDR_OUT      = 8'h04;  // Output register
    localparam [7:0] ADDR_IN       = 8'h08;  // Input register
    localparam [7:0] ADDR_INT_EN   = 8'h0C;  // Interrupt enable register
    localparam [7:0] ADDR_INT_PEND = 8'h14;  // Interrupt pending register
    localparam [7:0] ADDR_INT_CLR  = 8'h18;  // Interrupt clear register

    // Total output/input bits
    localparam NUM_OUT_TOTAL = NUM_BIDIR + NUM_OUT;
    localparam NUM_IN_TOTAL  = NUM_BIDIR + NUM_IN;

    wire [31-NUM_OUT_TOTAL:0] _unused_mem_wdata = mem_wdata[31:NUM_OUT_TOTAL];

    // GPIO request detection
    wire gpio_request = (mem_addr[31:8] == GPIO_BASE_ADDR[31:8]);
    wire [7:0] reg_offset = mem_addr[7:0];

    // Registers
    reg [NUM_BIDIR-1:0] dir_reg;      // Direction: 1=output, 0=input
    reg [NUM_OUT_TOTAL-1:0] out_reg;
    reg [NUM_IN_TOTAL-1:0] int_en_reg;
    reg [NUM_IN_TOTAL-1:0] int_pend_reg;

    reg gpio_interrupt_reg;

    // Output assignments
    assign gpio_bidir_out = out_reg[NUM_BIDIR-1:0];
    assign gpio_bidir_oe  = dir_reg;
    assign gpio_out       = out_reg[NUM_OUT_TOTAL-1:NUM_BIDIR];

    wire [NUM_IN_TOTAL-1:0] in_data = {gpio_in, gpio_bidir_in};

    assign gpio_interrupt = gpio_interrupt_reg;

    // Synchronize input (avoid metastability)
    reg [NUM_IN_TOTAL-1:0] gpio_sync1, gpio_sync2;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gpio_sync1 <= {NUM_IN_TOTAL{1'b0}};
            gpio_sync2 <= {NUM_IN_TOTAL{1'b0}};
        end else begin
            gpio_sync1 <= in_data;
            gpio_sync2 <= gpio_sync1;
        end
    end

    // Rising edge: 0 -> 1
    wire [NUM_IN_TOTAL-1:0] rising_edge = ~gpio_sync2 & gpio_sync1;

    // INT_CLR write data (bits written with 1 clear corresponding pending)
    wire [NUM_IN_TOTAL-1:0] int_clr_write = (gpio_request && mem_we && (reg_offset == ADDR_INT_CLR))
                                           ? mem_wdata[NUM_IN_TOTAL-1:0]
                                           : {NUM_IN_TOTAL{1'b0}};

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            int_pend_reg <= {NUM_IN_TOTAL{1'b0}};
        end else begin
            for (i = 0; i < NUM_IN_TOTAL; i = i + 1) begin
                if (int_clr_write[i])
                    int_pend_reg[i] <= 1'b0;
                else if (int_en_reg[i] && rising_edge[i])
                    int_pend_reg[i] <= 1'b1;
                else
                    int_pend_reg[i] <= int_pend_reg[i];
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            gpio_interrupt_reg <= 1'b0;
        else
            gpio_interrupt_reg <= |(int_en_reg & int_pend_reg);
    end

    // Read logic
    wire [31:0] gpio_mem_rdata =
        (reg_offset == ADDR_DIR)      ? {{(32-NUM_BIDIR){1'b0}}, dir_reg} :
        (reg_offset == ADDR_OUT)      ? {{(32-NUM_OUT_TOTAL){1'b0}}, out_reg} :
        (reg_offset == ADDR_IN)       ? {{(32-NUM_IN_TOTAL){1'b0}}, in_data} :
        (reg_offset == ADDR_INT_EN)   ? {{(32-NUM_IN_TOTAL){1'b0}}, int_en_reg} :
        (reg_offset == ADDR_INT_PEND) ? {{(32-NUM_IN_TOTAL){1'b0}}, int_pend_reg} :
        32'h0;
    assign mem_rdata = (gpio_request && mem_re) ? gpio_mem_rdata : 32'h0;

    // Write logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dir_reg    <= {NUM_BIDIR{1'b0}};     // Default: all bidirectional pins as input
            out_reg    <= {NUM_OUT_TOTAL{1'b0}};
            int_en_reg <= {NUM_IN_TOTAL{1'b0}};
        end else begin
            if (gpio_request && mem_we) begin
                case (reg_offset)
                    ADDR_DIR:    dir_reg <= mem_wdata[NUM_BIDIR-1:0];
                    ADDR_OUT:    out_reg <= mem_wdata[NUM_OUT_TOTAL-1:0];
                    ADDR_INT_EN: int_en_reg <= mem_wdata[NUM_IN_TOTAL-1:0];
                    default: ;
                endcase
            end
        end
    end

endmodule

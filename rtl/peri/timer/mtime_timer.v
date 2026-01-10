/* Machine Timer (mtime) and Machine Timer Compare (mtimecmp) Module
 * 
 * Implements RISC-V machine timer for timer interrupts.
 * 
 * Memory-mapped registers:
 * - mtime:     Read-only, increments every clock cycle (64-bit, but we use 48-bit)
 * - mtimecmp:  Read/write, compare value for timer interrupt
 * 
 * When mtime >= mtimecmp, the timer interrupt is pending (MTIP in mip register)
 */

module mtime_timer #(
    parameter TIMER_BASE_ADDR = 32'h40002000
) (
    input wire clk,
    input wire rst_n,

    // Memory-mapped interface
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output wire [31:0] mem_rdata,

    input wire [47:0] mtime,

    // Timer interrupt output (MTIP - Machine Timer Interrupt Pending)
    output wire timer_interrupt
);

    // Timer registers
    reg [47:0] mtimecmp;   // Machine time compare register

    // Address offsets (3-bit for 8-byte region)
    localparam [3:0] ADDR_MTIME_LO     = 4'h0;  // mtime at base + 0x0
    localparam [3:0] ADDR_MTIME_HI     = 4'h4;  // mtime at base + 0x4
    localparam [3:0] ADDR_MTIMECMP_LO  = 4'h8;  // mtimecmp at base + 0x8
    localparam [3:0] ADDR_MTIMECMP_HI  = 4'hC;  // mtimecmp at base + 0xC

    wire timer_request = (mem_addr[31:8] == TIMER_BASE_ADDR[31:8]);

    // Calculate offset from base address (only lower 3 bits needed)
    wire [3:0] addr_offset = mem_addr[3:0];

    assign timer_interrupt = (mtime >= mtimecmp);

    wire [31:0] timer_mem_rdata = (addr_offset == ADDR_MTIME_LO) ? mtime[31:0] :
                            (addr_offset == ADDR_MTIME_HI) ? {16'h0, mtime[47:32]} :
                            (addr_offset == ADDR_MTIMECMP_LO) ? mtimecmp[31:0] :
                            (addr_offset == ADDR_MTIMECMP_HI) ? {16'h0, mtimecmp[47:32]} :
                            32'h0;
    assign mem_rdata = (timer_request && mem_re) ? timer_mem_rdata : 32'h0;

    // Timer counter increment and mtimecmp write
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mtimecmp <= 48'hFFFFFFFFFFFF;  // Set to max value initially to prevent immediate interrupt
        end else begin
            if (timer_request && mem_we) begin
                case (addr_offset)
                    ADDR_MTIMECMP_LO: mtimecmp[31:0] <= mem_wdata;
                    ADDR_MTIMECMP_HI: mtimecmp[47:32] <= mem_wdata[15:0];
                    default: ;
                endcase
            end
        end
    end

endmodule



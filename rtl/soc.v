/* RV32I SoC - System on Chip
 * 
 * Integrates:
 * - RV32I processor core
 * - Memory controller with SPI Flash and SPI RAM interfaces
 * - Clock and reset management
 * 
 * Memory Map:
 * 0x80000000 - 0x8FFFFFFF: SPI Flash (Instructions)
 * 0x00000000 - 0x0FFFFFFF: SPI RAM (Data)
 */

module soc #(
    parameter RESET_ADDR = 32'h00000000 
) (
    input wire clk,
    input wire rst_n,
    
    // Shared SPI interface
    output wire flash_cs_n,
    output wire ram_cs_n,
    output wire spi_sclk,
    output wire spi_mosi,
    input wire spi_miso,
    
    // Debug interface (optional)
    output wire [31:0] debug_pc,
    output wire [31:0] debug_instr,
    output wire [15:0] debug_reg_addr,
    output wire [31:0] debug_reg_data,
    output wire debug_reg_we
);

    // Core to Memory Controller connections
    wire [31:0] core_instr_addr;
    wire [31:0] core_instr_data;
    wire [31:0] core_mem_addr;
    wire [31:0] core_mem_wdata;
    wire [31:0] core_mem_rdata;
    wire [2:0] core_mem_wflag;
    wire core_mem_we;
    wire core_mem_re;
    
    // Memory controller ready signals
    wire mem_instr_ready;
    wire mem_data_ready;
    
    // Enhanced core with ready signal handling
    wire core_instr_valid;
    wire core_mem_valid;
    
    // Simple ready signal handling - core waits for memory
    assign core_instr_valid = mem_instr_ready;
    assign core_mem_valid = mem_data_ready;
    
    // RV32I Core instantiation
    rv32i_core #(
        .RESET_ADDR(RESET_ADDR)
    ) cpu_core (
        .clk(clk),
        .rst_n(rst_n),
        
        // Instruction memory interface
        .instr_addr(core_instr_addr),
        .instr_data(core_instr_data),
        
        // Data memory interface  
        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_wflag(core_mem_wflag),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_data(core_mem_rdata)
    );
    
    // Memory Controller instantiation
    mem_ctl mem_ctrl (
        .clk(clk),
        .rst_n(rst_n),
        
        // Core instruction interface
        .instr_addr(core_instr_addr),
        .instr_data(core_instr_data),
        .instr_ready(mem_instr_ready),
        
        // Core data interface
        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_wflag(core_mem_wflag),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_rdata(core_mem_rdata),
        .mem_ready(mem_data_ready),
        
        // Shared SPI interface
        .flash_cs_n(flash_cs_n),
        .ram_cs_n(ram_cs_n),
        .spi_sclk(spi_sclk),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso)
    );
    
    // Debug outputs
    assign debug_pc = core_instr_addr;
    assign debug_instr = core_instr_data;
    assign debug_reg_addr = {12'b0, cpu_core.mem_wb_rd_addr};
    assign debug_reg_data = cpu_core.mem_wb_result;
    assign debug_reg_we = cpu_core.mem_wb_reg_we;
    
    // Simulation debug output
    `ifdef SIM_DEBUG
    always @(posedge clk) begin
        if (rst_n) begin
            $display("Time %0t: SOC - PC=0x%h, Instr=0x%h, MemAddr=0x%h, MemWE=%b, MemRE=%b", 
                     $time, core_instr_addr, core_instr_data, core_mem_addr, core_mem_we, core_mem_re);
            
            if (mem_instr_ready) begin
                $display("Time %0t: SOC - Instruction fetch complete: addr=0x%h, data=0x%h", 
                         $time, core_instr_addr, core_instr_data);
            end
            
            if (mem_data_ready) begin
                if (core_mem_we) begin
                    $display("Time %0t: SOC - Memory write complete: addr=0x%h, data=0x%h", 
                             $time, core_mem_addr, core_mem_wdata);
                end else if (core_mem_re) begin
                    $display("Time %0t: SOC - Memory read complete: addr=0x%h, data=0x%h", 
                             $time, core_mem_addr, core_mem_rdata);
                end
            end
        end
    end
    `endif

endmodule

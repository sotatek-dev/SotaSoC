/* Test Memory Controller for RV32I SoC
 * 
 * This test controller:
 * - Loads program binary from file at startup
 * - Serves instruction fetch requests from loaded memory
 * - Handles data memory operations in internal RAM
 * - Provides immediate responses (no SPI delays)
 * - Maintains same interface as mem_ctl.v for drop-in replacement
 * - SPI signals are present but unused (kept for compatibility)
 * 
 * Memory Map:
 * 0x00000000 - 0x0FFFFFFF: Program Memory (loaded from file)
 * 0x00002000 - 0x00011FFF: Data RAM (64KB)
 */

module mem_ctl (
    input wire clk,
    input wire rst_n,
    
    // Core interface
    input wire [31:0] instr_addr,
    output reg [31:0] instr_data,
    output reg instr_ready,
    
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire mem_we,
    input wire mem_re,
    output reg [31:0] mem_rdata,
    output reg mem_ready,
    
    // Shared SPI interface (unused in test controller)
    output reg flash_cs_n,
    output reg ram_cs_n,
    output reg spi_sclk,
    output reg spi_mosi,
    input wire spi_miso
);

    // Memory arrays
    parameter PROG_MEM_SIZE = 16384;  // 64KB program memory (16K x 32-bit words)
    parameter DATA_MEM_SIZE = 16384;  // 64KB data memory (16K x 32-bit words)
    
    reg [31:0] prog_mem [0:PROG_MEM_SIZE-1];
    reg [31:0] data_mem [0:DATA_MEM_SIZE-1];
    
    // Address mapping
    wire is_prog_addr = (instr_addr[31:28] == 4'h0);  // 0x0xxxxxxx
    wire is_data_addr = (mem_addr >= 32'h00002000) && (mem_addr < 32'h00012000);  // 0x00002000-0x00011FFF
    
    // Convert to word addresses
    wire [15:0] prog_word_addr = instr_addr[17:2];  // Word address for program memory
    wire [15:0] data_word_addr = (mem_addr - 32'h00002000) >> 2;  // Word address for data memory (offset by 0x2000)
    
    // Memory initialization - load program from file
    initial begin
        integer i;
        reg [8*256:1] hex_file;  // String to hold filename
        
        // Initialize memories to zero
        for (i = 0; i < PROG_MEM_SIZE; i = i + 1) begin
            prog_mem[i] = 32'h00000000;
        end
        
        for (i = 0; i < DATA_MEM_SIZE; i = i + 1) begin
            data_mem[i] = 32'h00000000;
        end
        
        // Load program binary if file exists
        if ($value$plusargs("HEX_FILE=%s", hex_file)) begin
            $readmemh(hex_file, prog_mem);
            $display("Test Memory Controller: Loaded program from %s", hex_file);
        end else begin
            // Load default test program
            $display("Test Memory Controller: Loading default test program");
            
            // Simple test program - just some NOPs and basic instructions
            prog_mem[0] = 32'h00000013;  // nop (addi x0, x0, 0)
            prog_mem[1] = 32'h00100093;  // addi x1, x0, 1
            prog_mem[2] = 32'h00200113;  // addi x2, x0, 2
            prog_mem[3] = 32'h002081b3;  // add x3, x1, x2
            prog_mem[4] = 32'h00000013;  // nop
            prog_mem[5] = 32'h00000013;  // nop
            prog_mem[6] = 32'hffdff06f;  // jal x0, -4 (infinite loop)
        end
        
        $display("Test Memory Controller: Memory initialization complete");
    end
    
    // Instruction fetch handling
    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            instr_data <= 32'h00000000;
            instr_ready <= 1'b0;
            // Keep SPI signals in safe state
            flash_cs_n <= 1'b1;
            ram_cs_n <= 1'b1;
            spi_sclk <= 1'b0;
            spi_mosi <= 1'b0;
        end else begin
            if (is_prog_addr && prog_word_addr < PROG_MEM_SIZE) begin
                instr_data <= prog_mem[prog_word_addr];
                instr_ready <= 1'b1;
                
                `ifdef SIM_DEBUG
                $display("Time %0t: TEST_MEM - Instruction fetch: addr=0x%h, data=0x%h", 
                         $time, instr_addr, prog_mem[prog_word_addr]);
                `endif
            end else begin
                instr_data <= 32'h00000000;  // Return NOP for invalid addresses
                instr_ready <= 1'b1;
                
                `ifdef SIM_DEBUG
                if (is_prog_addr)
                    $display("Time %0t: TEST_MEM - Invalid instruction address: 0x%h", $time, instr_addr);
                `endif
            end
        end
    end
    
    // Data memory handling
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mem_rdata <= 32'h00000000;
            mem_ready <= 1'b0;
        end else begin
            mem_ready <= 1'b0;
            
            if (is_data_addr && data_word_addr < DATA_MEM_SIZE) begin
                if (mem_we) begin
                    // Write operation
                    data_mem[data_word_addr] <= mem_wdata;
                    mem_ready <= 1'b1;
                    
                    `ifdef SIM_DEBUG
                    $display("Time %0t: TEST_MEM - Data write: addr=0x%h, data=0x%h", 
                             $time, mem_addr, mem_wdata);
                    `endif
                end else if (mem_re) begin
                    // Read operation
                    mem_rdata <= data_mem[data_word_addr];
                    mem_ready <= 1'b1;
                    
                    `ifdef SIM_DEBUG
                    $display("Time %0t: TEST_MEM - Data read: addr=0x%h, data=0x%h", 
                             $time, mem_addr, data_mem[data_word_addr]);
                    `endif
                end
            end else if (mem_we || mem_re) begin
                // Invalid data address
                mem_rdata <= 32'h00000000;
                mem_ready <= 1'b1;
                
                `ifdef SIM_DEBUG
                $display("Time %0t: TEST_MEM - Invalid data address: 0x%h", $time, mem_addr);
                `endif
            end
        end
    end
    
    // Debug output for memory contents
    `ifdef SIM_DEBUG
    initial begin
        $display("Test Memory Controller Debug Info:");
        $display("Program Memory Size: %0d words (%0d bytes)", PROG_MEM_SIZE, PROG_MEM_SIZE * 4);
        $display("Data Memory Size: %0d words (%0d bytes)", DATA_MEM_SIZE, DATA_MEM_SIZE * 4);
        $display("Program Address Range: 0x00000000 - 0x0%07h", (PROG_MEM_SIZE * 4) - 1);
        $display("Data Address Range: 0x00002000 - 0x%08h", 32'h00002000 + (DATA_MEM_SIZE * 4) - 1);
    end
    `endif

endmodule 
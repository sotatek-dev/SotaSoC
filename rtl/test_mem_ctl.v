/* Test Memory Controller for RV32I SoC
 * 
 * This test controller:
 * - Loads program binary from file at startup
 * - Serves instruction fetch requests from loaded memory
 * - Handles data memory operations in internal RAM
 * - Provides immediate responses (no SPI delays)
 * - Maintains same interface as mem_ctl.v for drop-in replacement
 * - SPI signals are present but unused (kept for compatibility)
 * - Supports byte, halfword, and word writes (SB, SH, SW) via write_flag
 * 
 * Memory Map:
 * 0x00000000 - 0x00001FFF: Program Memory (loaded from file) - 8KB
 * 0x00002000 - 0x00003FFF: Data RAM (8KB)
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
    input wire [2:0] mem_wflag,    // funct3 from store instruction: 000=SB, 001=SH, 010=SW
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

    // Memory arrays - 0x2000 = 8192 bytes = 2048 words (32-bit each)
    parameter PROG_MEM_SIZE = 2048;  // 8KB program memory (2K x 32-bit words)
    parameter DATA_MEM_SIZE = 8192;  // 8KB data memory (8K bytes)
    parameter TOTAL_MEM_SIZE = PROG_MEM_SIZE + (DATA_MEM_SIZE/4);  // Total memory size in words
    
    reg [31:0] prog_mem [0:PROG_MEM_SIZE-1];
    reg [7:0] data_mem [0:DATA_MEM_SIZE-1];  // Byte-addressed data memory
    reg [31:0] combined_mem [0:TOTAL_MEM_SIZE-1];  // Temporary array for loading
    
    // Address mapping
    wire is_prog_addr = (instr_addr < 32'h00002000);  // 0x00000000-0x00001FFF
    wire is_data_addr = (mem_addr >= 32'h00002000) && (mem_addr < 32'h00004000);  // 0x00002000-0x00003FFF
    
    // Convert to addresses
    wire [10:0] prog_word_addr = instr_addr[12:2];  // Word address for program memory (11 bits for 2048 words)
    wire [12:0] data_byte_addr = mem_addr - 32'h00002000;  // Byte address for data memory (offset by 0x2000)

    // Memory initialization - load program from file
    initial begin
        integer i;
        reg [8*256:1] hex_file;  // String to hold filename
        
        // Initialize memories to zero
        for (i = 0; i < PROG_MEM_SIZE; i = i + 1) begin
            prog_mem[i] = 32'h00000000;
        end
        
        for (i = 0; i < DATA_MEM_SIZE; i = i + 1) begin
            data_mem[i] = 8'h00;
        end
        
        // Load program binary if file exists
        if ($value$plusargs("HEX_FILE=%s", hex_file)) begin
            // Load entire hex file into temporary combined memory
            $readmemh(hex_file, combined_mem);
            
            // Copy first part to program memory
            for (i = 0; i < PROG_MEM_SIZE; i = i + 1) begin
                prog_mem[i] = combined_mem[i];
            end
            
            // Copy second part to data memory (convert from 32-bit words to bytes)
            for (i = 0; i < DATA_MEM_SIZE/4; i = i + 1) begin
                data_mem[i*4 + 0] = combined_mem[PROG_MEM_SIZE + i][7:0];
                data_mem[i*4 + 1] = combined_mem[PROG_MEM_SIZE + i][15:8];
                data_mem[i*4 + 2] = combined_mem[PROG_MEM_SIZE + i][23:16];
                data_mem[i*4 + 3] = combined_mem[PROG_MEM_SIZE + i][31:24];
            end
            
            $display("Test Memory Controller: Loaded combined hex file %s", hex_file);
            $display("  - Program memory: %0d words (0x00000000-0x%08h)", PROG_MEM_SIZE, (PROG_MEM_SIZE * 4) - 1);
            $display("  - Data memory: %0d bytes (0x00002000-0x%08h)", DATA_MEM_SIZE, 32'h00002000 + DATA_MEM_SIZE - 1);
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
    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mem_rdata <= 32'h00000000;
            mem_ready <= 1'b0;
        end else begin
            mem_ready <= 1'b0;
            
            if (is_data_addr && data_byte_addr < DATA_MEM_SIZE) begin
                if (mem_we) begin
                    // Write operation using byte enable signals based on write_flag
                    // write_flag corresponds to funct3 field:
                    // 3'b000 → SB (Store Byte)
                    // 3'b001 → SH (Store Halfword)
                    // 3'b010 → SW (Store Word)

                    data_mem[data_byte_addr + 0] <= mem_wdata[7:0];
                    if (mem_wflag == 3'b001 || mem_wflag == 3'b010) data_mem[data_byte_addr + 1] <= mem_wdata[15:8];
                    if (mem_wflag == 3'b010) data_mem[data_byte_addr + 2] <= mem_wdata[23:16];
                    if (mem_wflag == 3'b010) data_mem[data_byte_addr + 3] <= mem_wdata[31:24];
                    
                    mem_ready <= 1'b1;
                    
                    `ifdef SIM_DEBUG
                    case (write_flag)
                        3'b000: $display("Time %0t: TEST_MEM - SB (Store Byte): addr=0x%h, data=0x%02h, byte_enable=0x%h", 
                                        $time, mem_addr, mem_wdata[7:0], byte_enable);
                        3'b001: $display("Time %0t: TEST_MEM - SH (Store Halfword): addr=0x%h, data=0x%04h, byte_enable=0x%h", 
                                        $time, mem_addr, mem_wdata[15:0], byte_enable);
                        3'b010: $display("Time %0t: TEST_MEM - SW (Store Word): addr=0x%h, data=0x%08h, byte_enable=0x%h", 
                                        $time, mem_addr, mem_wdata, byte_enable);
                        default: $display("Time %0t: TEST_MEM - Unknown store type: write_flag=0x%h, addr=0x%h, data=0x%08h", 
                                         $time, write_flag, mem_addr, mem_wdata);
                    endcase
                    `endif
                end else if (mem_re) begin
                    // Read operation - 32-bit word read from byte memory
                    mem_rdata <= {data_mem[data_byte_addr + 3], data_mem[data_byte_addr + 2], 
                                  data_mem[data_byte_addr + 1], data_mem[data_byte_addr + 0]};
                    mem_ready <= 1'b1;
                    
                    `ifdef SIM_DEBUG
                    $display("Time %0t: TEST_MEM - Data read: addr=0x%h, data=0x%h", 
                             $time, mem_addr, {data_mem[data_byte_addr + 3], data_mem[data_byte_addr + 2], 
                                               data_mem[data_byte_addr + 1], data_mem[data_byte_addr + 0]});
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
        $display("Data Memory Size: %0d bytes", DATA_MEM_SIZE);
        $display("Program Address Range: 0x00000000 - 0x%08h", (PROG_MEM_SIZE * 4) - 1);
        $display("Data Address Range: 0x00002000 - 0x%08h", 32'h00002000 + DATA_MEM_SIZE - 1);
        $display("Store operations supported via write_flag (funct3):");
        $display("  - write_flag=3'b000 → SB (Store Byte): Writes 1 byte");
        $display("  - write_flag=3'b001 → SH (Store Halfword): Writes 2 bytes");
        $display("  - write_flag=3'b010 → SW (Store Word): Writes 4 bytes");
    end
    `endif

endmodule 
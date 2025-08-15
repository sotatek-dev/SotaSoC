/* Test Memory Controller for RV32I SoC
 * 
 * This test controller:
 * - Loads program binary from file at startup
 * - Serves instruction fetch requests from loaded memory
 * - Handles data memory operations in internal RAM
 * - Simulates realistic memory access delays
 * - Maintains same interface as mem_ctl.v for drop-in replacement
 * - SPI signals are present but unused (kept for compatibility)
 * - Supports byte, halfword, and word writes (SB, SH, SW) via write_flag
 * - SEQUENTIAL ACCESS: Only instruction OR data access at a time
 * - DATA PRIORITY: Data memory access has higher priority than instruction fetch
 * 
 * Memory Map:
 * 0x00000000 - 0x00001FFF: Program Memory (loaded from file) - 8KB
 * 0x00002000 - 0x00003FFF: Data RAM (8KB)
 */

module mem_ctl #(
    parameter PROG_MEM_SIZE = 32'h00002000,
    parameter DATA_MEM_SIZE = 32'h00002000,
    parameter UART_BASE_ADDR = 32'h40000000,
    parameter UART_SIZE = 16,
    parameter GPIO_BASE_ADDR = 32'h40001000,
    parameter GPIO_SIZE = 5
) (
    input wire clk,
    input wire rst_n,
    
    // Core interface
    input wire [31:0] instr_addr,
    output reg [31:0] instr_data,
    output reg instr_ready,
    
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire [2:0] mem_flag,    // funct3 from store instruction: 000=SB, 001=SH, 010=SW
    input wire mem_we,
    input wire mem_re,
    output reg [31:0] mem_rdata,
    output reg mem_ready,
    
    // UART TX interface
    output wire uart_tx_en,
    input wire uart_tx_busy,
    output wire [7:0] uart_tx_data,

    // UART RX interface
    output wire uart_rx_en,
    input wire uart_rx_break,
    input wire uart_rx_valid,
    input wire [7:0] uart_rx_data,

    // GPIO interface
    output wire [GPIO_SIZE-1:0] gpio_out,
    
    // Shared SPI interface (unused in test controller)
    output reg flash_cs_n,
    output reg ram_cs_n,
    output reg spi_sclk,
    output reg spi_mosi,
    input wire spi_miso
);

    // `define USE_MEMORY_DELAY 1
    // Memory access delay constants
    parameter INSTR_FETCH_DELAY = 3;  // Instruction fetch takes 3 cycles
    parameter DATA_ACCESS_DELAY = 2;  // Data read/write takes 2 cycles
    
    parameter TOTAL_MEM_SIZE = PROG_MEM_SIZE + DATA_MEM_SIZE;  // Total memory size in bytes

    reg [7:0] unified_mem [0:TOTAL_MEM_SIZE-1];  // Single byte-addressed memory array
    reg [31:0] combined_mem [0:(TOTAL_MEM_SIZE/4)-1];  // Temporary array for loading
    reg [7:0] uart_tx_data_reg;
    reg uart_tx_en_reg;
    reg uart_rx_en_reg;
    reg uart_rx_break_reg;
    reg uart_rx_valid_reg;

    reg [GPIO_SIZE-1:0] gpio_reg;
    
    // Address mapping
    // Allow access to both program and data memory,
    // because there are some tests that write instructions to data memory then jump to that address
    // wire is_prog_addr = (instr_addr < PROG_MEM_SIZE);
    wire is_prog_addr = (instr_addr < PROG_MEM_SIZE + DATA_MEM_SIZE);
    wire is_data_addr = (mem_addr >= PROG_MEM_SIZE) && (mem_addr < PROG_MEM_SIZE + DATA_MEM_SIZE);
    wire is_uart_addr = (mem_addr >= UART_BASE_ADDR) && (mem_addr < UART_BASE_ADDR + UART_SIZE);
    wire gpio_request = is_data_addr && (mem_addr == GPIO_BASE_ADDR);

    // ========================================
    // UNIFIED ACCESS CONTROLLER
    // ========================================
    // Controls sequential access with data memory priority
    reg [2:0] access_state;
    reg [2:0] access_delay_counter;
    reg [31:0] current_addr;
    reg [31:0] current_wdata;
    reg [2:0] current_flag;
    reg current_we;
    reg current_is_instr;

    localparam ACCESS_IDLE = 3'b000;
    localparam ACCESS_ACTIVE = 3'b001;
    
    // Request signals
    wire data_request = mem_we || mem_re;
    wire instr_request = (instr_addr != current_addr) || !instr_ready;
    
    // Priority logic: data has higher priority
    wire start_data_access = data_request && (access_state == ACCESS_IDLE);
    wire start_instr_access = instr_request && (access_state == ACCESS_IDLE) && !data_request;

    // Memory initialization - load program from file
    integer i;
    reg [8*256:1] hex_file;  // String to hold filename
    initial begin
        
        // Initialize memory to zero
        for (i = 0; i < TOTAL_MEM_SIZE; i = i + 1) begin
            unified_mem[i] = 8'h00;
        end
        
        // Load program binary if file exists
        if ($value$plusargs("HEX_FILE=%s", hex_file)) begin
            // Load entire hex file into temporary combined memory
            $readmemh(hex_file, combined_mem);
            $display("Test Memory Controller: Loaded combined hex file %s", hex_file);
        end else begin
            // Load default test program
            $readmemh("program.hex", combined_mem);
            $display("Test Memory Controller: Loaded default test program");
        end

        // Copy to unified memory (convert from 32-bit words to bytes)
        for (i = 0; i < TOTAL_MEM_SIZE/4; i = i + 1) begin
            unified_mem[i*4 + 0] = combined_mem[i][7:0];
            unified_mem[i*4 + 1] = combined_mem[i][15:8];
            unified_mem[i*4 + 2] = combined_mem[i][23:16];
            unified_mem[i*4 + 3] = combined_mem[i][31:24];
        end

        $display("  - Program memory: %0d bytes (0x00000000-0x%08h)", PROG_MEM_SIZE, PROG_MEM_SIZE - 1);
        $display("  - Data memory: %0d bytes (0x00002000-0x%08h)", DATA_MEM_SIZE, 32'h00002000 + DATA_MEM_SIZE - 1);

        $display("Test Memory Controller: Memory initialization complete");
        $display("  - Instruction fetch delay: %0d cycles", INSTR_FETCH_DELAY);
        $display("  - Data access delay: %0d cycles", DATA_ACCESS_DELAY);
    end

    // Include UART defines from shared header
    `include "uart_defines.vh"

    // UART register access handling (immediate response)
    assign uart_tx_en = uart_tx_en_reg;
    assign uart_tx_data = uart_tx_data_reg;
    assign uart_rx_en = uart_rx_en_reg;

    // GPIO register access handling (immediate response)
    assign gpio_out = gpio_reg;

    `ifndef USE_MEMORY_DELAY
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
            if (is_prog_addr) begin
                // Read 32-bit word from byte memory (little-endian)
                instr_data <= {unified_mem[instr_addr + 3], unified_mem[instr_addr + 2], 
                              unified_mem[instr_addr + 1], unified_mem[instr_addr + 0]};
                instr_ready <= 1'b1;
                
                // `ifdef SIM_DEBUG
                $display("Time %0t: TEST_MEM - Instruction fetch: addr=0x%h, data=0x%h", 
                         $time, instr_addr, {unified_mem[instr_addr + 3], unified_mem[instr_addr + 2], 
                                            unified_mem[instr_addr + 1], unified_mem[instr_addr + 0]});
                // `endif
            end // is_prog_addr || is_data_addr
        end // rst_n
    end
    
    // Data memory handling
    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mem_rdata <= 32'h00000000;
            mem_ready <= 1'b0;
            uart_tx_en_reg <= 1'b0;
            uart_rx_en_reg <= 1'b0;
            uart_rx_break_reg <= 1'b0;
            uart_rx_valid_reg <= 1'b0;
            gpio_reg <= {GPIO_SIZE{1'b0}};
        end else begin

            // This signal is only active for 1 cycle, so we need to latch it
            if (uart_rx_valid) begin
                uart_rx_valid_reg <= uart_rx_valid;
            end
        
            if (is_uart_addr) begin
                uart_tx_en_reg <= 1'b0;

                if (mem_we) begin
                    case (mem_addr[3:0])
                        4'h0: `UART_WRITE_TX_DATA(mem_wdata)
                        4'h4: `UART_WRITE_CONTROL(mem_wdata)
                        4'h8: `UART_WRITE_RX_DATA_IGNORED(mem_wdata)
                        4'hC: `UART_WRITE_RX_CONTROL(mem_wdata)
                        default: `UART_WRITE_RESERVED(mem_addr, mem_wdata)
                    endcase
                end else begin
                    case (mem_addr[3:0])
                        4'h0: `UART_READ_TX_DATA(mem_rdata)
                        4'h4: `UART_READ_CONTROL(mem_rdata)
                        4'h8: `UART_READ_RX_DATA(mem_rdata)
                        4'hC: `UART_READ_RX_CONTROL(mem_rdata)
                        default: `UART_READ_RESERVED(mem_rdata, mem_addr)
                    endcase
                end
                mem_ready <= 1'b1;
            end

            if (gpio_request) begin
                if (mem_we) begin
                    gpio_reg <= mem_wdata[GPIO_SIZE-1:0];
                end else begin
                    mem_rdata <= {27'b0, gpio_reg};
                end
                mem_ready <= 1'b1;
                access_state <= ACCESS_IDLE;
            end
        
            if (is_data_addr) begin
                mem_ready <= 1'b0;

                if (mem_we) begin
                    // Write operation using byte enable signals based on write_flag
                    // write_flag corresponds to funct3 field:
                    // 3'b000 → SB (Store Byte)
                    // 3'b001 → SH (Store Halfword)
                    // 3'b010 → SW (Store Word)

                    unified_mem[mem_addr + 0] <= mem_wdata[7:0];
                    if (mem_flag == 3'b001 || mem_flag == 3'b010) unified_mem[mem_addr + 1] <= mem_wdata[15:8];
                    if (mem_flag == 3'b010) unified_mem[mem_addr + 2] <= mem_wdata[23:16];
                    if (mem_flag == 3'b010) unified_mem[mem_addr + 3] <= mem_wdata[31:24];
                    
                    mem_ready <= 1'b1;
                    
                    // `ifdef SIM_DEBUG
                    case (mem_flag)
                        3'b000: $display("Time %0t: TEST_MEM - SB (Store Byte): addr=0x%h, data=0x%02h, mem_flag=0x%h", 
                                        $time, mem_addr, mem_wdata[7:0], mem_flag);
                        3'b001: $display("Time %0t: TEST_MEM - SH (Store Halfword): addr=0x%h, data=0x%04h, mem_flag=0x%h", 
                                        $time, mem_addr, mem_wdata[15:0], mem_flag);
                        3'b010: $display("Time %0t: TEST_MEM - SW (Store Word): addr=0x%h, data=0x%08h, mem_flag=0x%h", 
                                        $time, mem_addr, mem_wdata, mem_flag);
                        default: $display("Time %0t: TEST_MEM - Unknown store type: mem_flag=0x%h, addr=0x%h, data=0x%08h", 
                                         $time, mem_flag, mem_addr, mem_wdata);
                    endcase
                    // `endif
                end else if (mem_re) begin
                    // Read operation - 32-bit word read from byte memory
                    mem_rdata <= {unified_mem[mem_addr + 3], unified_mem[mem_addr + 2], 
                                  unified_mem[mem_addr + 1], unified_mem[mem_addr + 0]};
                    mem_ready <= 1'b1;
                    
                    // `ifdef SIM_DEBUG
                    $display("Time %0t: TEST_MEM - Data read: addr=0x%h, data=0x%h", 
                             $time, mem_addr, {unified_mem[mem_addr + 3], unified_mem[mem_addr + 2], 
                                               unified_mem[mem_addr + 1], unified_mem[mem_addr + 0]});
                    // `endif
                end // mem_re
            end // is_data_addr
        end // rst_n
    end
    `endif // !USE_MEMORY_DELAY
    
    `ifdef USE_MEMORY_DELAY
    // Unified memory access handling with data priority
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            instr_data <= 32'h00000000;
            instr_ready <= 1'b0;
            mem_rdata <= 32'h00000000;
            mem_ready <= 1'b0;
            access_state <= ACCESS_IDLE;
            access_delay_counter <= 3'b0;
            current_addr <= 32'h0;
            current_wdata <= 32'h0;
            current_flag <= 3'b0;
            current_we <= 1'b0;
            current_is_instr <= 1'b0;

            uart_tx_en_reg <= 1'b0;
            uart_rx_en_reg <= 1'b0;
            uart_rx_break_reg <= 1'b0;
            uart_rx_valid_reg <= 1'b0;

            gpio_reg <= {GPIO_SIZE{1'b0}};

            // Keep SPI signals in safe state
            flash_cs_n <= 1'b1;
            ram_cs_n <= 1'b1;
            spi_sclk <= 1'b0;
            spi_mosi <= 1'b0;
        end else begin

            // This signal is only active for 1 cycle, so we need to latch it
            if (uart_rx_valid) begin
                uart_rx_valid_reg <= uart_rx_valid;
            end

            case (access_state)
                ACCESS_IDLE: begin
                    // Clear ready signals when starting new access
                    // if (start_data_access || start_instr_access) begin
                        instr_ready <= 1'b0;
                        mem_ready <= 1'b0;
                    // end
                    
                    // Priority 1: Data memory access (higher priority)
                    if (start_data_access) begin
                        current_addr <= mem_addr;
                        current_wdata <= mem_wdata;
                        current_flag <= mem_flag;
                        current_we <= mem_we;
                        current_is_instr <= 1'b0;
                        access_state <= ACCESS_ACTIVE;
                        access_delay_counter <= DATA_ACCESS_DELAY - 1;
                        if (is_uart_addr) begin
                            uart_tx_en_reg <= 1'b0;

                            if (mem_we) begin
                                case (mem_addr[3:0])
                                    4'h0: `UART_WRITE_TX_DATA(mem_wdata)
                                    4'h4: `UART_WRITE_CONTROL(mem_wdata)
                                    4'h8: `UART_WRITE_RX_DATA_IGNORED(mem_wdata)
                                    4'hC: `UART_WRITE_RX_CONTROL(mem_wdata)
                                    default: `UART_WRITE_RESERVED(mem_addr, mem_wdata)
                                endcase
                            end else begin
                                case (mem_addr[3:0])
                                    4'h0: `UART_READ_TX_DATA(mem_rdata)
                                    4'h4: `UART_READ_CONTROL(mem_rdata)
                                    4'h8: `UART_READ_RX_DATA(mem_rdata)
                                    4'hC: `UART_READ_RX_CONTROL(mem_rdata)
                                    default: `UART_READ_RESERVED(mem_rdata, mem_addr)
                                endcase
                            end
                            mem_ready <= 1'b1;
                            access_state <= ACCESS_IDLE;
                        end

                        if (gpio_request) begin
                            if (mem_we) begin
                                gpio_reg <= mem_wdata[GPIO_SIZE-1:0];
                            end else begin
                                mem_rdata <= {27'b0, gpio_reg};
                            end
                            mem_ready <= 1'b1;
                            access_state <= ACCESS_IDLE;
                        end
                        
                        if (mem_we) begin
                            case (current_flag)
                                3'b000: $display("Time %0t: TEST_MEM - Starting SB (Store Byte): addr=0x%h, data=0x%02h, delay=%0d cycles", 
                                                $time, mem_addr, mem_wdata[7:0], DATA_ACCESS_DELAY);
                                3'b001: $display("Time %0t: TEST_MEM - Starting SH (Store Halfword): addr=0x%h, data=0x%04h, delay=%0d cycles", 
                                                $time, mem_addr, mem_wdata[15:0], DATA_ACCESS_DELAY);
                                3'b010: $display("Time %0t: TEST_MEM - Starting SW (Store Word): addr=0x%h, data=0x%08h, delay=%0d cycles", 
                                                $time, mem_addr, mem_wdata, DATA_ACCESS_DELAY);
                                default: $display("Time %0t: TEST_MEM - Starting unknown store: mem_flag=0x%h, addr=0x%h, data=0x%08h, delay=%0d cycles", 
                                                 $time, current_flag, mem_addr, mem_wdata, DATA_ACCESS_DELAY);
                            endcase
                        end else begin
                            $display("Time %0t: TEST_MEM - Starting data read: addr=0x%h, delay=%0d cycles", 
                                     $time, mem_addr, DATA_ACCESS_DELAY);
                        end
                    end
                    // Priority 2: Instruction fetch (lower priority)
                    else if (start_instr_access) begin
                        current_addr <= instr_addr;
                        current_wdata <= 32'h0;
                        current_flag <= 3'b0;
                        current_we <= 1'b0;
                        current_is_instr <= 1'b1;
                        access_state <= ACCESS_ACTIVE;
                        access_delay_counter <= INSTR_FETCH_DELAY - 1;
                        
                        // `ifdef SIM_DEBUG
                        $display("Time %0t: TEST_MEM - Starting instruction fetch: addr=0x%h, delay=%0d cycles", 
                                 $time, instr_addr, INSTR_FETCH_DELAY);
                        // `endif
                    end
                end
                
                ACCESS_ACTIVE: begin
                    if (access_delay_counter == 0) begin
                        // Access complete
                        if (current_is_instr) begin
                            // Instruction fetch complete
                            instr_data <= {unified_mem[instr_addr + 3], unified_mem[instr_addr + 2], 
                                          unified_mem[instr_addr + 1], unified_mem[instr_addr + 0]};
                            instr_ready <= 1'b1;
                            
                            // `ifdef SIM_DEBUG
                            $display("Time %0t: TEST_MEM - Instruction fetch complete: addr=0x%h, data=0x%h", 
                                     $time, current_addr, {unified_mem[instr_addr + 3], unified_mem[instr_addr + 2], 
                                                          unified_mem[instr_addr + 1], unified_mem[instr_addr + 0]});
                            // `endif
                        end else begin
                            // Data access complete
                            if (current_we) begin
                                // Write operation using byte enable signals based on write_flag
                                // write_flag corresponds to funct3 field:
                                // 3'b000 → SB (Store Byte)
                                // 3'b001 → SH (Store Halfword)
                                // 3'b010 → SW (Store Word)
                                unified_mem[mem_addr + 0] <= current_wdata[7:0];
                                if (current_flag == 3'b001 || current_flag == 3'b010) 
                                    unified_mem[mem_addr + 1] <= current_wdata[15:8];
                                if (current_flag == 3'b010) 
                                    unified_mem[mem_addr + 2] <= current_wdata[23:16];
                                if (current_flag == 3'b010) 
                                    unified_mem[mem_addr + 3] <= current_wdata[31:24];
                                
                                // `ifdef SIM_DEBUG
                                case (current_flag)
                                    3'b000: $display("Time %0t: TEST_MEM - SB (Store Byte) complete: addr=0x%h, data=0x%02h", 
                                                    $time, current_addr, current_wdata[7:0]);
                                    3'b001: $display("Time %0t: TEST_MEM - SH (Store Halfword) complete: addr=0x%h, data=0x%04h", 
                                                    $time, current_addr, current_wdata[15:0]);
                                    3'b010: $display("Time %0t: TEST_MEM - SW (Store Word) complete: addr=0x%h, data=0x%08h", 
                                                    $time, current_addr, current_wdata);
                                    default: $display("Time %0t: TEST_MEM - Unknown store complete: mem_flag=0x%h, addr=0x%h, data=0x%08h", 
                                                    $time, current_flag, current_addr, current_wdata);
                                endcase
                                // `endif
                            end else begin
                                // Read operation - 32-bit word read from byte memory
                                mem_rdata <= {unified_mem[mem_addr + 3], unified_mem[mem_addr + 2], 
                                            unified_mem[mem_addr + 1], unified_mem[mem_addr + 0]};
                                
                                // `ifdef SIM_DEBUG
                                $display("Time %0t: TEST_MEM - Data read complete: addr=0x%h, data=0x%h", 
                                        $time, current_addr, {unified_mem[mem_addr + 3], unified_mem[mem_addr + 2], 
                                                            unified_mem[mem_addr + 1], unified_mem[mem_addr + 0]});
                                // `endif
                            end
                            mem_ready <= 1'b1;
                        end
                        
                        access_state <= ACCESS_IDLE;
                    end else begin
                        access_delay_counter <= access_delay_counter - 1;
                    end
                end
                
                default: access_state <= ACCESS_IDLE;
            endcase
        end
    end
    `endif // USE_MEMORY_DELAY

    // Debug output for memory contents
    `ifdef SIM_DEBUG
    initial begin
        $display("Test Memory Controller Debug Info:");
        $display("Unified Memory Size: %0d bytes", TOTAL_MEM_SIZE);
        $display("Program Memory Size: %0d bytes", PROG_MEM_SIZE);
        $display("Data Memory Size: %0d bytes", DATA_MEM_SIZE);
        $display("Program Address Range: 0x00000000 - 0x%08h", PROG_MEM_SIZE - 1);
        $display("Data Address Range: 0x00002000 - 0x%08h", 32'h00002000 + DATA_MEM_SIZE - 1);
        $display("Memory Access Policy:");
        $display("  - SEQUENTIAL ACCESS: Only instruction OR data access at a time");
        $display("  - DATA PRIORITY: Data memory access has higher priority than instruction fetch");
        $display("Memory Access Delays:");
        $display("  - Instruction fetch: %0d cycles", INSTR_FETCH_DELAY);
        $display("  - Data access: %0d cycles", DATA_ACCESS_DELAY);
        $display("Store operations supported via write_flag (funct3):");
        $display("  - write_flag=3'b000 → SB (Store Byte): Writes 1 byte");
        $display("  - write_flag=3'b001 → SH (Store Halfword): Writes 2 bytes");
        $display("  - write_flag=3'b010 → SW (Store Word): Writes 4 bytes");
    end
    `endif

endmodule 
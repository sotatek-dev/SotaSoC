/* Memory Controller for RV32I SoC
 * 
 * This controller handles:
 * - Instruction fetch from SPI Flash 
 * - Data memory operations to SPI RAM
 * - Address mapping and SPI protocol handling
 * 
 * Memory Map:
 * 0x80000000 - 0x8FFFFFFF: Flash (Instructions)
 * 0x00000000 - 0x0FFFFFFF: RAM (Data)
 */

`include "debug_defines.vh"

module mem_ctl #(
    parameter FLASH_SIZE = 32'h00002000,
    parameter PSRAM_SIZE = 32'h00002000,
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
    output wire instr_ready,
    
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

    // Shared SPI interface
    output wire flash_cs_n,
    output wire ram_cs_n,
    output wire spi_sclk,
    output wire spi_mosi,
    input wire spi_miso
);
    localparam ACCESS_IDLE = 3'b000;
    localparam ACCESS_ACTIVE = 3'b001;
    localparam ACCESS_PAUSE = 3'b010;
    localparam ACCESS_STOP = 3'b011;
    localparam ACCESS_NEXT_INSTR = 3'b100;

    // SPI Flash commands
    localparam FLASH_READ_CMD = 8'h03;  // Read command
    
    // SPI RAM commands  
    localparam RAM_READ_CMD = 8'h03;    // Read command
    localparam RAM_WRITE_CMD = 8'h02;   // Write command

    reg [2:0] access_state;

    reg instr_ready_reg;

    reg [31:0] next_instr_data;
    reg next_instr_ready_reg;

    // SPI signals
    reg spi_start;
    reg spi_stop;
    reg spi_cont_read;
    reg spi_write_enable;
    reg spi_read_enable;
    reg [31:0] spi_cmd_addr;
    reg [31:0] spi_data_in;
    wire [31:0] spi_data_out;
    wire spi_done;

    wire spi_cs_n;

    reg [5:0] spi_data_len;
    reg spi_is_instr;

    reg [GPIO_SIZE-1:0] gpio_reg;

    // UART controller interface signals
    wire [31:0] uart_mem_rdata;

    assign gpio_out = gpio_reg;

    // SPI Master instance
    spi_master spi_master_inst (
        .clk(clk),
        .rst_n(rst_n),
        
        // CPU interface
        .start(spi_start),
        .stop(spi_stop),
        .cont_read(spi_cont_read),
        .write_enable(spi_write_enable),
        .is_instr(spi_is_instr),
        .cmd_addr(spi_cmd_addr),
        .data_len(spi_data_len),
        .data_in(spi_data_in),
        .data_out(spi_data_out),
        .done(spi_done),
        
        // SPI interface
        .spi_clk(spi_sclk),
        .spi_cs_n(spi_cs_n),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso)
    );

    // UART Controller instance
    uart_ctl uart_ctl_inst (
        .clk(clk),
        .rst_n(rst_n),
        
        // Memory-mapped interface
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_we(mem_we),
        .mem_re(mem_re),
        .mem_rdata(uart_mem_rdata),
        
        // UART TX interface
        .uart_tx_en(uart_tx_en),
        .uart_tx_data(uart_tx_data),
        .uart_tx_busy(uart_tx_busy),
        
        // UART RX interface
        .uart_rx_en(uart_rx_en),
        .uart_rx_break(uart_rx_break),
        .uart_rx_valid(uart_rx_valid),
        .uart_rx_data(uart_rx_data)
    );

    wire instr_addr_not_changed = instr_addr[23:0] == spi_cmd_addr[23:0];
    wire instr_addr_changed = !instr_addr_not_changed;

    assign instr_ready = instr_ready_reg && instr_addr_not_changed;

    // we can access data in flash memory, like const data
    assign flash_cs_n = (spi_is_instr == 1'b1 || (spi_is_instr == 1'b0 && mem_addr < FLASH_SIZE)) && spi_stop == 1'b0 ? spi_cs_n : 1'b1;
    assign ram_cs_n = (spi_is_instr == 1'b0 && mem_addr >= FLASH_SIZE) && spi_stop == 1'b0 ? spi_cs_n : 1'b1;

    // There are 2 cases of memory access:
    // 1. The mem_ctl is at ACCESS_IDLE state and the core is requesting memory access
    //    In this case, we check data_request based on mem_we or mem_re
    // 2. The mem_ctl is at ACCESS_ACTIVE or ACCESS_PAUSE state and the core is requesting memory access
    //    In this case, we stop current transaction (set spi_stop to 1) and switch to ACCESS_STOP state.
    //    And because the mem_we and mem_re are high for only 1 cycle, so we need to capture these values to spi_write_enable and spi_read_enable.
    //
    // spi_write_enable and spi_read_enable are cleared to 0 when the transaction is complete.
    wire mem_write_request = mem_we || spi_write_enable;
    wire mem_read_request = mem_re || spi_read_enable;

    // Request signals
    wire data_request = mem_write_request || mem_read_request;
    wire instr_request = instr_addr_changed || !instr_ready_reg;
    wire uart_request = data_request && (mem_addr >= UART_BASE_ADDR) && (mem_addr < UART_BASE_ADDR + UART_SIZE);
    wire gpio_request = data_request && (mem_addr == GPIO_BASE_ADDR);
    
    // Priority logic: data has higher priority
    wire start_data_access = data_request && (access_state == ACCESS_IDLE || ACCESS_PAUSE);
    wire start_instr_access = instr_request && (access_state == ACCESS_IDLE) && !data_request;

    wire [23:0] next_instr_addr = spi_cmd_addr[23:0] + 4;

    // SPI access handling
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            instr_data <= 32'h00000000;
            instr_ready_reg <= 1'b0;
            mem_rdata <= 32'h00000000;
            mem_ready <= 1'b0;
            access_state <= ACCESS_IDLE;

            next_instr_data <= 32'h00000000;
            next_instr_ready_reg <= 1'b0;

            gpio_reg <= {GPIO_SIZE{1'b0}};

            spi_start <= 1'b0;
            spi_stop <= 1'b0;
            spi_cont_read <= 1'b0;
            spi_write_enable <= 1'b0;
            spi_read_enable <= 1'b0;
            spi_cmd_addr <= 32'h0;
            spi_data_in <= 32'h0;

            spi_data_len <= 6'b0;
            spi_is_instr <= 1'b0;
        end else begin
            spi_start <= 1'b0;
            spi_stop <= 1'b0;
            spi_cont_read <= 1'b0;

            // `DEBUG_PRINT(("Time %0t: SPI_MEM - access_state: %d, start_data_access: %d, mem_we %d", $time, access_state, start_data_access, mem_we));

            // If we need to access memory but mem ctl is reading instruction => stop reading instruction
            if (start_data_access && (access_state == ACCESS_ACTIVE || ACCESS_PAUSE) && spi_is_instr == 1'b1) begin
                spi_stop <= 1'b1;
                spi_is_instr <= 1'b0;
                spi_write_enable <= mem_we;
                spi_read_enable <= mem_re;
                access_state <= ACCESS_STOP;
                `DEBUG_PRINT(("Time %0t: SPI_MEM - Stopping instruction fetch: addr=0x%h", $time, instr_addr));
            end else begin // normal access
                case (access_state)
                    ACCESS_IDLE: begin
                        mem_ready <= 1'b0;
                        
                        // Priority 1: Data memory access (higher priority)
                        if (start_data_access) begin
                            instr_ready_reg <= 1'b0;
                            spi_start <= 1'b1;
                            if (mem_write_request) begin
                                spi_cmd_addr <= {8'h02, mem_addr[23:0]};
                            end else begin
                                spi_cmd_addr <= {8'h03, mem_addr[23:0]};
                            end
                            spi_data_in <= (mem_flag == 3'b000) ? {mem_wdata[7:0], 24'h0} :
                                            (mem_flag == 3'b001) ? {mem_wdata[7:0], mem_wdata[15:8], 16'h0} :
                                            (mem_flag == 3'b010) ? {mem_wdata[7:0], mem_wdata[15:8], mem_wdata[23:16], mem_wdata[31:24]} :
                                            {mem_wdata[7:0], mem_wdata[15:8], mem_wdata[23:16], mem_wdata[31:24]};
                            spi_data_len <= (mem_flag == 3'b000) ? 6'h08 :
                                            (mem_flag == 3'b001) ? 6'h10 :
                                            (mem_flag == 3'b010) ? 6'h20 :
                                            (mem_flag == 3'b100) ? 6'h08 :
                                            (mem_flag == 3'b101) ? 6'h10 :
                                            6'h00;
                            spi_write_enable <= mem_write_request;
                            spi_read_enable <= mem_read_request;
                            spi_is_instr <= 1'b0;
                            access_state <= ACCESS_ACTIVE;

                            if (uart_request) begin
                                // UART requests are handled by uart_ctl module
                                // Just forward the response
                                mem_rdata <= uart_mem_rdata;
                                spi_start <= 1'b0;
                                mem_ready <= 1'b1;
                                access_state <= ACCESS_IDLE;
                            end

                            if (gpio_request) begin
                                if (mem_we) begin
                                    gpio_reg <= mem_wdata[GPIO_SIZE-1:0];
                                end else begin
                                    mem_rdata <= {27'b0, gpio_reg};
                                end
                                spi_start <= 1'b0;
                                mem_ready <= 1'b1;
                                access_state <= ACCESS_IDLE;
                            end
                            
                            if (mem_we) begin
                                case (mem_flag)
                                    3'b000: `DEBUG_PRINT(("Time %0t: SPI_MEM - Starting SB (Store Byte): addr=0x%h, data=0x%02h", 
                                                    $time, mem_addr, mem_wdata[7:0]));
                                    3'b001: `DEBUG_PRINT(("Time %0t: SPI_MEM - Starting SH (Store Halfword): addr=0x%h, data=0x%04h", 
                                                    $time, mem_addr, mem_wdata[15:0]));
                                    3'b010: `DEBUG_PRINT(("Time %0t: SPI_MEM - Starting SW (Store Word): addr=0x%h, data=0x%08h", 
                                                    $time, mem_addr, mem_wdata));
                                    default: `DEBUG_PRINT(("Time %0t: SPI_MEM - Starting unknown store: mem_flag=0x%h, addr=0x%h, data=0x%08h", 
                                                    $time, mem_flag, mem_addr, mem_wdata));
                                endcase
                            end else begin
                                `DEBUG_PRINT(("Time %0t: SPI_MEM - Starting data read: addr=0x%h", 
                                        $time, mem_addr));
                            end
                        end
                        // Priority 2: Instruction fetch (lower priority)
                        else if (start_instr_access) begin
                            instr_ready_reg <= 1'b0;
                            next_instr_data <= 32'h00000000;
                            next_instr_ready_reg <= 1'b0;
                            spi_start <= 1'b1;
                            spi_cmd_addr <= {8'h03, instr_addr[23:0]};
                            spi_data_in <= 32'h0;
                            spi_data_len <= 6'h20;
                            spi_write_enable <= 1'b0;
                            spi_is_instr <= 1'b1;
                            access_state <= ACCESS_ACTIVE;
                            
                            `DEBUG_PRINT(("Time %0t: SPI_MEM - Starting instruction fetch: addr=0x%h", 
                                    $time, instr_addr));
                        end
                    end

                    ACCESS_STOP: begin
                        instr_ready_reg <= 1'b0;
                        next_instr_data <= 32'h00000000;
                        next_instr_ready_reg <= 1'b0;
                        mem_ready <= 1'b0;
                        spi_start <= 1'b0;
                        spi_cont_read <= 1'b0;
                        spi_cmd_addr <= 32'h0;
                        spi_data_in <= 32'h0;
                        spi_data_len <= 6'b0;
                        spi_is_instr <= 1'b0;

                        spi_stop <= 1'b0;
                        access_state <= ACCESS_IDLE;
                    end
                    
                    ACCESS_ACTIVE: begin
                        if (spi_done == 1'b1) begin
                            // Access complete
                            if (spi_is_instr) begin
                                // Instruction fetch complete
                                instr_data <= {spi_data_out[7:0], spi_data_out[15:8], spi_data_out[23:16], spi_data_out[31:24]};
                                instr_ready_reg <= 1'b1;

                                // Fetch next instruction automatically
                                next_instr_ready_reg <= 1'b0;
                                spi_cont_read <= 1'b1;
                                access_state <= ACCESS_NEXT_INSTR;
                                // access_state <= ACCESS_PAUSE;
                                
                                `DEBUG_PRINT(("Time %0t: SPI_MEM - Instruction fetch complete: addr=0x%h, data=0x%h", 
                                        $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_out));
                            end else begin
                                // Data access complete
                                if (spi_write_enable) begin
                                    case (spi_data_len)
                                        6'h08: `DEBUG_PRINT(("Time %0t: SPI_MEM - SB (Store Byte) complete: addr=0x%h, data=0x%02h", 
                                                        $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_in[7:0]));
                                        6'h10: `DEBUG_PRINT(("Time %0t: SPI_MEM - SH (Store Halfword) complete: addr=0x%h, data=0x%04h", 
                                                        $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_in[15:0]));
                                        6'h20: `DEBUG_PRINT(("Time %0t: SPI_MEM - SW (Store Word) complete: addr=0x%h, data=0x%08h", 
                                                        $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_in));
                                        default: `DEBUG_PRINT(("Time %0t: SPI_MEM - Unknown store complete: spi_data_len=0x%h, addr=0x%h, data=0x%08h", 
                                                        $time, spi_data_len, {8'b0, spi_cmd_addr[23:0]}, spi_data_in));
                                    endcase
                                end else begin
                                    // Read operation - 32-bit word read from byte memory
                                    mem_rdata <= (mem_flag == 3'b000) ? {24'h0, spi_data_out[7:0]} :
                                                (mem_flag == 3'b001) ? {16'h0, spi_data_out[7:0], spi_data_out[15:8]} :
                                                (mem_flag == 3'b010) ? {spi_data_out[7:0], spi_data_out[15:8], spi_data_out[23:16], spi_data_out[31:24]} :
                                                (mem_flag == 3'b100) ? {24'h0, spi_data_out[7:0]} :
                                                (mem_flag == 3'b101) ? {16'h0, spi_data_out[7:0], spi_data_out[15:8]} :
                                                {spi_data_out[7:0], spi_data_out[15:8], spi_data_out[23:16], spi_data_out[31:24]};
                                    
                                    `DEBUG_PRINT(("Time %0t: TEST_MEM - Data read complete: addr=0x%h, data=0x%h", 
                                            $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_out));
                                end
                                mem_ready <= 1'b1;
                                spi_write_enable <= 1'b0;
                                spi_read_enable <= 1'b0;
                                access_state <= ACCESS_IDLE;
                            end
                        end
                    end

                    ACCESS_NEXT_INSTR: begin
                        // If this is jump instruction, stop current instruction fetch
                        if (instr_addr_changed && instr_addr[23:0] != next_instr_addr) begin
                            spi_stop <= 1'b1;
                            spi_is_instr <= 1'b0;
                            spi_write_enable <= mem_we;
                            spi_read_enable <= mem_re;
                            access_state <= ACCESS_STOP;
                        end else begin
                            if (spi_done == 1'b1) begin
                                // Instruction fetch complete
                                next_instr_data <= {spi_data_out[7:0], spi_data_out[15:8], spi_data_out[23:16], spi_data_out[31:24]};
                                next_instr_ready_reg <= 1'b1;
                                access_state <= ACCESS_PAUSE;
                                
                                `DEBUG_PRINT(("Time %0t: SPI_MEM - Next instruction fetch complete: addr=0x%h, data=0x%h", 
                                        $time, {8'b0, next_instr_addr[23:0]}, spi_data_out));
                            end
                        end
                    end

                    ACCESS_PAUSE: begin
                        mem_ready <= 1'b0;
                        if (instr_addr_not_changed) begin
                            // do nothing
                        end else if (instr_addr[23:0] == next_instr_addr) begin
                            if (next_instr_ready_reg) begin
                                instr_data <= next_instr_data;
                                instr_ready_reg <= 1'b1;
                                spi_cmd_addr <= {8'h03, instr_addr[23:0]};

                                next_instr_ready_reg <= 1'b0;
                                spi_cont_read <= 1'b1;
                                access_state <= ACCESS_NEXT_INSTR;
                            end else begin
                                `DEBUG_PRINT(("Time %0t: SPI_MEM - It should not happen: next_instr_ready_reg=0, instr_addr=0x%h, next_instr_addr=0x%h", 
                                        $time, {8'b0, instr_addr[23:0]}, {8'b0, next_instr_addr[23:0]}));
                            end
                        end else begin
                            instr_ready_reg <= 1'b0;
                            spi_stop <= 1'b1;
                            access_state <= ACCESS_STOP;
                        end
                    end
                    
                    default: access_state <= ACCESS_IDLE;
                endcase
            end // end normal access
        end
    end
endmodule 
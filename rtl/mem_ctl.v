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

module mem_ctl #(
    parameter PROG_MEM_SIZE = 32'h00002000,
    parameter DATA_MEM_SIZE = 32'h00002000
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

    // Shared SPI interface
    output wire flash_cs_n,
    output wire ram_cs_n,
    output wire spi_sclk,
    output wire spi_mosi,
    input wire spi_miso
);
    localparam ACCESS_IDLE = 3'b000;
    localparam ACCESS_ACTIVE = 3'b001;

    // SPI Flash commands
    localparam FLASH_READ_CMD = 8'h03;  // Read command
    
    // SPI RAM commands  
    localparam RAM_READ_CMD = 8'h03;    // Read command
    localparam RAM_WRITE_CMD = 8'h02;   // Write command

    reg [2:0] access_state;

    // SPI signals
    reg spi_start;
    reg spi_write_enable;
    reg [31:0] spi_cmd_addr;
    reg [31:0] spi_data_in;
    wire [31:0] spi_data_out;
    wire spi_done;

    wire spi_cs_n;

    reg [5:0] spi_data_len;
    reg spi_is_instr;

    // SPI Master instance
    spi_master spi_master_inst (
        .clk(clk),
        .rst_n(rst_n),
        
        // CPU interface
        .start(spi_start),
        .write_enable(spi_write_enable),
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
    
    assign flash_cs_n = (spi_is_instr == 1'b1) ? spi_cs_n : 1'b1;
    assign ram_cs_n = (spi_is_instr == 1'b0) ? spi_cs_n : 1'b1;


    // Request signals
    wire data_request = mem_we || mem_re;
    wire instr_request = (instr_addr[23:0] != spi_cmd_addr[23:0]) || !instr_ready;
    
    // Priority logic: data has higher priority
    wire start_data_access = data_request && (access_state == ACCESS_IDLE);
    wire start_instr_access = instr_request && (access_state == ACCESS_IDLE) && !data_request;

    // SPI access handling
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            instr_data <= 32'h00000000;
            instr_ready <= 1'b0;
            mem_rdata <= 32'h00000000;
            mem_ready <= 1'b0;
            access_state <= ACCESS_IDLE;

            // uart_tx_en_reg <= 1'b0;
            // uart_rx_en_reg <= 1'b0;
            // uart_rx_break_reg <= 1'b0;
            // uart_rx_valid_reg <= 1'b0;

            spi_start <= 1'b0;
            spi_write_enable <= 1'b0;
            spi_cmd_addr <= 32'h0;
            spi_data_in <= 32'h0;

            spi_data_len <= 6'b0;
            spi_is_instr <= 1'b0;
        end else begin
            // This signal is only active for 1 cycle, so we need to latch it
            // if (uart_rx_valid) begin
            //     uart_rx_valid_reg <= uart_rx_valid;
            // end

            spi_start <= 1'b0;

            case (access_state)
                ACCESS_IDLE: begin
                    instr_ready <= 1'b0;
                    mem_ready <= 1'b0;
                    
                    // Priority 1: Data memory access (higher priority)
                    if (start_data_access) begin
                        spi_start <= 1'b1;
                        if (mem_we) begin
                            spi_cmd_addr <= {8'h02, mem_addr[23:0]};
                        end else begin
                            spi_cmd_addr <= {8'h03, mem_addr[23:0]};
                        end
                        spi_data_in <= (mem_flag == 3'b000) ? {mem_wdata[7:0], 24'h0} :
                                        (mem_flag == 3'b001) ? {mem_wdata[15:0], 16'h0} :
                                        (mem_flag == 3'b010) ? mem_wdata :
                                        mem_wdata;
                        spi_data_len <= (mem_flag == 3'b000) ? 6'h08 :
                                        (mem_flag == 3'b001) ? 6'h10 :
                                        (mem_flag == 3'b010) ? 6'h20 :
                                        (mem_flag == 3'b100) ? 6'h08 :
                                        (mem_flag == 3'b101) ? 6'h10 :
                                        6'h00;
                        spi_write_enable <= mem_we;
                        spi_is_instr <= 1'b0;
                        access_state <= ACCESS_ACTIVE;

                        // if (is_uart_addr) begin
                        //     uart_tx_en_reg <= 1'b0;

                        //     if (mem_we) begin
                        //         case (mem_addr[3:0])
                        //             4'h0: `UART_WRITE_TX_DATA(mem_wdata)
                        //             4'h4: `UART_WRITE_CONTROL(mem_wdata)
                        //             4'h8: `UART_WRITE_RX_DATA_IGNORED(mem_wdata)
                        //             4'hC: `UART_WRITE_RX_CONTROL(mem_wdata)
                        //             default: `UART_WRITE_RESERVED(mem_addr, mem_wdata)
                        //         endcase
                        //     end else begin
                        //         case (mem_addr[3:0])
                        //             4'h0: `UART_READ_TX_DATA(mem_rdata)
                        //             4'h4: `UART_READ_CONTROL(mem_rdata)
                        //             4'h8: `UART_READ_RX_DATA(mem_rdata)
                        //             4'hC: `UART_READ_RX_CONTROL(mem_rdata)
                        //             default: `UART_READ_RESERVED(mem_rdata, mem_addr)
                        //         endcase
                        //     end
                        //     mem_ready <= 1'b1;
                        //     access_state <= ACCESS_IDLE;
                        // end
                        
                        if (mem_we) begin
                            case (mem_flag)
                                3'b000: $display("Time %0t: SPI_MEM - Starting SB (Store Byte): addr=0x%h, data=0x%02h", 
                                                $time, mem_addr, mem_wdata[7:0]);
                                3'b001: $display("Time %0t: SPI_MEM - Starting SH (Store Halfword): addr=0x%h, data=0x%04h", 
                                                $time, mem_addr, mem_wdata[15:0]);
                                3'b010: $display("Time %0t: SPI_MEM - Starting SW (Store Word): addr=0x%h, data=0x%08h", 
                                                $time, mem_addr, mem_wdata);
                                default: $display("Time %0t: SPI_MEM - Starting unknown store: mem_flag=0x%h, addr=0x%h, data=0x%08h", 
                                                 $time, mem_flag, mem_addr, mem_wdata);
                            endcase
                        end else begin
                            $display("Time %0t: SPI_MEM - Starting data read: addr=0x%h", 
                                     $time, mem_addr);
                        end
                    end
                    // Priority 2: Instruction fetch (lower priority)
                    else if (start_instr_access) begin
                        spi_start <= 1'b1;
                        spi_cmd_addr <= {8'h03, instr_addr[23:0]};
                        spi_data_in <= 32'h0;
                        spi_data_len <= 6'h20;
                        spi_write_enable <= 1'b0;
                        spi_is_instr <= 1'b1;
                        access_state <= ACCESS_ACTIVE;
                        
                        // `ifdef SIM_DEBUG
                        $display("Time %0t: SPI_MEM - Starting instruction fetch: addr=0x%h", 
                                 $time, instr_addr);
                        // `endif
                    end
                end
                
                ACCESS_ACTIVE: begin
                    if (spi_done == 1'b1) begin
                        // Access complete
                        if (spi_is_instr) begin
                            // Instruction fetch complete
                            instr_data <= spi_data_out;
                            instr_ready <= 1'b1;
                            
                            // `ifdef SIM_DEBUG
                            $display("Time %0t: SPI_MEM - Instruction fetch complete: addr=0x%h, data=0x%h", 
                                     $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_out);
                            // `endif
                        end else begin
                            // Data access complete
                            if (spi_write_enable) begin
                                // `ifdef SIM_DEBUG
                                case (spi_data_len)
                                    6'h08: $display("Time %0t: SPI_MEM - SB (Store Byte) complete: addr=0x%h, data=0x%02h", 
                                                    $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_in[7:0]);
                                    6'h10: $display("Time %0t: SPI_MEM - SH (Store Halfword) complete: addr=0x%h, data=0x%04h", 
                                                    $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_in[15:0]);
                                    6'h20: $display("Time %0t: SPI_MEM - SW (Store Word) complete: addr=0x%h, data=0x%08h", 
                                                    $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_in);
                                    default: $display("Time %0t: SPI_MEM - Unknown store complete: spi_data_len=0x%h, addr=0x%h, data=0x%08h", 
                                                    $time, spi_data_len, {8'b0, spi_cmd_addr[23:0]}, spi_data_in);
                                endcase
                                // `endif
                            end else begin
                                // Read operation - 32-bit word read from byte memory
                                mem_rdata <= (mem_flag == 3'b000) ? {24'h0, spi_data_out[7:0]} :
                                            (mem_flag == 3'b001) ? {16'h0, spi_data_out[7:0], spi_data_out[15:8]} :
                                            (mem_flag == 3'b010) ? {spi_data_out[7:0], spi_data_out[15:8], spi_data_out[23:16], spi_data_out[31:24]} :
                                            (mem_flag == 3'b100) ? {24'h0, spi_data_out[7:0]} :
                                            (mem_flag == 3'b101) ? {16'h0, spi_data_out[7:0], spi_data_out[15:8]} :
                                            {spi_data_out[7:0], spi_data_out[15:8], spi_data_out[23:16], spi_data_out[31:24]};
                                
                                // `ifdef SIM_DEBUG
                                $display("Time %0t: TEST_MEM - Data read complete: addr=0x%h, data=0x%h", 
                                        $time, {8'b0, spi_cmd_addr[23:0]}, spi_data_out);
                                // `endif
                            end
                            mem_ready <= 1'b1;
                        end
                        
                        access_state <= ACCESS_IDLE;
                    end
                end
                
                default: access_state <= ACCESS_IDLE;
            endcase
        end
    end
endmodule 
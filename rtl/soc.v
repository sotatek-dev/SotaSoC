/* RV32I SoC - System on Chip
 * 
 * Integrates:
 * - RV32I processor core
 * - Memory controller with SPI Flash and SPI RAM interfaces
 * - UART TX for serial communication
 * - Clock and reset management
 * 
 * Memory Map:
 * 0x80000000 - 0x8FFFFFFF: SPI Flash (Instructions)
 * 0x00000000 - 0x0FFFFFFF: SPI RAM (Data)
 */

module soc #(
    parameter CLK_HZ = 10000000,
    parameter RESET_ADDR = 32'h00000000 ,
    parameter FLASH_SIZE = 32'h00002000,
    parameter PSRAM_SIZE = 32'h00002000,
    parameter UART_BIT_RATE = 115200,
    parameter GPIO_SIZE = 5
) (
    input wire clk,
    input wire rst_n,
    
    // Shared SPI interface
    output wire flash_cs_n,
    output wire ram_cs_n,
    output wire spi_sclk,
    output wire spi_mosi,
    input wire spi_miso,
    
    // UART interface
    output wire uart_tx,
    input wire uart_rx,

    // GPIO interface
    output wire [GPIO_SIZE-1:0] gpio_out,

    // Error flag
    output wire error_flag
);

    // Core to Memory Controller connections
    wire [31:0] core_instr_addr;
    wire [31:0] core_instr_data;
    wire [31:0] core_mem_addr;
    wire [31:0] core_mem_wdata;
    wire [31:0] core_mem_rdata;
    wire [2:0] core_mem_flag;
    wire core_mem_we;
    wire core_mem_re;
    
    // Memory controller ready signals
    wire mem_instr_ready;
    wire mem_data_ready;
    
    // UART TX connections
    wire uart_tx_en;
    wire uart_tx_busy;
    wire [7:0] uart_tx_data;

    wire uart_rx_en;
    wire uart_rx_break;
    wire uart_rx_valid;
    wire [7:0] uart_rx_data;
    
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
        .instr_ready(mem_instr_ready),
        
        // Data memory interface  
        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_flag(core_mem_flag),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_data(core_mem_rdata),
        .mem_ready(mem_data_ready),

        // Error flag
        .error_flag(error_flag)
    );
    
    // Memory Controller instantiation
    mem_ctl #(
        .FLASH_SIZE(FLASH_SIZE),
        .PSRAM_SIZE(PSRAM_SIZE),
        .GPIO_SIZE(GPIO_SIZE)
    ) mem_ctrl (
        .clk(clk),
        .rst_n(rst_n),
        
        // Core instruction interface
        .instr_addr(core_instr_addr),
        .instr_data(core_instr_data),
        .instr_ready(mem_instr_ready),
        
        // Core data interface
        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_flag(core_mem_flag),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_rdata(core_mem_rdata),
        .mem_ready(mem_data_ready),
        
        // UART TX interface
        .uart_tx_en(uart_tx_en),
        .uart_tx_busy(uart_tx_busy),
        .uart_tx_data(uart_tx_data),

        // UART RX interface
        .uart_rx_en(uart_rx_en),
        .uart_rx_break(uart_rx_break),
        .uart_rx_valid(uart_rx_valid),
        .uart_rx_data(uart_rx_data),
        
        // GPIO interface
        .gpio_out(gpio_out),
        
        // Shared SPI interface
        .flash_cs_n(flash_cs_n),
        .ram_cs_n(ram_cs_n),
        .spi_sclk(spi_sclk),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso)
    );
    
    // UART TX module instantiation
    uart_tx #(
        .CLK_HZ(CLK_HZ),
        .BIT_RATE(UART_BIT_RATE),
        .PAYLOAD_BITS(8),
        .STOP_BITS(1)
    ) uart_transmitter (
        .clk(clk),
        .resetn(rst_n),
        .uart_txd(uart_tx),
        .uart_tx_busy(uart_tx_busy),
        .uart_tx_en(uart_tx_en),
        .uart_tx_data(uart_tx_data)
    );

    uart_rx #(
        .CLK_HZ(CLK_HZ),
        .BIT_RATE(UART_BIT_RATE),
        .PAYLOAD_BITS(8),
        .STOP_BITS(1)
    ) uart_receiver (
        .clk(clk),
        .resetn(rst_n),
        .uart_rxd(uart_rx),
        .uart_rx_en(uart_rx_en),
        .uart_rx_break(uart_rx_break),
        .uart_rx_valid(uart_rx_valid),
        .uart_rx_data(uart_rx_data)
    );

endmodule

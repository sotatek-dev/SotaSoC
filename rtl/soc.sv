/* RV32I SoC - System on Chip
 * 
 * Integrates:
 * - RV32I processor core
 * - Memory controller with SPI Flash and SPI RAM interfaces
 * - Multiple UART instances for serial communication
 * - Clock and reset management
 * 
 */

module soc #(
    parameter RESET_ADDR       = 32'h00000000 ,
    parameter FLASH_BASE_ADDR  = 32'h00000000,
    parameter PSRAM_BASE_ADDR  = 32'h01000000,
    parameter UART_BASE_ADDR   = 32'h40000000,
    parameter GPIO_BASE_ADDR   = 32'h40001000,
    parameter TIMER_BASE_ADDR  = 32'h40002000,
    parameter PWM_BASE_ADDR    = 32'h40003000,
    parameter UART_NUM         = 1,  // Maximum 4 instances
    parameter UART_SPACING     = 32'h100,
    parameter GPIO_SIZE        = 5,
    parameter PWM_NUM          = 2
) (
    input wire clk,
    input wire rst_n,
    
    // Shared SPI interface
    output wire flash_cs_n,
    output wire ram_cs_n,
    output wire spi_sclk,
    input wire [3:0] spi_io_in,
    output wire [3:0] spi_io_out,
    output wire [3:0] spi_io_oe,
    
    // UART interface
    output wire [UART_NUM-1:0] uart_tx,
    input wire [UART_NUM-1:0] uart_rx,

    // GPIO interface
    output wire [GPIO_SIZE-1:0] gpio_out,

    // PWM interface
    output wire [PWM_NUM-1:0] pwm_out,

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

    wire [47:0] mtime;

    // Memory controller ready signals
    wire mem_instr_ready;
    wire mem_data_ready;

    // UART connections
    wire [UART_NUM*32-1:0] uart_mem_rdata;

    // Timer connections
    wire timer_interrupt;
    wire [31:0] timer_mem_rdata;

    // PWM connections
    wire [31:0] pwm_mem_rdata;

    // RV32I Core instantiation
    rv32i_core #(
        .RESET_ADDR(RESET_ADDR)
    ) cpu_core (
        .clk(clk),
        .rst_n(rst_n),
        
        // Instruction memory interface
        .o_instr_addr(core_instr_addr),
        .i_instr_data(core_instr_data),
        .i_instr_ready(mem_instr_ready),
        
        // Data memory interface  
        .o_mem_addr(core_mem_addr),
        .o_mem_wdata(core_mem_wdata),
        .o_mem_flag(core_mem_flag),
        .o_mem_we(core_mem_we),
        .o_mem_re(core_mem_re),
        .i_mem_data(core_mem_rdata),
        .i_mem_ready(mem_data_ready),

        .o_mtime(mtime),

        // Timer interrupt
        .i_timer_interrupt(timer_interrupt),

        // Error flag
        .o_error_flag(error_flag)
    );
    
    // Memory Controller instantiation
    mem_ctl #(
        .FLASH_BASE_ADDR(FLASH_BASE_ADDR),
        .PSRAM_BASE_ADDR(PSRAM_BASE_ADDR),
        .UART_BASE_ADDR(UART_BASE_ADDR),
        .UART_NUM(UART_NUM),
        .GPIO_BASE_ADDR(GPIO_BASE_ADDR),
        .GPIO_SIZE(GPIO_SIZE),
        .TIMER_BASE_ADDR(TIMER_BASE_ADDR),
        .PWM_BASE_ADDR(PWM_BASE_ADDR)
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
        
        // UART interface
        .uart_mem_rdata(uart_mem_rdata),
        
        // GPIO interface
        .gpio_out(gpio_out),

        // Timer interface
        .timer_mem_rdata(timer_mem_rdata),

        // PWM interface
        .pwm_mem_rdata(pwm_mem_rdata),
        
        // Shared SPI interface
        .flash_cs_n(flash_cs_n),
        .ram_cs_n(ram_cs_n),
        .spi_sclk(spi_sclk),
        .spi_io_in(spi_io_in),
        .spi_io_out(spi_io_out),
        .spi_io_oe(spi_io_oe)
    );

    // UART Controller module instantiation
    genvar i;
    generate
        for (i = 0; i < UART_NUM; i = i + 1) begin : uart_instances
            uart_ctl #(
                .UART_BASE_ADDR(UART_BASE_ADDR + (i * UART_SPACING)),
                .PAYLOAD_BITS(8),
                .STOP_BITS(1)
            ) uart_inst (
                .clk(clk),
                .rst_n(rst_n),
                .mem_addr(core_mem_addr),
                .mem_wdata(core_mem_wdata),
                .mem_we(core_mem_we),
                .mem_re(core_mem_re),
                .mem_rdata(uart_mem_rdata[i*32 +: 32]),
                .uart_tx(uart_tx[i]),
                .uart_rx(uart_rx[i])
            );
        end
    endgenerate

    // Timer module
    mtime_timer #(
        .TIMER_BASE_ADDR(TIMER_BASE_ADDR)
    ) timer_inst (
        .clk(clk),
        .rst_n(rst_n),

        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_rdata(timer_mem_rdata),

        .mtime(mtime),

        .timer_interrupt(timer_interrupt)
    );

    // PWM module
    pwm #(
        .PWM_BASE_ADDR(PWM_BASE_ADDR),
        .PWM_NUM(PWM_NUM),
        .COUNTER_WIDTH(16)
    ) pwm_inst (
        .clk(clk),
        .rst_n(rst_n),

        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_rdata(pwm_mem_rdata),

        .pwm_out(pwm_out)
    );

endmodule

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
    parameter REG_NUM          = 16,
    parameter RESET_ADDR       = 32'h00000000 ,
    parameter FLASH_BASE_ADDR  = 32'h00000000,
    parameter PSRAM_BASE_ADDR  = 32'h01000000,
    parameter UART_BASE_ADDR   = 32'h40000000,
    parameter GPIO_BASE_ADDR   = 32'h40001000,
    parameter TIMER_BASE_ADDR  = 32'h40002000,
    parameter PWM_BASE_ADDR    = 32'h40003000,
    parameter I2C_BASE_ADDR    = 32'h40004000,
    parameter SPI_BASE_ADDR    = 32'h40005000,
    parameter UART_NUM         = 1,  // Maximum 4 instances
    parameter UART_SPACING     = 32'h100,
    parameter GPIO_NUM_BIDIR   = 4,
    parameter GPIO_NUM_OUT     = 3,
    parameter GPIO_NUM_IN      = 6,
    parameter PWM_NUM          = 2
) (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    wire _unused_ena = ena;

    localparam UIO_OE_OUT = 1'b1;

    // ============ External wires ============
    // Shared SPI interface
    wire flash_cs_n;
    wire ram_cs_n;
    wire bus_spi_sclk;
    wire [3:0] bus_io_in;
    wire [3:0] bus_io_out;
    wire [3:0] bus_io_oe;

    // UART interface
    wire [UART_NUM-1:0] uart_tx;
    wire [UART_NUM-1:0] uart_rx;

    // GPIO bidirectional interface
    wire [GPIO_NUM_BIDIR-1:0] gpio_bidir_in;
    wire [GPIO_NUM_BIDIR-1:0] gpio_bidir_out;
    wire [GPIO_NUM_BIDIR-1:0] gpio_bidir_oe;

    // GPIO output-only interface
    wire [GPIO_NUM_OUT-1:0] gpio_out;

    // GPIO input-only interface
    wire [GPIO_NUM_IN-1:0] gpio_in;

    // PWM interface
    wire [PWM_NUM-1:0] pwm_ena;
    wire [PWM_NUM-1:0] pwm_out;

    // I2C interface
    wire i2c_ena;
    wire i2c_sda_in;
    wire i2c_sda_out;
    wire i2c_sda_oe;
    wire i2c_scl_in;
    wire i2c_scl_out;
    wire i2c_scl_oe;

    // SPI interface
    wire spi_ena;
    wire spi_sclk;
    wire spi_mosi;
    wire spi_miso;

    // Error flag
    wire error_flag;
    // ============ External wires ============

    // ============ Internal wires ============
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

    // Timer connections
    wire timer_interrupt;
    wire [31:0] timer_mem_rdata;

    // GPIO connections
    wire [31:0] gpio_mem_rdata;

    // PWM connections
    wire [31:0] pwm_mem_rdata;

    // UART connections
    wire [UART_NUM*32-1:0] uart_mem_rdata;

    // I2C connections
    wire [31:0] i2c_mem_rdata;

    // SPI connections
    wire [31:0] spi_mem_rdata;
    // ============ Internal wires ============

    // RV32I Core instantiation
    rv32i_core #(
        .REG_NUM(REG_NUM),
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
        .TIMER_BASE_ADDR(TIMER_BASE_ADDR),
        .PWM_BASE_ADDR(PWM_BASE_ADDR),
        .I2C_BASE_ADDR(I2C_BASE_ADDR),
        .SPI_BASE_ADDR(SPI_BASE_ADDR)
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
        .gpio_mem_rdata(gpio_mem_rdata),

        // Timer interface
        .timer_mem_rdata(timer_mem_rdata),

        // PWM interface
        .pwm_mem_rdata(pwm_mem_rdata),

        // I2C interface
        .i2c_mem_rdata(i2c_mem_rdata),

        // SPI Peripheral interface
        .spi_mem_rdata(spi_mem_rdata),

        // Shared SPI interface
        .flash_cs_n(flash_cs_n),
        .ram_cs_n(ram_cs_n),
        .spi_sclk(bus_spi_sclk),
        .spi_io_in(bus_io_in),
        .spi_io_out(bus_io_out),
        .spi_io_oe(bus_io_oe)
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

    // GPIO module
    gpio #(
        .GPIO_BASE_ADDR(GPIO_BASE_ADDR),
        .NUM_BIDIR(GPIO_NUM_BIDIR),
        .NUM_OUT(GPIO_NUM_OUT),
        .NUM_IN(GPIO_NUM_IN)
    ) gpio_inst (
        .clk(clk),
        .rst_n(rst_n),

        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_rdata(gpio_mem_rdata),

        .gpio_bidir_in(gpio_bidir_in),
        .gpio_bidir_out(gpio_bidir_out),
        .gpio_bidir_oe(gpio_bidir_oe),
        .gpio_out(gpio_out),
        .gpio_in(gpio_in)
    );

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

        .ena(pwm_ena),
        .pwm_out(pwm_out)
    );

    // I2C Master module
    i2c_master #(
        .I2C_BASE_ADDR(I2C_BASE_ADDR)
    ) i2c_inst (
        .clk(clk),
        .rst_n(rst_n),

        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_rdata(i2c_mem_rdata),

        .ena(i2c_ena),
        .i2c_sda_in(i2c_sda_in),
        .i2c_sda_out(i2c_sda_out),
        .i2c_sda_oe(i2c_sda_oe),
        .i2c_scl_in(i2c_scl_in),
        .i2c_scl_out(i2c_scl_out),
        .i2c_scl_oe(i2c_scl_oe)
    );

    // SPI Master module
    spi_master #(
        .SPI_BASE_ADDR(SPI_BASE_ADDR)
    ) spi_inst (
        .clk(clk),
        .rst_n(rst_n),

        .mem_addr(core_mem_addr),
        .mem_wdata(core_mem_wdata),
        .mem_we(core_mem_we),
        .mem_re(core_mem_re),
        .mem_rdata(spi_mem_rdata),

        .ena(spi_ena),
        .spi_sclk(spi_sclk),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso)
    );

    assign uart_rx[0] = ui_in[0];
    assign spi_miso = ui_in[1];
    assign gpio_in[GPIO_NUM_IN-1:0] = ui_in[7:2];

    assign uo_out[0] = error_flag;
    assign uo_out[1] = flash_cs_n;
    assign uo_out[2] = ram_cs_n;
    assign uo_out[3] = bus_spi_sclk;
    assign uo_out[4] = uart_tx[0];
    assign uo_out[5] = gpio_out[0];
    assign uo_out[6] = spi_ena ? spi_mosi : gpio_out[1];
    assign uo_out[7] = pwm_ena[0] ? pwm_out[0] : gpio_out[2];

    assign bus_io_in[3:0] = uio_in[3:0];

    assign gpio_bidir_in[0] = uio_in[4];  // Shared with I2C SDA
    assign gpio_bidir_in[1] = uio_in[5];  // Shared with I2C SCL
    assign gpio_bidir_in[2] = uio_in[6];  // Shared with SPI SCLK
    assign gpio_bidir_in[3] = uio_in[7];  // Shared with pwm[1]

    assign i2c_sda_in = uio_in[4];
    assign i2c_scl_in = uio_in[5];

    assign uio_out[3:0] = bus_io_out[3:0];
    assign uio_out[4] = i2c_ena ? i2c_sda_out : gpio_bidir_out[0];
    assign uio_out[5] = i2c_ena ? i2c_scl_out : gpio_bidir_out[1];
    assign uio_out[6] = spi_ena ? spi_sclk : gpio_bidir_out[2];
    assign uio_out[7] = pwm_ena[1] ? pwm_out[1] : gpio_bidir_out[3];

    assign uio_oe[3:0] = bus_io_oe[3:0];
    assign uio_oe[4] = i2c_ena ? i2c_sda_oe : gpio_bidir_oe[0];
    assign uio_oe[5] = i2c_ena ? i2c_scl_oe : gpio_bidir_oe[1];
    assign uio_oe[6] = spi_ena ? UIO_OE_OUT : gpio_bidir_oe[2];
    assign uio_oe[7] = pwm_ena[1] ? UIO_OE_OUT : gpio_bidir_oe[3];
endmodule

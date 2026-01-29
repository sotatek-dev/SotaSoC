/* RV32I SoC Testbench - cocotb wrapper */

module test_soc_tb;
    // Clock and reset
    reg clk;
    reg rst_n;

    wire error_flag;
    // Shared SPI interface
    wire flash_cs_n;
    wire ram_cs_n;
    wire bus_sclk;
    wire uart0_tx;
    wire[2:0] gpio_out;

    reg [3:0] bus_io_in;
    wire [3:0] bus_io_out;
    wire [3:0] gpio_io_out;

    reg uart0_rx;
    reg [5:0] gpio_in;
    reg [3:0] gpio_io_in;

    wire [1:0] pwm_out;

    wire spi_cs_n;
    wire spi_sclk;
    wire spi_mosi;
    reg spi_miso;

    // I2C interface signals
    reg i2c_ena;
    reg i2c_sda_in;
    wire i2c_sda_out;
    wire i2c_sda_oe;
    reg i2c_scl_in;
    wire i2c_scl_out;
    wire i2c_scl_oe;

    wire [7:0] ui_in;
    wire [7:0] uo_out;
    wire [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    assign ui_in[0] = uart0_rx;
    assign ui_in[1] = spi_miso;
    assign ui_in[7:2] = gpio_in;

    assign error_flag = uo_out[0];
    assign flash_cs_n = uo_out[1];
    assign ram_cs_n = uo_out[2];
    assign bus_sclk = uo_out[3];
    assign uart0_tx = uo_out[4];
    assign spi_cs_n = uo_out[5];
    assign spi_mosi = uo_out[6];
    assign gpio_out = uo_out[7:5];

    assign bus_io_out = uio_out[3:0];
    assign gpio_io_out = uio_out[7:4];

    assign uio_in[3:0] = bus_io_in;
    assign uio_in[4] = i2c_ena ? i2c_sda_in : gpio_io_in[0];
    assign uio_in[5] = i2c_ena ? i2c_scl_in : gpio_io_in[1];
    assign uio_in[7:6] = gpio_io_in[3:2];

    assign pwm_out[0] = uo_out[7];
    assign pwm_out[1] = uio_out[7];

    assign spi_sclk = uio_out[6];

    // I2C signal assignments
    // I2C SDA is on uio[4], SCL is on uio[5]
    // SDA and SCL are open-drain, so if oe is high(output), the signal is low,
    // and if oe is low (input), the signal is high-z
    assign i2c_sda_out = uio_oe[4] ? 1'b0 : 1'b1;
    assign i2c_sda_oe  = uio_oe[4];
    assign i2c_scl_out = uio_oe[5] ? 1'b0 : 1'b1;
    assign i2c_scl_oe  = uio_oe[5];

    `ifndef FLASH_BASE_ADDR  
    `define FLASH_BASE_ADDR 32'h00000000
    `endif

    `ifndef PSRAM_BASE_ADDR
    `define PSRAM_BASE_ADDR 32'h01000000
    `endif

    // Instantiate the SoC
    soc#(
        .FLASH_BASE_ADDR(`FLASH_BASE_ADDR),
        .PSRAM_BASE_ADDR(`PSRAM_BASE_ADDR)
    ) soc_inst (
        .ui_in(ui_in),
        .uo_out(uo_out),
        .uio_in(uio_in),
        .uio_out(uio_out),
        .uio_oe(uio_oe),
        .ena(1'b1),
        .clk(clk),
        .rst_n(rst_n)
    );

    // Monitor signals for debugging
    // always @(posedge clk) begin
    //     if (rst_n) begin
    //         $display("Time %0t: SOC_TB - PC=%h, Instr=%h, Flash_CS=%b, RAM_CS=%b, SPI_SCLK=%b, SPI_MOSI=%b, SPI_MISO=%b", 
    //                  $time, debug_pc, debug_instr, flash_cs_n, ram_cs_n, spi_sclk, spi_mosi, spi_miso);
    //         
    //         if (debug_reg_we) begin
    //             $display("Time %0t: SOC_TB - Register Write: x%0d = 0x%h", 
    //                      $time, debug_reg_addr[4:0], debug_reg_data);
    //         end
    //     end
    // end

    // Waveform dump for cocotb
    initial begin
        $dumpfile("vcd/test_soc_tb.vcd");
        $dumpvars(0, test_soc_tb);
    end

endmodule

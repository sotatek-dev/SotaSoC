/* RV32I SoC Testbench - cocotb wrapper */

module test_soc_tb;
    // Boot mode: 00=0cy, 01=1cy, 10=2cy, 11=3cy delay for QSPI data path (pin-mux simulation)
    localparam [1:0] BOOT_MODE = 2'b00;

    // Clock and reset
    reg clk;
    reg rst_n;

    wire error_flag;
    // Shared SPI interface
    wire flash_cs_n;
    wire ram_cs_n;
    wire bus_sclk;
    wire uart0_tx;
    wire[5:0] gpio_out;

    reg [3:0] bus_io_in;
    wire [3:0] bus_io_out;
    wire [0:0] gpio_io_out;

    reg uart0_rx = 0;
    // gpio_in[5:4] = boot_mode; initial value simulates pull at boot, then freely changeable (GPIO)
    reg [5:0] gpio_in = {BOOT_MODE, 4'b0000};
    reg [0:0] gpio_io_in = 0;

    // Pipeline to simulate pin-mux delay on QSPI input; selection by BOOT_MODE
    reg [3:0] bus_io_in_d1, bus_io_in_d2, bus_io_in_d3;
    wire [3:0] bus_io_in_eff = (BOOT_MODE == 2'b00) ? bus_io_in :
                               (BOOT_MODE == 2'b01) ? bus_io_in_d1 :
                               (BOOT_MODE == 2'b10) ? bus_io_in_d2 : bus_io_in_d3;

    wire [1:0] pwm_out;

    wire spi_cs_n;
    wire spi_sclk;
    wire spi_mosi;
    reg spi_miso = 0;

    // I2C interface signals
    reg i2c_ena = 0;
    reg i2c_sda_in = 0;
    wire i2c_sda_out;
    wire i2c_scl_out;

    wire [7:0] ui_in;
    wire [7:0] uo_out;
    wire [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    /* Power nets for gate-level netlist (inout must be connected to nets) */
    wire VPWR, VGND;
    assign VPWR = 1'b1;
    assign VGND = 1'b0;

    assign ui_in[0] = spi_miso;
    assign ui_in[6:1] = gpio_in;
    assign ui_in[7] = uart0_rx;

    assign uart0_tx = uo_out[0];
    assign error_flag = uo_out[1];
    assign i2c_scl_out = uo_out[2];
    assign spi_cs_n = uo_out[3];
    assign spi_sclk = uo_out[4];
    assign spi_mosi = uo_out[5];
    assign pwm_out[1:0] = uo_out[7:6];
    assign gpio_out = uo_out[7:2];

    assign flash_cs_n = uio_out[0];
    assign bus_io_out[1:0] = uio_out[2:1];
    assign bus_sclk = uio_out[3];
    assign bus_io_out[3:2] = uio_out[5:4];
    assign ram_cs_n = uio_out[6];
    assign gpio_io_out[0:0] = uio_out[7:7];

    assign uio_in[0] = 1'b0;
    assign uio_in[2:1] = bus_io_in_eff[1:0];
    assign uio_in[3] = 1'b0;
    assign uio_in[5:4] = bus_io_in_eff[3:2];
    assign uio_in[6] = 1'b0;
    assign uio_in[7] = i2c_ena ? i2c_sda_in : gpio_io_in[0];

    // Delay pipeline for QSPI input (pin-mux simulation); select by BOOT_MODE
    always @(posedge clk) begin
        if (!rst_n) begin
            bus_io_in_d1 <= 4'b0;
            bus_io_in_d2 <= 4'b0;
            bus_io_in_d3 <= 4'b0;
        end else begin
            bus_io_in_d1 <= bus_io_in;
            bus_io_in_d2 <= bus_io_in_d1;
            bus_io_in_d3 <= bus_io_in_d2;
        end
    end


    // I2C signal assignments
    // I2C SDA is on uio[4], SCL is on uio[5]
    // SDA is open-drain, so if oe is high(output), the signal is low,
    // and if oe is low (input), the signal is high-z
    assign i2c_sda_out = uio_oe[7] ? 1'b0 : 1'b1;

    `ifndef FLASH_BASE_ADDR  
    `define FLASH_BASE_ADDR 32'h00000000
    `endif

    `ifndef PSRAM_BASE_ADDR
    `define PSRAM_BASE_ADDR 32'h01000000
    `endif

    // Instantiate RTL SoC or gate-level netlist (IHP sg13g2)
    `ifdef GL_TEST
    tt_um_SotaSoC soc_inst (
        .clk(clk),
        .ena(1'b1),
        .rst_n(rst_n),
        .VPWR(VPWR),
        .VGND(VGND),
        .ui_in(ui_in),
        .uio_in(uio_in),
        .uio_oe(uio_oe),
        .uio_out(uio_out),
        .uo_out(uo_out)
    );
    `else
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
    `endif

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

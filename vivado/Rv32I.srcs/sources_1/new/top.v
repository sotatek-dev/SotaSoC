module top #(
    parameter GPIO_SIZE = 5
)(
    input clk_p,
    input clk_n,
    input rst_n,
    output flash_cs_n,
    output ram_cs_n,
    output spi_sclk,
    inout wire [3:0] spi_io,
    output uart_tx,
    input wire uart_rx,
    output wire [GPIO_SIZE-1:0] gpio_out,
    output wire error_flag
);

wire [3:0] spi_io_in;
wire [3:0] spi_io_out;
wire [3:0] spi_io_oe;

wire clk_200m;
wire clk;
IBUFDS #(
  .DIFF_TERM("FALSE"),       
  .IBUF_LOW_PWR("TRUE"),     
  .IOSTANDARD("DEFAULT")     
) IBUFDS_inst (
  .O(clk_200m), 
  .I(clk_p),  
  .IB(clk_n) 
);

clk_wiz_0 clk_ins(
   .clk_out100(clk),
   .clk_in1(clk_200m)
);

genvar i;
generate
    for (i = 0; i < 4; i = i + 1) begin : spi_buf
        IOBUF iobuf_inst (
            .I  (spi_io_out[i]),
            .O  (spi_io_in[i]),
            .IO (spi_io[i]),
            .T  (~spi_io_oe[i])
        );
    end
endgenerate

soc #(
    .CLK_HZ(20000000),
    .FLASH_SIZE(32'h00020000),
    .PSRAM_SIZE(32'h00020000)
) soc_ins(
    .clk(clk),
    .rst_n(rst_n),

    .flash_cs_n(flash_cs_n),
    .ram_cs_n(ram_cs_n),
    .spi_sclk(spi_sclk),
    .spi_io_in(spi_io_in),
    .spi_io_out(spi_io_out),
    .spi_io_oe(spi_io_oe),

    .uart_tx(uart_tx),
    .uart_rx(uart_rx),
    .gpio_out(gpio_out),
    
    .error_flag(error_flag)
);


endmodule
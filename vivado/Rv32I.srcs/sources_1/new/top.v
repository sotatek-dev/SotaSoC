module top #(
    parameter GPIO_SIZE = 5
)(
    input clk_p,
    input clk_n,
    input rst_n,
    output flash_cs_n,
    output ram_cs_n,
    output spi_sclk,
    output spi_mosi,
    input spi_miso,
    output uart_tx,
    input wire uart_rx,
    output wire [GPIO_SIZE-1:0] gpio_out
);

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
   .clk_out1(clk),
   .clk_in1(clk_200m)
);

soc #(
    .FLASH_SIZE(32'h00000080),
    .PSRAM_SIZE(32'h00000080)
) soc_ins(
    .clk(clk),
    .rst_n(rst_n),

    .flash_cs_n(flash_cs_n),
    .ram_cs_n(ram_cs_n),
    .spi_sclk(spi_sclk),
    .spi_mosi(spi_mosi),
    .spi_miso(spi_miso),

    .uart_tx(uart_tx),
    .uart_rx(uart_rx),
    .gpio_out(gpio_out)
);


endmodule
module top #(
)(
    input clk_p,
    input clk_n,
    input rst_n,
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    inout  wire [7:0] uio       // IOs
);

wire [7:0] uio_in;
wire [7:0] uio_out;
wire [7:0] uio_oe;

wire ena = 1'b1;

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
   .clk_out(clk),
   .clk_in1(clk_200m)
);

genvar i;
generate
    for (i = 0; i < 8; i = i + 1) begin : io_buf
        IOBUF iobuf_inst (
            .I  (uio_out[i]),
            .O  (uio_in[i]),
            .IO (uio[i]),
            .T  (~uio_oe[i])
        );
    end
endgenerate

soc #(
) soc_ins(
    .ui_in(ui_in),
    .uo_out(uo_out),
    .uio_in(uio_in),
    .uio_out(uio_out),
    .uio_oe(uio_oe),
    .ena(ena),
    .clk(clk),
    .rst_n(rst_n)
);


endmodule
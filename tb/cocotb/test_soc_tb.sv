/* RV32I SoC Testbench - cocotb wrapper */

module test_soc_tb;
    // Clock and reset
    reg clk;
    reg rst_n;
    
    // Shared SPI interface
    wire flash_cs_n;
    wire ram_cs_n;
    wire spi_sclk;
    wire spi_mosi;
    reg spi_miso;
    
    // Debug interface
    wire [31:0] debug_pc;
    wire [31:0] debug_instr;
    wire [15:0] debug_reg_addr;
    wire [31:0] debug_reg_data;
    wire debug_reg_we;
    
    // Instantiate the SoC
    soc#(
        .RESET_ADDR(32'h00000000)
    ) soc_inst (
        .clk(clk),
        .rst_n(rst_n),
        .flash_cs_n(flash_cs_n),
        .ram_cs_n(ram_cs_n),
        .spi_sclk(spi_sclk),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .debug_pc(debug_pc),
        .debug_instr(debug_instr),
        .debug_reg_addr(debug_reg_addr),
        .debug_reg_data(debug_reg_data),
        .debug_reg_we(debug_reg_we)
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
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("vcd/test_soc_tb.vcd");
        $dumpvars(0, test_soc_tb);
    end
    `endif

endmodule

/* RV32I SoC Testbench - cocotb wrapper */

module test_soc_tb;
    // Clock and reset
    reg clk;
    reg rst_n;
    
    // Shared SPI interface
    wire flash_cs_n;
    wire ram_cs_n;
    wire spi_sclk;
    reg [3:0] spi_io_in;
    wire [3:0] spi_io_out;
    wire error_flag;
    
    // Define default values if not provided
    `ifndef CLK_HZ
    `define CLK_HZ 10000000
    `endif
    
    `ifndef FLASH_BASE_ADDR  
    `define FLASH_BASE_ADDR 32'h00000000
    `endif
    
    `ifndef PSRAM_BASE_ADDR
    `define PSRAM_BASE_ADDR 32'h01000000
    `endif
    
    // Instantiate the SoC
    soc#(
        .CLK_HZ(`CLK_HZ),
        .RESET_ADDR(32'h00000000),
        .FLASH_BASE_ADDR(`FLASH_BASE_ADDR),
        .PSRAM_BASE_ADDR(`PSRAM_BASE_ADDR)
    ) soc_inst (
        .clk(clk),
        .rst_n(rst_n),
        .flash_cs_n(flash_cs_n),
        .ram_cs_n(ram_cs_n),
        .spi_sclk(spi_sclk),
        .spi_io_in(spi_io_in),
        .spi_io_out(spi_io_out),
        .error_flag(error_flag)
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

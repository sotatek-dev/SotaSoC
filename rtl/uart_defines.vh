`ifndef UART_DEFINES_VH
`define UART_DEFINES_VH

// UART Register Write Macros
`define UART_WRITE_TX_DATA(wdata) \
    begin \
        uart_tx_data_reg <= wdata[7:0]; \
        $display("Time %0t: UART_MEM - TX Data Write: data=0x%02h (%c)", \
                 $time, wdata[7:0], wdata[7:0]); \
    end

`define UART_WRITE_CONTROL(wdata) \
    begin \
        uart_tx_en_reg <= wdata[1]; \
        $display("Time %0t: UART_MEM - Control Write: ctrl=0x%08h", \
                 $time, wdata); \
    end

`define UART_WRITE_RX_DATA_IGNORED(wdata) \
    begin \
        $display("Time %0t: UART_MEM - RX Data Write: ignored", $time); \
    end

`define UART_WRITE_RX_CONTROL(wdata) \
    begin \
        uart_rx_valid_reg <= wdata[0]; \
        uart_rx_en_reg <= wdata[1]; \
        uart_rx_break_reg <= wdata[2]; \
        $display("Time %0t: UART_MEM - RX Control Write: ctrl=0x%08h", \
                 $time, wdata); \
    end

`define UART_WRITE_RESERVED(addr, wdata) \
    begin \
        $display("Time %0t: UART_MEM - Reserved register write: addr=0x%08h, data=0x%08h", \
                 $time, addr, wdata); \
    end

// UART Register Read Macros
`define UART_READ_TX_DATA(rdata) \
    begin \
        rdata <= 32'h00000000; \
        $display("Time %0t: UART_MEM - TX Data Read (write-only): data=0x00000000", $time); \
    end

`define UART_READ_CONTROL(rdata) \
    begin \
        rdata <= {31'b0, uart_tx_busy}; \
        $display("Time %0t: UART_MEM - Control Read: ctrl=0x%08h, busy=%b", \
                 $time, {31'b0, uart_tx_busy}, uart_tx_busy); \
    end

`define UART_READ_RX_DATA(rdata) \
    begin \
        rdata <= {24'b0, uart_rx_data}; \
        $display("Time %0t: UART_MEM - RX Data Read: data=0x%08h", \
                 $time, {24'b0, uart_rx_data}); \
    end

`define UART_READ_RX_CONTROL(rdata) \
    begin \
        rdata <= {29'b0, uart_rx_break_reg, uart_rx_en_reg, uart_rx_valid_reg}; \
        $display("Time %0t: UART_MEM - RX Control Read: ctrl=0x%08h", \
                 $time, {29'b0, uart_rx_break_reg, uart_rx_en_reg, uart_rx_valid_reg}); \
    end

`define UART_READ_RESERVED(rdata, addr) \
    begin \
        rdata <= 32'h00000000; \
        $display("Time %0t: UART_MEM - Reserved register read: addr=0x%08h, data=0x00000000", \
                 $time, addr); \
    end

`endif // UART_DEFINES_VH
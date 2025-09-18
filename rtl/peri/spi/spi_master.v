module spi_master (
    input wire clk,
    input wire rst_n,
    
    // CPU interface
    input wire start,                    // Start SPI transaction
    input wire write_enable,             // 1 = write operation, 0 = read operation
    input wire [31:0] cmd_addr,          // 32-bit input: [31:24] command, [23:0] address
    input wire [5:0] data_len,           // 5-bit input: data length (0-31)
    input wire [31:0] data_in,           // 32-bit data input for write operations
    output reg [31:0] data_out,          // 32-bit data output
    output reg done,                     // Transaction complete
    
    // SPI interface
    output reg spi_clk,                  // SPI clock
    output reg spi_cs_n,                 // SPI chip select (active low)
    output reg spi_mosi,                 // SPI Master Out Slave In
    input wire spi_miso                  // SPI Master In Slave Out
);

    // Parameters
    parameter CLK_DIV = 4;               // Clock divider for SPI clock (system_clk / CLK_DIV)
    parameter FSM_IDLE = 3'b000;
    parameter FSM_INIT = 3'b001;
    parameter FSM_SEND_CMD_ADDR = 3'b010;
    parameter FSM_DATA_TRANSFER = 3'b011;
    parameter FSM_DONE_STATE = 3'b100;

    localparam INIT_CYCLES = 12'd4095;

    // Internal signals
    reg [2:0] fsm_state;
    reg [2:0] fsm_next_state;
    reg [7:0] bit_counter;
    reg [7:0] byte_counter;
    reg [31:0] shift_reg_out;
    reg [31:0] shift_reg_in;
    reg [7:0] clk_counter;
    reg spi_clk_en;
    reg is_write_op;

    reg write_mosi;

    reg initialized = 1'b0;
    reg [11:0] init_cnt = 12'b0;
    
    // Clock generation for SPI
    // always @(posedge clk or negedge rst_n) begin
    //     if (!rst_n) begin
    //         clk_counter <= 8'b0;
    //         spi_clk <= 1'b0;
    //     end else if (spi_clk_en) begin
    //         if (clk_counter == (CLK_DIV/2 - 1)) begin
    //             clk_counter <= 8'b0;
    //             spi_clk <= ~spi_clk;
    //         end else begin
    //             clk_counter <= clk_counter + 1;
    //         end
    //     end else begin
    //         clk_counter <= 8'b0;
    //         spi_clk <= 1'b0;
    //     end
    // end

    // assign spi_clk = (spi_clk_en) ? clk : 1'b0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            spi_clk <= 1'b0;
        end else if (spi_clk_en) begin
            spi_clk <= ~spi_clk;
        end else begin
            spi_clk <= 1'b0;
        end
    end

    // State machine
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fsm_state <= FSM_IDLE;
        end else begin
            fsm_state <= fsm_next_state;
        end
    end

    // Next fsm_state logic
    always @(*) begin
        case (fsm_state)
            FSM_IDLE: begin
                if (start) begin
                    if (initialized) begin
                        fsm_next_state = FSM_SEND_CMD_ADDR;
                        $display("Time %0t: SPI_MASTER - Starting SPI transaction: cmd_addr=0x%h", $time, cmd_addr);
                    end else begin
                        fsm_next_state = FSM_INIT;
                        $display("Time %0t: SPI_MASTER - Initializing SPI", $time);
                    end
                end else begin
                    fsm_next_state = FSM_IDLE;
                end
            end

            FSM_INIT: begin
                if (initialized) begin
                    fsm_next_state = FSM_SEND_CMD_ADDR;
                end else begin
                    fsm_next_state = FSM_INIT;
                end
            end
            
            FSM_SEND_CMD_ADDR: begin
                if (bit_counter == 32/* && spi_clk == 1'b0*/)
                    fsm_next_state = FSM_DATA_TRANSFER;
                else
                    fsm_next_state = FSM_SEND_CMD_ADDR;
             end
             
            FSM_DATA_TRANSFER: begin
                if (bit_counter == data_len/* && spi_clk == 1'b0*/)
                    fsm_next_state = FSM_DONE_STATE;
                else
                    fsm_next_state = FSM_DATA_TRANSFER;
             end
            
            FSM_DONE_STATE: begin
                fsm_next_state = FSM_IDLE;
            end
            
            default: fsm_next_state = FSM_IDLE;
        endcase
    end

    // Control signals and data handling
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            done <= 1'b0;
            spi_cs_n <= 1'b1;
            spi_mosi <= 1'b0;
            spi_clk_en <= 1'b0;
            bit_counter <= 8'b0;
            byte_counter <= 8'b0;
            shift_reg_out <= 32'b0;
            shift_reg_in <= 32'b0;
            data_out <= 32'b0;
            is_write_op <= 1'b0;

            write_mosi <= 1'b0;
        end else begin
            // $display("Time %0t: SPI_MASTER - fsm_state=%d, bit_counter=%d, spi_clk=%b, spi_mosi=%b, spi_miso=%b", $time, fsm_state, bit_counter, spi_clk, spi_mosi, spi_miso);
            case (fsm_state)
                FSM_IDLE: begin
                    done <= 1'b0;
                    spi_cs_n <= 1'b1;
                    spi_mosi <= 1'b0;
                    spi_clk_en <= 1'b0;
                    bit_counter <= 8'b0;
                    byte_counter <= 8'b0;
                    write_mosi <= 1'b0;
                    
                    if (start) begin
                        if (initialized) begin
                            spi_cs_n <= 1'b0;
                            shift_reg_out <= cmd_addr;  // Load command and address
                            shift_reg_in <= 32'b0;
                            is_write_op <= write_enable; // Store operation type

                            write_mosi <= 1'b1;
                        end else begin
                        end
                    end
                end

                FSM_INIT: begin
                    init_cnt <= init_cnt + 1;
                    if (init_cnt == INIT_CYCLES) begin
                        initialized <= 1'b1;
                        spi_cs_n <= 1'b0;
                        shift_reg_out <= cmd_addr;  // Load command and address
                        shift_reg_in <= 32'b0;
                        is_write_op <= write_enable; // Store operation type

                        write_mosi <= 1'b1;
                    end
                end
                
                FSM_SEND_CMD_ADDR: begin
                    spi_clk_en <= 1'b1;
                    spi_cs_n <= 1'b0;
                    if (write_mosi == 1'b1) begin  // Falling edge of SPI clock
                        spi_mosi <= shift_reg_out[31];
                        shift_reg_out <= {shift_reg_out[30:0], 1'b0};
                        bit_counter <= bit_counter + 1;
                        
                    end
                    // When command+address phase is done, prepare for data phase
                    if (bit_counter == 32) begin
                        if (is_write_op) begin
                            shift_reg_out <= data_in;  // Load write data for next phase
                        end else begin
                            shift_reg_out <= 32'b0;   // Clear for read phase
                        end
                        bit_counter <= 8'b0;  // Reset counter for data phase
                    end

                    write_mosi <= ~write_mosi;
                end

                FSM_DATA_TRANSFER: begin
                    spi_cs_n <= 1'b0;
                    if (is_write_op) begin
                        // Write operation: send data
                        if (write_mosi == 1'b1) begin  // Falling edge of SPI clock
                            spi_mosi <= shift_reg_out[31];
                            shift_reg_out <= {shift_reg_out[30:0], 1'b0};
                            bit_counter <= bit_counter + 1;
                        end
                    end else begin
                        // Read operation: receive data
                        spi_mosi <= 1'b0;  // Don't drive MOSI during read
                        
                        if (spi_clk == 1'b0) begin  // Rising edge - sample MISO
                            shift_reg_in <= {shift_reg_in[30:0], spi_miso};
                            bit_counter <= bit_counter + 1;
                        end
                    end

                    write_mosi <= ~write_mosi;
                end
                
                FSM_DONE_STATE: begin
                    done <= 1'b1;
                    spi_cs_n <= 1'b1;
                    spi_clk_en <= 1'b0;
                    bit_counter <= 8'b0;
                    spi_mosi <= 1'b0;
                    
                    // For read operations, output the received data
                    // For write operations, data_out can be used for status/acknowledgment
                    if (!is_write_op) begin
                        data_out <= shift_reg_in;  // Output the received data
                    end else begin
                        data_out <= 32'h00000000;  // Write confirmation or status
                    end
                end
            endcase
        end
    end

endmodule

module spi_master (
    input wire clk,
    input wire rst_n,
    
    // CPU interface
    input wire start,                    // Start QSPI transaction
    input wire stop,                     // Stop QSPI transaction
    input wire write_enable,             // 1 = write operation, 0 = read operation
    input wire is_instr,                 // 1 = instruction, 0 = data
    input wire [23:0] addr,              // 24-bit input: address
    input wire [5:0] data_len,           // 6-bit input: data length in bits (0-63)
    input wire [31:0] data_in,           // 32-bit data input for write operations
    output reg [31:0] data_out,          // 32-bit data output
    output reg done,                     // Transaction complete
    
    // QSPI interface (4-bit mode only)
    output reg spi_clk,                  // QSPI clock
    output reg spi_cs_n,                 // QSPI chip select (active low)
    input wire [3:0] spi_io_in,          // QSPI IO input (IO0, IO1, IO2, IO3)
    output reg [3:0] spi_io_out,         // QSPI IO output (IO0, IO1, IO2, IO3)
    output reg [3:0] spi_io_oe           // Output enable for each IO line (1=output, 0=input)
);

    // Parameters
    parameter FSM_IDLE = 4'b0000;
    parameter FSM_INIT = 4'b0001;
    parameter FSM_SEND_CMD = 4'b0010;
    parameter FSM_SEND_CMD_QUAD = 4'b0011;
    parameter FSM_SEND_ADDR = 4'b0100;
    parameter FSM_DUMMY = 4'b0101;
    parameter FSM_DATA_TRANSFER = 4'b0110;
    parameter FSM_DONE = 4'b0111;

    parameter FSM_RESET_FLASH0 = 4'b1000;
    parameter FSM_RESET_FLASH1 = 4'b1001;
    parameter FSM_RESET_FLASH2 = 4'b1010;
    parameter FSM_RESET_FLASH3 = 4'b1011;
    parameter FSM_RESET_FLASH4 = 4'b1100;

    parameter FSM_RESET_RAM0 = 4'b1101;
    parameter FSM_RESET_RAM1 = 4'b1110;
    parameter FSM_RESET_RAM2 = 4'b1111;

    localparam INIT_CYCLES = 12'd4095;

    // Internal signals
    reg [3:0] fsm_state;
    reg [3:0] fsm_next_state;
    reg [5:0] bit_counter;               // Counts bits transferred
    reg [31:0] shift_reg_out;
    reg [31:0] shift_reg_in;
    reg spi_clk_en;
    reg is_write_op;

    reg write_mosi;

    reg initialized;
    reg [11:0] init_cnt;

    reg flash_in_cont_mode;
    reg ram_in_quad_mode;

    // We send quad command by bit counter index, so LSB is the first bit
    wire[0:7] cmd_enter_quad_mode = 8'h35;

    wire [7:0] cmd = write_enable ? 8'h38 : 8'hEB;
    wire [31:0] cmd_addr = {cmd, addr};

    // These conditions are checked right before receiving the last 4 bits of the instruction
    wire is_compressed_instr = (bit_counter == 12) && (shift_reg_in[5:4] != 2'b11);
    wire is_normal_instr = (bit_counter == 28);
    wire is_instr_complete = is_instr && (fsm_state == FSM_DATA_TRANSFER) && (is_compressed_instr || is_normal_instr);

    // State machine
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fsm_state <= FSM_IDLE;
        end else begin
            fsm_state <= fsm_next_state;
        end
    end

    // Next state logic
    always @(*) begin
        case (fsm_state)
            FSM_IDLE: begin
                if (start) begin
                    if (initialized) begin
                        if (is_instr) begin
                            if (flash_in_cont_mode) begin
                                fsm_next_state = FSM_SEND_ADDR;
                            end else begin
                                // This case should not happen
                                // Flash shoule be in continuous mode after initialization
                                fsm_next_state = FSM_SEND_CMD;
                            end
                        end else begin
                            if (ram_in_quad_mode) begin
                                fsm_next_state = FSM_SEND_CMD_QUAD;
                            end else begin
                                fsm_next_state = FSM_RESET_RAM0;
                            end
                            // fsm_next_state = FSM_SEND_CMD;
                        end
//                        `DEBUG_PRINT(("Time %0t: SPI_MASTER - Starting SPI transaction: cmd_addr=0x%h", $time, cmd_addr));
                    end else begin
                        fsm_next_state = FSM_INIT;
//                        `DEBUG_PRINT(("Time %0t: QSPI_MASTER - Initializing QSPI", $time));
                    end
                end else begin
                    fsm_next_state = FSM_IDLE;
                end
            end

            FSM_INIT: begin
                if (init_cnt == INIT_CYCLES) begin
                    fsm_next_state = FSM_RESET_FLASH0;
                end else begin
                    fsm_next_state = FSM_INIT;
                end
            end

            FSM_RESET_FLASH0: begin
                fsm_next_state = FSM_RESET_FLASH1;
            end

            FSM_RESET_FLASH1: begin
                if (bit_counter == 7)
                    fsm_next_state = FSM_RESET_FLASH2;
                else
                    fsm_next_state = FSM_RESET_FLASH1;
            end

            FSM_RESET_FLASH2: begin
                if (bit_counter == 13)
                    fsm_next_state = FSM_RESET_FLASH3;
                else
                    fsm_next_state = FSM_RESET_FLASH2;
            end

            FSM_RESET_FLASH3: begin
                fsm_next_state = FSM_RESET_FLASH4;
            end

            FSM_RESET_FLASH4: begin
                fsm_next_state = FSM_SEND_CMD;
            end

            FSM_RESET_RAM0: begin
                fsm_next_state = FSM_RESET_RAM1;
            end

            FSM_RESET_RAM1: begin
                if (bit_counter == 9)
                    fsm_next_state = FSM_RESET_RAM2;
                else
                    fsm_next_state = FSM_RESET_RAM1;
            end

            FSM_RESET_RAM2: begin
                fsm_next_state = FSM_SEND_CMD_QUAD;
            end

            FSM_SEND_CMD: begin
                if (bit_counter == 8)
                    fsm_next_state = FSM_SEND_ADDR;
                else
                    fsm_next_state = FSM_SEND_CMD;
            end

            FSM_SEND_CMD_QUAD: begin
                if (bit_counter == 8)
                    fsm_next_state = FSM_SEND_ADDR;
                else
                    fsm_next_state = FSM_SEND_CMD_QUAD;
            end

            FSM_SEND_ADDR: begin
                if (bit_counter == 24)
                    if (write_enable) begin
                        fsm_next_state = FSM_DATA_TRANSFER;
                    end else begin
                        fsm_next_state = FSM_DUMMY;
                    end
                else
                    fsm_next_state = FSM_SEND_ADDR;
            end

            FSM_DUMMY: begin
                if (bit_counter == 6)
                    fsm_next_state = FSM_DATA_TRANSFER;
                else
                    fsm_next_state = FSM_DUMMY;
            end

            FSM_DATA_TRANSFER: begin
                if (is_instr) begin
                    fsm_next_state = FSM_DATA_TRANSFER;
                end else begin
                    if (bit_counter == data_len) begin
                        fsm_next_state = FSM_DONE;
                    end else begin
                        fsm_next_state = FSM_DATA_TRANSFER;
                    end
                end
            end

            FSM_DONE: begin
                fsm_next_state = FSM_IDLE;
            end

            default: fsm_next_state = FSM_IDLE;
        endcase

        if (stop) begin // force stop QSPI transaction no matter what state we are in
            fsm_next_state = FSM_IDLE;
        end
    end

    // Control signals and data handling
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            spi_clk <= 1'b0;

            done <= 1'b0;
            spi_cs_n <= 1'b1;
            spi_io_oe <= 4'b0000;
            spi_io_out <= 4'b0000;
            spi_clk_en <= 1'b0;
            bit_counter <= 6'b0;
            shift_reg_out <= 32'b0;
            shift_reg_in <= 32'b0;
            data_out <= 32'b0;
            is_write_op <= 1'b0;

            write_mosi <= 1'b0;

            initialized <= 1'b0;
            init_cnt <= 12'b0;

            flash_in_cont_mode <= 1'b0;
            ram_in_quad_mode <= 1'b0;
        end else begin

            if (spi_clk_en) begin
                spi_clk <= ~spi_clk;
            end else begin
                spi_clk <= 1'b0;
            end

            case (fsm_state)
                FSM_IDLE: begin
                    done <= 1'b0;
                    spi_cs_n <= 1'b1;
                    spi_io_oe <= 4'b0000;
                    spi_io_out <= 4'b0000;
                    spi_clk_en <= 1'b0;
                    bit_counter <= 6'b0;
                    write_mosi <= 1'b0;
                    
                    if (start) begin
                        if (initialized) begin
                            spi_cs_n <= 1'b0;
                            spi_io_oe <= 4'b1111;       // All IOs are outputs for command/address
                            if (is_instr) begin
                                // In this case, the flash should already be in continuous mode
                                shift_reg_out <= {addr, 8'h00};   // Load address
                            end else begin
                                shift_reg_out <= cmd_addr;   // Load command and address
                            end
                            shift_reg_in <= 32'b0;
                            is_write_op <= write_enable; // Store operation type

                            write_mosi <= 1'b1;
                        end else begin
                        end
                    end
                end

                FSM_INIT: begin
                    init_cnt <= init_cnt + 1;
                end

                FSM_RESET_FLASH0: begin
                    // Start reset transaction
                    spi_cs_n <= 1'b0;
                    spi_io_oe <= 4'b1111;       // All IOs are outputs
                    spi_io_out <= 4'b0000;
                    spi_clk_en <= 1'b0;

                    write_mosi <= 1'b1;
                end

                FSM_RESET_FLASH1: begin
                    // Send 8 0x0 nibbles to make sure flash quit continuous mode
                    // If flash is not in continuous mode, it receives the 0x00 command => do nothing
                    // If flash is in continuous mode, it receives the 0x000000 address
                    // and 0x00 for M[7:0] => quit continuous mode
                    spi_cs_n <= 1'b0;
                    spi_clk_en <= 1'b1;

                    spi_io_oe <= 4'b1111;       // All IOs are outputs
                    spi_io_out <= 4'b0000;

                    if (write_mosi == 1'b1) begin
                        bit_counter <= bit_counter + 1;
                    end
                    write_mosi <= ~write_mosi;
                end

                FSM_RESET_FLASH2: begin
                    // Release bus and wait for some cycles
                    spi_cs_n <= 1'b0;
                    spi_clk_en <= 1'b1;
                    spi_io_oe <= 4'b0000;       // Release bus

                    if (write_mosi == 1'b1) begin
                        bit_counter <= bit_counter + 1;
                    end
                    write_mosi <= ~write_mosi;
                end

                FSM_RESET_FLASH3: begin
                    // Finish reset transaction
                    initialized <= 1'b1;
                    spi_cs_n <= 1'b1;
                    spi_clk_en <= 1'b0;
                end

                FSM_RESET_FLASH4: begin
                    // Prepare for fetch instruction
                    spi_cs_n <= 1'b0;
                    spi_io_oe <= 4'b1111;       // All IOs are outputs for command/address
                    // Fetch instruction for first time, need both command and address
                    shift_reg_out <= cmd_addr;
                    shift_reg_in <= 32'b0;
                    is_write_op <= write_enable; // Store operation type

                    spi_clk_en <= 1'b0;
                    bit_counter <= 6'b0;
                    spi_io_out <= 4'b0000;

                    write_mosi <= 1'b1;
                end

                FSM_RESET_RAM0: begin
                    // Start reset transaction
                    spi_cs_n <= 1'b0;
                    spi_io_oe <= 4'b1111;       // All IOs are outputs
                    spi_io_out <= 4'b0000;
                    spi_clk_en <= 1'b0;
                    bit_counter <= 0;

                    write_mosi <= 1'b1;
                end

                FSM_RESET_RAM1: begin
                    if (bit_counter == 9) begin
                        // Wait for 2 cycles to make sure clk is low before starting new transaction
                        spi_cs_n <= 1'b1;
                        spi_clk_en <= 1'b0;
                        spi_io_out <= 4'b0000;
                        ram_in_quad_mode <= 1'b1;
                    end else begin
                        // Send command to enter quad mode
                        spi_cs_n <= 1'b0;
                        spi_clk_en <= 1'b1;
                        if (write_mosi == 1'b1) begin  // Falling edge of SPI clock
                            if (bit_counter == 8) begin
                                spi_cs_n <= 1'b1;
                                spi_clk_en <= 1'b0;
                                spi_io_out <= 4'b0000;
                            end else begin
                                // If the RAM is not in quad mode, it will receive the command of 0x35
                                // If the RAM is in quad mode, it will receive the command of 0x00 => do nothing
                                spi_io_out <= {4{cmd_enter_quad_mode[bit_counter]}};
                            end
                            bit_counter <= bit_counter + 1;
                        end

                        write_mosi <= ~write_mosi;
                    end
                end

                FSM_RESET_RAM2: begin
                    // Prepare for fetch instruction
                    spi_cs_n <= 1'b0;
                    spi_io_oe <= 4'b1111;       // All IOs are outputs for command/address
                    // Fetch instruction for first time, need both command and address
                    shift_reg_out <= cmd_addr;
                    shift_reg_in <= 32'b0;
                    is_write_op <= write_enable; // Store operation type

                    spi_clk_en <= 1'b0;
                    bit_counter <= 6'b0;
                    spi_io_out <= 4'b0000;

                    write_mosi <= 1'b1;
                end

                FSM_SEND_CMD: begin
                    spi_clk_en <= 1'b1;
                    spi_cs_n <= 1'b0;
                    if (write_mosi == 1'b1) begin  // Falling edge of SPI clock
                        spi_io_out <= {3'b0, shift_reg_out[31]};
                        shift_reg_out <= {shift_reg_out[30:0], 1'b0};
                        bit_counter <= bit_counter + 1;
                    end

                    if (bit_counter == 8) begin
                        bit_counter <= 6'b0;  // Reset counter for data phase
                    end

                    write_mosi <= ~write_mosi;
                end

                FSM_SEND_CMD_QUAD: begin
                    spi_clk_en <= 1'b1;
                    spi_cs_n <= 1'b0;
                    if (write_mosi == 1'b1) begin  // Falling edge of SPI clock
                        spi_io_out <= shift_reg_out[31:28];
                        shift_reg_out <= {shift_reg_out[27:0], 4'b0000};
                        bit_counter <= bit_counter + 4;
                    end

                    if (bit_counter == 8) begin
                        bit_counter <= 6'b0;  // Reset counter for data phase
                    end

                    write_mosi <= ~write_mosi;
                end

                FSM_SEND_ADDR: begin
                    spi_clk_en <= 1'b1;
                    spi_cs_n <= 1'b0;
                    if (write_mosi == 1'b1) begin  // Falling edge of SPI clock
                        spi_io_out <= shift_reg_out[31:28];
                        shift_reg_out <= {shift_reg_out[27:0], 4'b0000};
                        bit_counter <= bit_counter + 4;
                        
                    end
                    // When address phase is done, prepare for data phase
                    if (bit_counter == 24) begin
                        if (is_write_op) begin
                            shift_reg_out <= data_in;  // Load write data for next phase
                        end else begin
                            shift_reg_out <= 32'b0;    // Clear for read phase
                        end
                        bit_counter <= 6'b0;  // Reset counter for data phase
                    end

                    write_mosi <= ~write_mosi;
                end

                FSM_DUMMY: begin
                    if (write_mosi == 1'b1) begin
                        if (bit_counter == 0) begin
                            spi_io_oe <= 4'b1111;      // IOs become outputs for write M7-M0
                            spi_io_out <= 4'hA;        // Send 4'hA to enter continuous mode
                        end else begin
                            spi_io_oe <= 4'b0000;      // IOs become inputs for read
                            spi_io_out <= 4'h0;        // Clear for read phase
                        end

                        bit_counter <= bit_counter + 1;
                    end

                    if (bit_counter == 6) begin
                        bit_counter <= 6'b0;
                        flash_in_cont_mode <= 1'b1;
                    end

                    write_mosi <= ~write_mosi;
                end

                FSM_DATA_TRANSFER: begin
                    done <= 1'b0;
                    spi_clk_en <= 1'b1;
                    spi_cs_n <= 1'b0;
                    if (is_write_op) begin
                        // Write operation: send data
                        spi_io_oe <= 4'b1111;       // All IOs are outputs
                        if (write_mosi == 1'b1) begin  // Falling edge of SPI clock
                            spi_io_out <= shift_reg_out[31:28];
                            shift_reg_out <= {shift_reg_out[27:0], 4'b0000};
                            bit_counter <= bit_counter + 4;
                        end
                    end else begin
                        // Read operation: receive data
                        spi_io_oe <= 4'b0000;       // All IOs are inputs
                        spi_io_out <= 4'b0000;      // Don't drive outputs
                        
                        if (spi_clk == 1'b0) begin  // Rising edge - sample input
                            if (is_instr_complete) begin
                            // In case of fetch instruction, we update flag and data here to save one clock cycle
                                bit_counter <= 6'b0;
                                done <= 1'b1;
                                if (bit_counter == 12) begin
                                    data_out <= {shift_reg_in[11:0], spi_io_in, 16'b0};
                                end else begin
                                    data_out <= {shift_reg_in[27:0], spi_io_in};
                                end
                            end else begin
                                shift_reg_in <= {shift_reg_in[27:0], spi_io_in};  // Shift in 4 bits
                                bit_counter <= bit_counter + 4;
                            end
                        end
                    end

                    write_mosi <= ~write_mosi;
                end

                FSM_DONE: begin
                    done <= 1'b1;
                    spi_cs_n <= 1'b1;
                    spi_clk_en <= 1'b0;
                    bit_counter <= 6'b0;
                    spi_io_oe <= 4'b0000;
                    spi_io_out <= 4'b0000;
                    
                    // For read operations, output the received data
                    // For write operations, data_out can be used for status/acknowledgment
                    if (!is_write_op) begin
                        data_out <= shift_reg_in;  // Output the received data
                    end else begin
                        data_out <= 32'h00000000;  // Write confirmation or status
                    end
                end

                default: ;
            endcase

            if (stop) begin // force stop QSPI transaction no matter what state we are in
                spi_cs_n <= 1'b1;
                spi_clk_en <= 1'b0;
                spi_io_oe <= 4'b0000;
            end
        end
    end

endmodule


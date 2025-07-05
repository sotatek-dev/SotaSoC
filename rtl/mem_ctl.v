/* Memory Controller for RV32I SoC
 * 
 * This controller handles:
 * - Instruction fetch from SPI Flash 
 * - Data memory operations to SPI RAM
 * - Address mapping and SPI protocol handling
 * 
 * Memory Map:
 * 0x80000000 - 0x8FFFFFFF: Flash (Instructions)
 * 0x00000000 - 0x0FFFFFFF: RAM (Data)
 */

module mem_ctl (
    input wire clk,
    input wire rst_n,
    
    // Core interface
    input wire [31:0] instr_addr,
    output reg [31:0] instr_data,
    output reg instr_ready,
    
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire [2:0] mem_wflag,    // funct3 from store instruction: 000=SB, 001=SH, 010=SW
    input wire mem_we,
    input wire mem_re,
    output reg [31:0] mem_rdata,
    output reg mem_ready,
    
    // Shared SPI interface
    output reg flash_cs_n,
    output reg ram_cs_n,
    output reg spi_sclk,
    output reg spi_mosi,
    input wire spi_miso
);

    // State machine states
    localparam IDLE = 3'b000;
    localparam SPI_CMD = 3'b001;
    localparam SPI_ADDR = 3'b010;
    localparam SPI_DATA = 3'b011;
    localparam DONE = 3'b111;

    reg [2:0] state, next_state;
    reg [2:0] spi_state;
    reg [5:0] bit_counter;
    reg [7:0] command;
    reg [23:0] address;
    reg [31:0] data_buffer;
    reg [31:0] write_data;
    reg is_write_op;
    reg flash_active;
    reg ram_active;
    
    // SPI Flash commands
    localparam FLASH_READ_CMD = 8'h03;  // Read command
    
    // SPI RAM commands  
    localparam RAM_READ_CMD = 8'h03;    // Read command
    localparam RAM_WRITE_CMD = 8'h02;   // Write command
    
    // Address mapping
    wire is_flash_addr = (instr_addr[31:28] == 4'h8);  // 0x8xxxxxxx
    wire is_ram_addr = (mem_addr[31:28] == 4'h0);      // 0x0xxxxxxx
    
    // Convert to 24-bit addresses for SPI devices
    wire [23:0] flash_addr_24 = instr_addr[23:0];
    wire [23:0] ram_addr_24 = mem_addr[23:0];
    
    // State machine
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            flash_cs_n <= 1'b1;
            ram_cs_n <= 1'b1;
            spi_sclk <= 1'b0;
            spi_mosi <= 1'b0;
            instr_ready <= 1'b0;
            mem_ready <= 1'b0;
            instr_data <= 32'h0;
            mem_rdata <= 32'h0;
            bit_counter <= 6'b0;
            data_buffer <= 32'h0;
            flash_active <= 1'b0;
            ram_active <= 1'b0;
        end else begin
            state <= next_state;
            
            case (state)
                IDLE: begin
                    instr_ready <= 1'b0;
                    mem_ready <= 1'b0;
                    flash_cs_n <= 1'b1;
                    ram_cs_n <= 1'b1;
                    spi_sclk <= 1'b0;
                    bit_counter <= 6'b0;
                    
                    // Check for instruction fetch request
                    if (is_flash_addr && !instr_ready) begin
                        flash_active <= 1'b1;
                        ram_active <= 1'b0;
                        command <= FLASH_READ_CMD;
                        address <= flash_addr_24;
                        is_write_op <= 1'b0;
                        flash_cs_n <= 1'b0;
                    end
                    // Check for data memory request
                    else if (is_ram_addr && (mem_we || mem_re) && !mem_ready) begin
                        flash_active <= 1'b0;
                        ram_active <= 1'b1;
                        command <= mem_we ? RAM_WRITE_CMD : RAM_READ_CMD;
                        address <= ram_addr_24;
                        write_data <= mem_wdata;
                        is_write_op <= mem_we;
                        ram_cs_n <= 1'b0;
                    end
                end
                
                SPI_CMD: begin
                    if (flash_active || ram_active) begin
                        spi_sclk <= ~spi_sclk;
                        if (spi_sclk) begin  // Rising edge - setup data
                            spi_mosi <= command[7 - bit_counter[2:0]];
                        end else begin  // Falling edge - increment counter
                            if (bit_counter[2:0] == 3'b111) begin
                                bit_counter <= 6'b0;
                            end else begin
                                bit_counter <= bit_counter + 1;
                            end
                        end
                    end
                end
                
                SPI_ADDR: begin
                    if (flash_active || ram_active) begin
                        spi_sclk <= ~spi_sclk;
                        if (spi_sclk) begin  // Rising edge - setup data
                            spi_mosi <= address[23 - bit_counter[4:0]];
                        end else begin  // Falling edge - increment counter
                            if (bit_counter[4:0] == 5'b10111) begin  // 24 bits sent
                                bit_counter <= 6'b0;
                            end else begin
                                bit_counter <= bit_counter + 1;
                            end
                        end
                    end
                end
                
                SPI_DATA: begin
                    if (flash_active || ram_active) begin
                        spi_sclk <= ~spi_sclk;
                        if (is_write_op) begin
                            // Write operation (RAM only)
                            if (spi_sclk) begin  // Rising edge - setup data
                                spi_mosi <= write_data[31 - bit_counter[4:0]];
                            end else begin  // Falling edge - increment counter
                                if (bit_counter[4:0] == 5'b11111) begin  // 32 bits sent
                                    mem_ready <= 1'b1;
                                    bit_counter <= 6'b0;
                                end else begin
                                    bit_counter <= bit_counter + 1;
                                end
                            end
                        end else begin
                            // Read operation (Flash or RAM)
                            if (~spi_sclk) begin  // Falling edge - sample data
                                data_buffer <= {data_buffer[30:0], spi_miso};
                                if (bit_counter[4:0] == 5'b11111) begin  // 32 bits received
                                    if (flash_active) begin
                                        instr_data <= {data_buffer[30:0], spi_miso};
                                        instr_ready <= 1'b1;
                                    end else begin
                                        mem_rdata <= {data_buffer[30:0], spi_miso};
                                        mem_ready <= 1'b1;
                                    end
                                    bit_counter <= 6'b0;
                                end else begin
                                    bit_counter <= bit_counter + 1;
                                end
                            end
                        end
                    end
                end
                
                DONE: begin
                    flash_cs_n <= 1'b1;
                    ram_cs_n <= 1'b1;
                    spi_sclk <= 1'b0;
                    flash_active <= 1'b0;
                    ram_active <= 1'b0;
                end
            endcase
        end
    end
    
    // Next state logic
    always @(*) begin
        next_state = state;
        
        case (state)
            IDLE: begin
                if (is_flash_addr && !instr_ready) begin
                    next_state = SPI_CMD;
                end else if (is_ram_addr && (mem_we || mem_re) && !mem_ready) begin
                    next_state = SPI_CMD;
                end
            end
            
            SPI_CMD: begin
                if (bit_counter[2:0] == 3'b111 && ~spi_sclk) begin
                    next_state = SPI_ADDR;
                end
            end
            
            SPI_ADDR: begin
                if (bit_counter[4:0] == 5'b10111 && ~spi_sclk) begin
                    next_state = SPI_DATA;
                end
            end
            
            SPI_DATA: begin
                if (bit_counter[4:0] == 5'b11111 && ~spi_sclk) begin
                    next_state = DONE;
                end
            end
            
            DONE: begin
                next_state = IDLE;
            end
        endcase
    end

endmodule 
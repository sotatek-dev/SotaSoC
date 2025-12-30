/* RV32I CSR (Control and Status Register) File */

`include "debug_defines.vh"

module rv32i_csr (
    input wire clk,
    input wire rst_n,

    // CSR access interface
    input wire [11:0] csr_addr,      // CSR address (12 bits)
    input wire [31:0] csr_wdata,     // Data to write to CSR
    input wire csr_we,               // CSR write enable
    input wire [2:0] csr_op,         // CSR operation: 001=CSRRW, 010=CSRRS, 011=CSRRC, 101=CSRRWI, 110=CSRRSI, 111=CSRRCI
    output reg [31:0] csr_rdata,     // Data read from CSR
    output reg csr_illegal,          // Illegal CSR access

    // Counter inputs (for cycle, time, instret)
    input wire [31:0] cycle_count,
    input wire [31:0] instret_count,

    // Exception interface
    input wire exception_trigger,       // Trigger exception handling
    input wire [31:0] exception_cause,  // Exception cause code
    input wire [31:0] exception_pc,     // PC of instruction causing exception
    input wire [31:0] exception_value,  // Value for mtval
    output wire [31:0] mtvec_out,       // Output mtvec for PC redirection
    
    // MRET interface
    input wire mret_trigger,            // Trigger MRET handling
    output wire [31:0] mepc_out         // Output mepc for PC redirection
);

    // CSR register definitions
    // Machine-level CSRs
    reg [31:0] mstatus;      // 0x300 - Machine status register
    // Note: misa (0x301) is read-only constant, returns 0x40000100 (RV32I, MXL=1)
    reg [31:0] mie;          // 0x304 - Machine interrupt enable
    reg [31:0] mtvec;        // 0x305 - Machine trap vector base address
    reg [31:0] mscratch;     // 0x340 - Machine scratch register
    reg [31:0] mepc;         // 0x341 - Machine exception program counter
    reg [31:0] mcause;       // 0x342 - Machine trap cause
    reg [31:0] mtval;        // 0x343 - Machine trap value
    reg [31:0] mip;          // 0x344 - Machine interrupt pending
    // Note: medeleg (0x302), mideleg (0x303), satp (0x180), pmpcfg0 (0x3a0), pmpaddr0 (0x3b0),
    // mvendorid (0xf11), marchid (0xf12), mimpid (0xf13), mhartid (0xf14)
    // are writable but always return 0 when read

    // Read-only counters (shadow copies for atomicity)
    reg [31:0] cycle;        // 0xc00 - Cycle counter
    reg [31:0] instret;      // 0xc02 - Instructions retired counter

    // Output mtvec for exception handling
    assign mtvec_out = mtvec;
    
    // Output mepc for MRET
    assign mepc_out = mepc;

    // CSR read operation
    always @(*) begin
        csr_rdata = 32'd0;
        csr_illegal = 1'b0;

        case (csr_addr)
            // Machine-level CSRs
            12'h300: csr_rdata = mstatus;      // MSTATUS
            12'h301: csr_rdata = 32'h40000100; // MISA - read-only constant (RV32I, MXL=1)
            12'h302: csr_rdata = 32'd0;        // MEDELEG
            12'h303: csr_rdata = 32'd0;        // MIDELEG
            12'h304: csr_rdata = mie;          // MIE
            12'h305: csr_rdata = mtvec;        // MTVEC
            12'h340: csr_rdata = mscratch;     // MSCRATCH
            12'h341: csr_rdata = mepc;         // MEPC
            12'h342: csr_rdata = mcause;       // MCAUSE
            12'h343: csr_rdata = mtval;        // MTVAL
            12'h344: csr_rdata = mip;          // MIP

            // Supervisor CSRs
            12'h180: csr_rdata = 32'd0;        // SATP

            // Physical Memory Protection CSRs
            12'h3a0: csr_rdata = 32'd0;        // PMPCFG0
            12'h3b0: csr_rdata = 32'd0;        // PMPADDR0

            // Read-only counters
            12'hc00: csr_rdata = cycle;        // CYCLE
            12'hc01: csr_rdata = cycle;        // TIME
            12'hc02: csr_rdata = instret;      // INSTRET
            
            // Read-only counter upper halves (for 64-bit counters, return 0 for 32-bit)
            12'hc80: csr_rdata = 32'd0;        // CYCLEH
            12'hc81: csr_rdata = 32'd0;        // TIMEH
            12'hc82: csr_rdata = 32'd0;        // INSTRETH

            // Machine Information CSRs
            12'hf11: csr_rdata = 32'd0;        // MVENDORID
            12'hf12: csr_rdata = 32'd0;        // MARCHID
            12'hf13: csr_rdata = 32'd0;        // MIMPID
            12'hf14: csr_rdata = 32'd0;        // MHARTID

            default: begin
                csr_rdata = 32'd0;
                csr_illegal = 1'b1;            // Illegal CSR address
            end
        endcase
    end

    // CSR write operation
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Initialize CSRs to reset values
            mstatus <= 32'h00001800;  // MPP = 3 (Machine mode), other fields 0
            mie <= 32'd0;
            mtvec <= 32'd0;
            mscratch <= 32'd0;
            mepc <= 32'd0;
            mcause <= 32'd0;
            mtval <= 32'd0;
            mip <= 32'd0;
            cycle <= 32'd0;
            instret <= 32'd0;
            `DEBUG_PRINT(("Time %0t: CSR - CSR file reset", $time));
        end else begin
            // Update counters from external inputs
            cycle <= cycle_count;
            instret <= instret_count;

            // Handle exceptions (takes priority over CSR writes)
            if (exception_trigger) begin
                // Save current privilege mode and interrupt enable
                // MPP (bits [12:11]) <- current privilege mode (assume machine mode = 3)
                // MPIE (bit 7) <- MIE (bit 3)
                // MIE (bit 3) <- 0 (disable interrupts)
                mstatus <= {mstatus[31:13], 2'b11, mstatus[10:8], mstatus[3], mstatus[6:4], 1'b0, mstatus[2:0]};
                mepc <= exception_pc;
                mcause <= exception_cause;
                mtval <= exception_value;
                // `DEBUG_PRINT(("Time %0t: CSR - Exception triggered: cause=0x%h, pc=0x%h, mtval=0x%h, mtvec=0x%h", 
                //           $time, exception_cause, exception_pc, exception_value, mtvec));
            end else if (mret_trigger) begin
                // Handle MRET: restore privilege mode and interrupt enable
                // MIE (bit 3) <- MPIE (bit 7)
                // MPIE (bit 7) <- 1
                // MPP (bits [12:11]) <- 0 (U-mode, or could be restored from saved value)
                mstatus <= {mstatus[31:13], 2'b00, mstatus[10:8], 1'b1, mstatus[6:4], mstatus[7], mstatus[2:0]};
                // `DEBUG_PRINT(("Time %0t: CSR - MRET triggered: mepc=0x%h, mstatus=0x%h", 
                //           $time, mepc, mstatus));
            end

            // Handle CSR writes
            // Note: For CSRRS/CSRRC/CSRRSI/CSRRCI, if rs1 is 0, no write should occur (but read still happens)
            // This is handled by checking if the write data is non-zero for set/clear operations
            if (csr_we && !csr_illegal) begin
                case (csr_op)
                    3'b001: begin // CSRRW - Atomic Read/Write
                        case (csr_addr)
                            12'h300: mstatus <= csr_wdata;
                            12'h301: ; // MISA
                            12'h302: ; // MEDELEG
                            12'h303: ; // MIDELEG
                            12'h304: mie <= csr_wdata;
                            12'h305: mtvec <= csr_wdata;
                            12'h340: mscratch <= csr_wdata;
                            12'h341: mepc <= csr_wdata;
                            12'h342: mcause <= csr_wdata;
                            12'h343: mtval <= csr_wdata;
                            12'h344: mip <= csr_wdata;
                            12'h180: ; // SATP
                            12'h3a0: ; // PMPCFG0
                            12'h3b0: ; // PMPADDR0
                            12'hf11: ; // MVENDORID
                            12'hf12: ; // MARCHID
                            12'hf13: ; // MIMPID
                            12'hf14: ; // MHARTID
                            // Read-only CSRs (cycle, time, instret) - ignore writes
                        endcase
                    end
                    3'b010: begin // CSRRS - Atomic Read and Set Bits
                        case (csr_addr)
                            12'h300: mstatus <= mstatus | csr_wdata;
                            12'h301: ; // MISA
                            12'h302: ; // MEDELEG
                            12'h303: ; // MIDELEG
                            12'h304: mie <= mie | csr_wdata;
                            12'h305: mtvec <= mtvec | csr_wdata;
                            12'h340: mscratch <= mscratch | csr_wdata;
                            12'h341: mepc <= mepc | csr_wdata;
                            12'h342: mcause <= mcause | csr_wdata;
                            12'h343: mtval <= mtval | csr_wdata;
                            12'h344: mip <= mip | csr_wdata;
                            12'h180: ; // SATP
                            12'h3a0: ; // PMPCFG0
                            12'h3b0: ; // PMPADDR0
                            12'hf11: ; // MVENDORID
                            12'hf12: ; // MARCHID
                            12'hf13: ; // MIMPID
                            12'hf14: ; // MHARTID
                        endcase
                    end
                    3'b011: begin // CSRRC - Atomic Read and Clear Bits
                        case (csr_addr)
                            12'h300: mstatus <= mstatus & ~csr_wdata;
                            12'h301: ; // MISA
                            12'h302: ; // MEDELEG
                            12'h303: ; // MIDELEG
                            12'h304: mie <= mie & ~csr_wdata;
                            12'h305: mtvec <= mtvec & ~csr_wdata;
                            12'h340: mscratch <= mscratch & ~csr_wdata;
                            12'h341: mepc <= mepc & ~csr_wdata;
                            12'h342: mcause <= mcause & ~csr_wdata;
                            12'h343: mtval <= mtval & ~csr_wdata;
                            12'h344: mip <= mip & ~csr_wdata;
                            12'h180: ; // SATP
                            12'h3a0: ; // PMPCFG0
                            12'h3b0: ; // PMPADDR0
                            12'hf11: ; // MVENDORID
                            12'hf12: ; // MARCHID
                            12'hf13: ; // MIMPID
                            12'hf14: ; // MHARTID
                        endcase
                    end
                    3'b101: begin // CSRRWI - Atomic Read/Write (Immediate)
                        case (csr_addr)
                            12'h300: mstatus <= {27'd0, csr_wdata[4:0]};
                            12'h301: ; // MISA
                            12'h302: ; // MEDELEG
                            12'h303: ; // MIDELEG
                            12'h304: mie <= {27'd0, csr_wdata[4:0]};
                            12'h305: mtvec <= {27'd0, csr_wdata[4:0]};
                            12'h340: mscratch <= {27'd0, csr_wdata[4:0]};
                            12'h341: mepc <= {27'd0, csr_wdata[4:0]};
                            12'h342: mcause <= {27'd0, csr_wdata[4:0]};
                            12'h343: mtval <= {27'd0, csr_wdata[4:0]};
                            12'h344: mip <= {27'd0, csr_wdata[4:0]};
                            12'h180: ; // SATP
                            12'h3a0: ; // PMPCFG0
                            12'h3b0: ; // PMPADDR0
                            12'hf11: ; // MVENDORID
                            12'hf12: ; // MARCHID
                            12'hf13: ; // MIMPID
                            12'hf14: ; // MHARTID
                        endcase
                    end
                    3'b110: begin // CSRRSI - Atomic Read and Set Bits (Immediate)
                        case (csr_addr)
                            12'h300: mstatus <= mstatus | {27'd0, csr_wdata[4:0]};
                            12'h301: ; // MISA
                            12'h302: ; // MEDELEG
                            12'h303: ; // MIDELEG
                            12'h304: mie <= mie | {27'd0, csr_wdata[4:0]};
                            12'h305: mtvec <= mtvec | {27'd0, csr_wdata[4:0]};
                            12'h340: mscratch <= mscratch | {27'd0, csr_wdata[4:0]};
                            12'h341: mepc <= mepc | {27'd0, csr_wdata[4:0]};
                            12'h342: mcause <= mcause | {27'd0, csr_wdata[4:0]};
                            12'h343: mtval <= mtval | {27'd0, csr_wdata[4:0]};
                            12'h344: mip <= mip | {27'd0, csr_wdata[4:0]};
                            12'h180: ; // SATP
                            12'h3a0: ; // PMPCFG0
                            12'h3b0: ; // PMPADDR0
                            12'hf11: ; // MVENDORID
                            12'hf12: ; // MARCHID
                            12'hf13: ; // MIMPID
                            12'hf14: ; // MHARTID
                        endcase
                    end
                    3'b111: begin // CSRRCI - Atomic Read and Clear Bits (Immediate)
                        case (csr_addr)
                            12'h300: mstatus <= mstatus & ~{27'd0, csr_wdata[4:0]};
                            12'h301: ; // MISA
                            12'h302: ; // MEDELEG
                            12'h303: ; // MIDELEG
                            12'h304: mie <= mie & ~{27'd0, csr_wdata[4:0]};
                            12'h305: mtvec <= mtvec & ~{27'd0, csr_wdata[4:0]};
                            12'h340: mscratch <= mscratch & ~{27'd0, csr_wdata[4:0]};
                            12'h341: mepc <= mepc & ~{27'd0, csr_wdata[4:0]};
                            12'h342: mcause <= mcause & ~{27'd0, csr_wdata[4:0]};
                            12'h343: mtval <= mtval & ~{27'd0, csr_wdata[4:0]};
                            12'h344: mip <= mip & ~{27'd0, csr_wdata[4:0]};
                            12'h180: ; // SATP
                            12'h3a0: ; // PMPCFG0
                            12'h3b0: ; // PMPADDR0
                            12'hf11: ; // MVENDORID
                            12'hf12: ; // MARCHID
                            12'hf13: ; // MIMPID
                            12'hf14: ; // MHARTID
                        endcase
                    end
                    default: begin
                        // Invalid CSR operation
                    end
                endcase

                `DEBUG_PRINT(("Time %0t: CSR - Write: addr=0x%h, op=%b, wdata=0x%h, rdata=0x%h", 
                         $time, csr_addr, csr_op, csr_wdata, csr_rdata));
            end
        end
    end

endmodule


`ifndef DEBUG_DEFINES_VH
`define DEBUG_DEFINES_VH

`ifdef IVERILOG
`define DEBUG_PRINT(args) $display args
`else
`define DEBUG_PRINT(args)
`endif

`endif // DEBUG_DEFINES_VH


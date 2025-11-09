# Get device information
set device [get_property PART [current_design]]
puts "Floorplanning for device: $device"

# Get clock region information
set clock_regions [get_clock_regions]
puts "Available clock regions: [llength $clock_regions]"

# ============================================================================
# 0. CLEANUP EXISTING PBLOCKS (if script is run multiple times)
# ============================================================================

puts "Checking for existing pblocks..."

set existing_pblocks [list pblock_regfile pblock_ex_mem pblock_if_id pblock_id_ex pblock_mem_wb pblock_pc]

foreach pblock_name $existing_pblocks {
    if {[get_pblocks -quiet $pblock_name] != ""} {
        puts "  Deleting existing pblock: $pblock_name"
        delete_pblocks $pblock_name
    }
}

puts "Cleanup complete.\n"


# ============================================================================
# Helper Utilities
# ============================================================================

proc unique_primitive_cells {cells used_list_name} {
    upvar 1 $used_list_name used_list
    set unique {}
    foreach cell $cells {
        if {[lsearch -exact $used_list $cell] == -1} {
            lappend unique $cell
            lappend used_list $cell
        }
    }
    return $unique
}

set used_primitive_cells {}

# ============================================================================
# Pblock Range Definitions
# ============================================================================

set PBLOCK_REGFILE_RANGE {SLICE_X28Y0:SLICE_X33Y19}
set PBLOCK_REGFILE_RANGE2 {SLICE_X34Y0:SLICE_X45Y19}
set PBLOCK_EX_MEM_RANGE  {SLICE_X28Y34:SLICE_X33Y49}
set PBLOCK_EX_MEM_RANGE2  {SLICE_X34Y34:SLICE_X39Y49}
set PBLOCK_IF_ID_RANGE   {SLICE_X38Y20:SLICE_X47Y23}
set PBLOCK_ID_EX_RANGE   {SLICE_X28Y20:SLICE_X31Y33}
set PBLOCK_ID_EX_RANGE2   {SLICE_X32Y20:SLICE_X37Y33}
# set PBLOCK_MEM_WB_RANGE  {SLICE_X48Y50:SLICE_X59Y80}
set PBLOCK_PC_RANGE      {SLICE_X38Y24:SLICE_X41Y33}
set PBLOCK_PC_RANGE2     {SLICE_X40Y24:SLICE_X47Y49}


# ============================================================================
# 1. REGISTER FILE REGION
# ============================================================================

if {[get_cells -hierarchical -filter {NAME =~ "*register_file*"}] != ""} {
    puts "Creating Register File Pblock..."
    
    # Create Pblock for Register File (will be created fresh after cleanup)
    create_pblock pblock_regfile
    set_property IS_SOFT false [get_pblocks pblock_regfile]
    
    set regfile_cells [get_cells -hierarchical -filter {
        NAME =~ "*register_file*"
    }]
    
    set regfile_cells [unique_primitive_cells $regfile_cells used_primitive_cells]
    if {[llength $regfile_cells] > 0} {
        add_cells_to_pblock pblock_regfile $regfile_cells
    }
    
    resize_pblock pblock_regfile -add $PBLOCK_REGFILE_RANGE
    resize_pblock pblock_regfile -add $PBLOCK_REGFILE_RANGE2
    
    puts "Register File Pblock created with [llength [get_cells -of_objects [get_pblocks pblock_regfile]]] cells"
}

# EX/MEM pipeline registers
if {[get_cells -hierarchical -filter {NAME =~ "*/ex_mem*"}] != ""} {
    # Create Pblock for EX/MEM (will be created fresh after cleanup)
    create_pblock pblock_ex_mem
    set_property IS_SOFT false [get_pblocks pblock_ex_mem]
    set ex_mem_cells [get_cells -hierarchical -filter {NAME =~ "*/ex_mem*"}]
    set ex_mem_cells [unique_primitive_cells $ex_mem_cells used_primitive_cells]
    if {[llength $ex_mem_cells] > 0} {
        add_cells_to_pblock pblock_ex_mem $ex_mem_cells
        resize_pblock pblock_ex_mem -add $PBLOCK_EX_MEM_RANGE
        resize_pblock pblock_ex_mem -add $PBLOCK_EX_MEM_RANGE2
        puts "EX/MEM Pblock created"
    }
}



# ============================================================================
# 2. PIPELINE REGISTERS - Between stages
# ============================================================================

puts "Creating Pipeline Register Pblocks..."

# IF/ID pipeline registers
if {[get_cells -hierarchical -filter {NAME =~ "*/if_id*"}] != ""} {
    # Create Pblock for IF/ID (will be created fresh after cleanup)
    create_pblock pblock_if_id
    set_property IS_SOFT false [get_pblocks pblock_if_id]
    set if_id_cells [get_cells -hierarchical -filter {NAME =~ "*/if_id*"}]
    set if_id_cells [unique_primitive_cells $if_id_cells used_primitive_cells]
    if {[llength $if_id_cells] > 0} {
        add_cells_to_pblock pblock_if_id $if_id_cells
        resize_pblock pblock_if_id -add $PBLOCK_IF_ID_RANGE
        puts "IF/ID Pblock created"
    }
}

# ID/EX pipeline registers
if {[get_cells -hierarchical -filter {NAME =~ "*/id_ex*"}] != ""} {
    # Create Pblock for ID/EX (will be created fresh after cleanup)
    create_pblock pblock_id_ex
    set_property IS_SOFT false [get_pblocks pblock_id_ex]
    set id_ex_cells [get_cells -hierarchical -filter {NAME =~ "*/id_ex*"}]
    set id_ex_cells [unique_primitive_cells $id_ex_cells used_primitive_cells]
    if {[llength $id_ex_cells] > 0} {
        add_cells_to_pblock pblock_id_ex $id_ex_cells
        resize_pblock pblock_id_ex -add $PBLOCK_ID_EX_RANGE
        resize_pblock pblock_id_ex -add $PBLOCK_ID_EX_RANGE2
        puts "ID/EX Pblock created"
    }
}

# MEM/WB pipeline registers
# if {[get_cells -hierarchical -filter {NAME =~ "*/mem_wb*"}] != ""} {
#     # Create Pblock for MEM/WB (will be created fresh after cleanup)
#     create_pblock pblock_mem_wb
#     set_property IS_SOFT false [get_pblocks pblock_mem_wb]
#     set mem_wb_cells [get_cells -hierarchical -filter {NAME =~ "*/mem_wb*"}]
#     set mem_wb_cells [unique_primitive_cells $mem_wb_cells used_primitive_cells]
#     if {[llength $mem_wb_cells] > 0} {
#         add_cells_to_pblock pblock_mem_wb $mem_wb_cells
#         resize_pblock pblock_mem_wb -add $PBLOCK_MEM_WB_RANGE
#         puts "MEM/WB Pblock created"
#     }
# }


# ============================================================================
# 3. PC REGION - Branch and jump logic
# ============================================================================
# PC update logic with branch comparison - critical for timing
# This includes: PC register, PC next logic, branch comparison, jump logic

if {[get_cells -hierarchical -filter {NAME =~ "*pc*" || NAME =~ "*PC*"}] != ""} {
    puts "Creating PC Pblock..."
    
    # Create Pblock for PC (will be created fresh after cleanup)
    create_pblock pblock_pc
    set_property IS_SOFT false [get_pblocks pblock_pc]
    
    # Get PC-related cells
    set pc_cells [get_cells -hierarchical -filter {
        NAME =~ "*pc*" ||
        NAME =~ "*PC*" ||
        NAME =~ "*pc_next*"
    }]
    
    set pc_cells [unique_primitive_cells $pc_cells used_primitive_cells]
    if {[llength $pc_cells] > 0} {
        add_cells_to_pblock pblock_pc $pc_cells
    }
    
    resize_pblock pblock_pc -add $PBLOCK_PC_RANGE
    resize_pblock pblock_pc -add $PBLOCK_PC_RANGE2
    
    puts "PC Pblock created with [llength [get_cells -of_objects [get_pblocks pblock_pc]]] cells"
}


# Save floorplan
save_constraints -force
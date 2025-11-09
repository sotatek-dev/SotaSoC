# Suppress all messages except errors
set_msg_config -severity INFO -suppress
set_msg_config -severity WARNING -suppress
set_msg_config -severity "CRITICAL WARNING" -suppress

proc get_pblock_slack {from_pblock to_pblock} {
    set report [report_timing -quiet -from [get_cells -quiet -of_objects [get_pblocks -quiet $from_pblock]] -to [get_cells -quiet -of_objects [get_pblocks -quiet $to_pblock]] -max_paths 1 -return_string]
    # Extract the slack line (usually the last line)
    set lines [split $report "\n"]
    foreach line [lreverse $lines] {
        if {[regexp {slack\s+(-?[\d.]+)} $line -> slack_value]} {
            puts "$from_pblock->$to_pblock: $slack_value"
            return
        }
    }
    puts "$from_pblock->$to_pblock: N/A"
}

proc report_all_pblock_slack {} {
    get_pblock_slack pblock_ex_mem pblock_ex_mem
    get_pblock_slack pblock_pc pblock_pc
    get_pblock_slack pblock_id_ex pblock_id_ex
    get_pblock_slack pblock_id_ex pblock_ex_mem
    get_pblock_slack pblock_id_ex pblock_pc
    get_pblock_slack pblock_ex_mem pblock_pc
    get_pblock_slack pblock_ex_mem pblock_id_ex
    get_pblock_slack pblock_ex_mem pblock_mem_wb
}

# Run the report
report_all_pblock_slack

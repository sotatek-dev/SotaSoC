import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock

# Constants
CYCLES_PER_INSTRUCTION = 8
MEMORY_CYCLES = 3
NOP_INSTR = 0x00000013

# Global variables to track memory operations
mem_addr = 0x00000000
mem_wdata = 0x00000000
mem_wflag = 0x00000000

def get_mem_vars():
    """Get the current memory variables (for testing)"""
    return mem_addr, mem_wdata, mem_wflag

async def do_test(dut, memory, cycles, mem_data=0x00000000):
    """Do test"""
    global mem_addr, mem_wdata, mem_wflag

    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    dut.instr_data.value = memory[0x80000000]
    dut.mem_data.value = mem_data
    dut.instr_ready.value = 0
    dut.mem_ready.value = 0

    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1

    current_pc  = 0
    current_mem_we = 0
    current_mem_re = 0
    instr_wait_cycles = 0
    mem_wait_cycles = 0
    
    # Execute for several cycles
    for _ in range(cycles * MEMORY_CYCLES):
        await FallingEdge(dut.clk)
        if mem_wait_cycles == 0 and ((dut.mem_we == 1 and current_mem_we == 0) or (dut.mem_re == 1 and current_mem_re == 0)):
            dut.mem_ready.value = 0
            mem_wait_cycles = MEMORY_CYCLES
            current_mem_we = dut.mem_we.value
            current_mem_re = dut.mem_re.value

        if mem_wait_cycles > 0:
            mem_wait_cycles -= 1
            if mem_wait_cycles == 0:
                dut.mem_ready.value = 1
                if (current_mem_we == 1):
                    mem_addr = dut.mem_addr.value.integer
                    mem_wdata = dut.mem_wdata.value.integer
                    mem_wflag = dut.mem_wflag.value.integer
                # Reset current memory operation flags when memory operation completes
                current_mem_we = 0
                current_mem_re = 0

        if instr_wait_cycles == 0 and dut.instr_addr.value.integer != current_pc:
            dut.instr_ready.value = 0
            instr_wait_cycles = MEMORY_CYCLES
            current_pc = dut.instr_addr.value.integer

        # Only fetch instruction if memory is not busy
        if mem_wait_cycles == 0 and instr_wait_cycles > 0:
            instr_wait_cycles -= 1
            if instr_wait_cycles == 0:
                dut.instr_data.value = memory[dut.instr_addr.value.integer]
                dut.instr_ready.value = 1

        # print(f"mem_wait_cycles={mem_wait_cycles}, instr_wait_cycles={instr_wait_cycles}")
        # print(f"Cycle {_}: PC={dut.instr_addr.value.integer:08x}, Instr={memory[dut.instr_addr.value.integer]:08x}")
        # print(f"Cycle {_}: mem_addr={dut.mem_addr.value.integer:08x}, mem_data={dut.mem_data.value.integer:08x}, mem_wdata={dut.mem_wdata.value.integer:08x}, mem_wflag={dut.mem_wflag.value.integer:08x}") 
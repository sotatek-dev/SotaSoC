#!/usr/bin/env python3
"""
Script to extract signature from RISCOF test simulation.
This script:
1. Gets begin_signature and end_signature addresses from ELF
2. Runs cocotb simulation with the bin file
3. Extracts signature from memory dump
4. Writes signature file in RISCOF format
"""

import os
import sys
import subprocess
import argparse
import re
import struct
import shutil
import time

# Global log file path
_log_file = None

def _get_log_file():
    """Get or create log file path"""
    global _log_file
    if _log_file is not None:
        return _log_file
    
    # Always use /tmp for log file
    _log_file = '/tmp/riscof_progress.log'
    return _log_file

def log_message(msg):
    """Write message to log file"""
    log_file = _get_log_file()
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(msg)
            f.flush()
    except:
        pass

# in the generated cocotb test

def get_symbol_address(elf_file, symbol_name):
    """Get address of a symbol from ELF file using readelf"""
    try:
        cmd = ['riscv32-unknown-elf-readelf', '-s', elf_file]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if symbol_name in line:
                # Parse readelf output: "   Num:    Value  Size Type    Bind   Vis      Ndx Name"
                # Example: "    12: 80001000     0 NOTYPE  GLOBAL DEFAULT    3 begin_signature"
                parts = line.split()
                if len(parts) >= 8 and parts[7] == symbol_name:
                    addr_str = parts[1]
                    return int(addr_str, 16)
        
        # Try with riscv64 if riscv32 doesn't work
        cmd = ['riscv64-unknown-elf-readelf', '-s', elf_file]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if symbol_name in line:
                parts = line.split()
                if len(parts) >= 8 and parts[7] == symbol_name:
                    addr_str = parts[1]
                    return int(addr_str, 16)
        
        return None
    except (subprocess.CalledProcessError, ValueError, IndexError) as e:
        log_message(f"[{time.strftime('%H:%M:%S')}] Error getting symbol address: {e}\n")
        return None


def extract_signature_from_memory(memory, begin_addr, end_addr):
    """Extract signature from memory between begin_addr and end_addr"""
    signature = []
    
    # Ensure addresses are aligned to 4-byte boundary
    begin_addr = begin_addr & ~0x3
    end_addr = (end_addr + 3) & ~0x3
    
    # Extract 32-bit words from memory (little-endian)
    addr = begin_addr
    while addr < end_addr:
        # Read 32-bit word (little-endian)
        word = (memory[addr] |
                (memory[addr + 1] << 8) |
                (memory[addr + 2] << 16) |
                (memory[addr + 3] << 24))
        signature.append(word)
        addr += 4
    
    return signature

def run_simulation_and_extract(elf_file, bin_file, sig_file, project_root):
    """Run cocotb simulation and extract signature
    
    Args:
        elf_file: Path to ELF file
        bin_file: Path to BIN file
        sig_file: Path to output signature file
        project_root: Project root directory
    """
    
    # Extract test name from path for logging
    # Path structure: riscof_work/src/test.S/dut/my.bin
    test_name = os.path.basename(os.path.dirname(os.path.dirname(bin_file)))
    if test_name.endswith('.S') or test_name.endswith('.s'):
        test_display = test_name
    else:
        test_display = os.path.basename(bin_file)
    
    # Log at the beginning to show which test is running
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Starting...\n")
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] ELF: {elf_file}\n")
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] BIN: {bin_file}\n")
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Signature: {sig_file}\n")
   
    # Get signature addresses from ELF
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Reading ELF file...\n")
    begin_addr = get_symbol_address(elf_file, 'begin_signature')
    end_addr = get_symbol_address(elf_file, 'end_signature')
    
    # Get tohost address from ELF (for detecting program completion)
    tohost_addr = get_symbol_address(elf_file, 'tohost')
    
    if begin_addr is None or end_addr is None:
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Error: Could not find signature addresses in ELF file\n")
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] begin_signature: {begin_addr}, end_signature: {end_addr}\n")
        return False
    
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Signature region: 0x{begin_addr:08x} to 0x{end_addr:08x}\n")
    if tohost_addr is not None:
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Tohost address: 0x{tohost_addr:08x}\n")
    else:
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Error: Could not find tohost address in ELF file\n")
        return False
    
    # Convert to byte addresses for memory access (SPI memory uses 24-bit addresses)
    # The SPI memory controller uses lower 24 bits of address
    begin_byte_addr = begin_addr
    end_byte_addr = end_addr
    tohost_byte_addr = tohost_addr if tohost_addr is not None else None
    
    # Format tohost_byte_addr for Python code generation
    tohost_byte_addr_str = f"0x{tohost_byte_addr:08x}" if tohost_byte_addr is not None else "None"
    
    # Get test directory and template directory
    test_dir = os.path.dirname(bin_file)
    template_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Copy template files to test directory
    template_py = os.path.join(template_dir, 'test_riscof_signature.template.py')
    template_mk = os.path.join(template_dir, 'test_riscof_signature.template.mk')
    
    if not os.path.exists(template_py):
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Error: Template file not found: {template_py}\n")
        return False
    
    if not os.path.exists(template_mk):
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Error: Template makefile not found: {template_mk}\n")
        return False
    
    # Copy makefile template to test directory
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Preparing test files...\n")
    test_makefile = os.path.join(test_dir, 'test_riscof_signature.mk')
    shutil.copy2(template_mk, test_makefile)
    
    # Read Python template
    with open(template_py, 'r') as f:
        template_content = f.read()
    
    # Replace placeholders with actual values (format addresses as hex)
    test_content = template_content.format(
        PROJECT_ROOT=project_root,
        BIN_FILE=bin_file,
        BEGIN_ADDR=f"0x{begin_addr:08x}",
        END_ADDR=f"0x{end_addr:08x}",
        BEGIN_BYTE_ADDR=f"0x{begin_byte_addr:08x}",
        END_BYTE_ADDR=f"0x{end_byte_addr:08x}",
        TOHOST_BYTE_ADDR=tohost_byte_addr_str,
        SIG_FILE=sig_file
    )
    
    # Write generated test file
    riscof_test_file = os.path.join(test_dir, 'test_riscof_signature.py')
    with open(riscof_test_file, 'w') as f:
        f.write(test_content)
    
    # Create vcd directory in test_dir before running simulation
    vcd_dir = os.path.join(test_dir, 'vcd')
    os.makedirs(vcd_dir, exist_ok=True)
    
    # Run cocotb simulation using the copied makefile in test directory
    env = os.environ.copy()
    env['BIN_FILE'] = bin_file
    env['PYTHONPATH'] = os.path.join(project_root, 'tb', 'cocotb') + ':' + env.get('PYTHONPATH', '')
    
    # Change to test directory and run make using the copied makefile
    # Pass PROJECT_ROOT to makefile so it can find RTL files even when run from test_dir
    cmd = ['make', '-f', test_makefile, 'MODULE=test_riscof_signature', f'BIN_FILE={bin_file}', f'PROJECT_ROOT={project_root}']
    
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Running simulation...\n")
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Command: {' '.join(cmd)}\n")
    log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Working directory: {test_dir}\n")
    
    # Use errors='replace' or 'ignore' to handle binary data in output
    result = subprocess.run(cmd, cwd=test_dir, env=env, capture_output=True, text=True, errors='replace')
    
    if result.returncode != 0:
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Simulation failed (return code: {result.returncode})\n")
        # Log error output
        stdout_preview = result.stdout[:10000] if result.stdout else ""
        stderr_preview = result.stderr[:10000] if result.stderr else ""
        if stdout_preview:
            log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] STDOUT (first 10000 chars):\n{stdout_preview}\n")
        if stderr_preview:
            log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] STDERR (first 10000 chars):\n{stderr_preview}\n")
        if len(result.stdout) > 10000:
            log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] ... (stdout truncated, total {len(result.stdout)} chars)\n")
        if len(result.stderr) > 10000:
            log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] ... (stderr truncated, total {len(result.stderr)} chars)\n")
        return False
    
    # Check if signature file was created
    if os.path.exists(sig_file):
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] ✓ Signature file created successfully\n")
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] Signature: {sig_file}\n")
        return True
    else:
        log_message(f"[{time.strftime('%H:%M:%S')}] [TEST: {test_display}] ✗ Error: Signature file not created: {sig_file}\n")
        return False

def main():
    # Initialize log file early
    log_file = _get_log_file()
    log_message(f"\n{'='*80}\n")
    log_message(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] extract_signature.py started\n")
    log_message(f"[{time.strftime('%H:%M:%S')}] Log file: {log_file}\n")
    log_message(f"[{time.strftime('%H:%M:%S')}] PID: {os.getpid()}\n")
    log_message(f"[{time.strftime('%H:%M:%S')}] Args: {sys.argv}\n")

    parser = argparse.ArgumentParser(description='Extract signature from RISCOF test')
    parser.add_argument('--elf', required=True, help='ELF file path')
    parser.add_argument('--bin', required=True, help='BIN file path')
    parser.add_argument('--signature', required=True, help='Output signature file path')
    parser.add_argument('--project-root', required=True, help='Project root directory')
    
    args = parser.parse_args()
    
    log_message(f"[{time.strftime('%H:%M:%S')}] Arguments parsed successfully\n")

    success = run_simulation_and_extract(
        args.elf, args.bin, args.signature, args.project_root
    )
    
    log_message(f"[{time.strftime('%H:%M:%S')}] Script finished: {'SUCCESS' if success else 'FAILED'}\n")
    log_message(f"{'='*80}\n\n")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()


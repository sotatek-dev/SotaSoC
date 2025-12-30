#!/usr/bin/env python3
"""
Convert ELF binary to simple hex format (one 32-bit word per line)
Format: Each line is 8 hex characters representing a 32-bit instruction
Example:
0480006f
34202f73
00800f93
"""

import sys
import struct

def elf_to_hex(elf_file, hex_file):
    """Convert ELF to simple hex format"""
    try:
        # Use objcopy to extract binary
        import subprocess
        import os
        import tempfile
        
        # Create temporary binary file
        bin_file = hex_file + '.bin'
        
        # Extract binary from ELF
        cmd = ['riscv32-unknown-elf-objcopy', '-O', 'binary', elf_file, bin_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Try riscv64
            cmd = ['riscv64-unknown-elf-objcopy', '-O', 'binary', elf_file, bin_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error: Failed to extract binary from ELF: {result.stderr}")
                return False
        
        # Read binary and convert to hex
        with open(bin_file, 'rb') as f:
            data = f.read()
        
        # Write hex file (one word per line)
        with open(hex_file, 'w') as f:
            # Write 32-bit words (little-endian)
            for i in range(0, len(data), 4):
                if i + 4 <= len(data):
                    word = struct.unpack('<I', data[i:i+4])[0]
                    f.write(f"{word:08x}\n")
                else:
                    # Handle last incomplete word
                    word_bytes = data[i:] + b'\x00' * (4 - len(data[i:]))
                    word = struct.unpack('<I', word_bytes)[0]
                    f.write(f"{word:08x}\n")
        
        # Clean up
        if os.path.exists(bin_file):
            os.remove(bin_file)
        
        return True
    except Exception as e:
        print(f"Error converting ELF to hex: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: elf_to_hex.py <elf_file> <hex_file>")
        sys.exit(1)
    
    success = elf_to_hex(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)


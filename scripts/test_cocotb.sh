#!/bin/bash

# Test script for all cocotb tests in tb/cocotb/
# This script runs each test and stops immediately on any error

set -e  # Exit immediately if a command exits with a non-zero status

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COCOTB_DIR="$PROJECT_ROOT/tb/cocotb"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Running all cocotb tests..."
echo "=========================================="
echo "Project root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Tests to skip
SKIP_TESTS="test_uart_rx.mk"

# Find all test makefiles (test_*.mk), exclude skipped tests, and sort them
mapfile -t test_makefiles < <(find "$COCOTB_DIR" -maxdepth 1 -name "test_*.mk" -printf "%f\n" | grep -v -E "^($SKIP_TESTS)$" | sort)

if [ ${#test_makefiles[@]} -eq 0 ]; then
    echo -e "${RED}No test makefiles found in $COCOTB_DIR${NC}"
    exit 1
fi

total_tests=${#test_makefiles[@]}
echo "Found $total_tests test(s): ${test_makefiles[*]}"
echo ""
current_test=0

for makefile in "${test_makefiles[@]}"; do
    current_test=$((current_test + 1))
    test_name="${makefile%.mk}"
    
    echo "=========================================="
    echo "[$current_test/$total_tests] Running $test_name..."
    echo "=========================================="
    
    # Run the test - will exit on failure due to set -e
    set -x
    make -f "tb/cocotb/$makefile" PROJECT_ROOT="$PROJECT_ROOT"
    set +x
    
    echo -e "${GREEN}$test_name passed${NC}"
    echo ""
done

echo "=========================================="
echo -e "${GREEN}All $total_tests tests passed!${NC}"
echo "=========================================="

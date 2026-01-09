#!/bin/bash

# Test script for all bin files in tb/riscv-tests/bin/
# This script runs each bin file through the SoC testbench and reports pass/fail status

HEX_DIR="tb/riscv-tests/bin"
MAKEFILE="tb/cocotb/test_soc.mk"
LOG_DIR="test_logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Initialize counters
total_tests=0
passed_tests=0
failed_tests=0

echo "=========================================="
echo "Running tests for all bin files..."
echo "=========================================="

# Get list of bin files
bin_files=($(find "$HEX_DIR" -name "*.bin" | sort))

if [ ${#bin_files[@]} -eq 0 ]; then
    echo "No bin files found in $HEX_DIR"
    exit 1
fi

echo "Found ${#bin_files[@]} bin files to test"
echo ""

# Test each bin file
for bin_file in "${bin_files[@]}"; do
    # Extract test name from file path
    test_name=$(basename "$bin_file" .bin)
    total_tests=$((total_tests + 1))
    
    echo -n "Testing $test_name... "
    
    # Run the test and capture output
    log_file="$LOG_DIR/${test_name}.log"
    if make -f "$MAKEFILE" BIN_FILE="$bin_file" > "$log_file" 2>&1; then
        # Check if the test actually passed by looking for "test_soc passed" in the output
        if grep -q "test_soc passed" "$log_file"; then
            echo -e "${GREEN}PASS${NC}"
            passed_tests=$((passed_tests + 1))
        else
            # Check if it failed
            if grep -q "test_soc failed" "$log_file"; then
                echo -e "${RED}FAIL${NC}"
                failed_tests=$((failed_tests + 1))
                # Extract the assertion error for more details
                error_msg=$(grep -A 1 "AssertionError:" "$log_file" | tail -1 | sed 's/^[[:space:]]*//')
                if [ -n "$error_msg" ]; then
                    echo "    Error: $error_msg"
                fi
            else
                echo -e "${YELLOW}UNKNOWN${NC}"
                echo "    Check log: $log_file"
            fi
        fi
    else
        echo -e "${RED}ERROR${NC}"
        echo "    Make command failed. Check log: $log_file"
    fi
done

echo ""
echo "=========================================="
echo "Test Summary:"
echo "=========================================="
echo "Total tests:  $total_tests"
echo -e "Passed:       ${GREEN}$passed_tests${NC}"
echo -e "Failed:       ${RED}$failed_tests${NC}"

if [ $failed_tests -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}$failed_tests test(s) failed.${NC}"
    echo "Check individual log files in $LOG_DIR/ for details."
    exit 1
fi 
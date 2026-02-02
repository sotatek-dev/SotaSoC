#!/bin/bash

LOG_DIR="test_logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

set -x

# Sample bash function that demonstrates common patterns
run_test() {
    local makefile="$1"
    local test_function="$2"
    local bin_file="$3"

    local test_name=$(basename "$bin_file" .bin)

    echo -n "Testing $test_name... "
    
    # Run the test and capture output
    log_file="$LOG_DIR/${test_name}.log"
    if make -f "$makefile" TESTCASE="$test_function" BIN_FILE="$bin_file" > "$log_file" 2>&1; then
        # Check if the test actually passed by looking for "test_soc passed" in the output
        if grep -q "PASS    " "$log_file"; then
            echo -e "${GREEN}PASS${NC}"
        else
            # Check if it failed
            if grep -q "test_soc failed" "$log_file"; then
                echo -e "${RED}FAIL${NC}"
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
}

run_test "tb/cocotb/test_spi_master.mk" "test_transfer_multiple_bytes_mode0" "tb/spi-tests/spi-transfer.bin"
run_test "tb/cocotb/test_spi_master.mk" "test_transfer_multiple_bytes_mode1" "tb/spi-tests/spi-transfer.bin"
run_test "tb/cocotb/test_spi_master.mk" "test_transfer_multiple_bytes_mode2" "tb/spi-tests/spi-transfer.bin"
run_test "tb/cocotb/test_spi_master.mk" "test_transfer_multiple_bytes_mode3" "tb/spi-tests/spi-transfer.bin"
run_test "tb/cocotb/test_spi_master.mk" "test_transfer_single_byte_mode0" "tb/spi-tests/spi-transfer.bin"
run_test "tb/cocotb/test_spi_master.mk" "test_transfer_single_byte_mode1" "tb/spi-tests/spi-transfer.bin"
run_test "tb/cocotb/test_spi_master.mk" "test_transfer_single_byte_mode2" "tb/spi-tests/spi-transfer.bin"
run_test "tb/cocotb/test_spi_master.mk" "test_transfer_single_byte_mode3" "tb/spi-tests/spi-transfer.bin"
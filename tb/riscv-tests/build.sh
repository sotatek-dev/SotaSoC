#!/bin/bash

# This file is modified from:
# https://github.com/georgeyhere/Toast-RV32i/blob/main/scripts/memgen.sh

# This is a script to compile and link the assembly tests from riscv-tests
# and then generate a dump and memory configuration file for each test.


# Enable command tracing
set -x

WORKSPACE=pwd
TESTDIR="`$WORKSPACE`/rv32ui/"
TEST_INCLUDE="`$WORKSPACE`/include/"
TEST_MACROS="`$WORKSPACE`/macros/scalar/"


##########################################################################
# Instructions are encoded starting from 0x00000000
# Data memory is encoded starting from 0x00002000

getfiles="ls $TESTDIR*.S"
filenames=`$getfiles`

for eachfile in $filenames
do
    if [ ! -f "$filenames" ]
    then
        # compile and link using gcc and ld;
        # then generate dump and $readmemh hex file
        riscv64-unknown-elf-gcc     -c $eachfile -I"$TEST_INCLUDE" -I"$TEST_MACROS" -o "$eachfile.o" -march=rv32i_zicsr -mabi=ilp32
        # find a solution to link rv32i from:
        # https://github.com/riscv-collab/riscv-gnu-toolchain/issues/409
        riscv64-unknown-elf-ld      "$eachfile.o" -Ttext 0x00000000 -Tdata 0x01000000 -o $eachfile.v2 -m elf32lriscv
        riscv64-unknown-elf-objcopy -O binary $eachfile.v2 $eachfile.bin
        riscv64-unknown-elf-objdump -d $eachfile.v2 > $eachfile.dump
        # elf2hex --bit-width 32 --input $eachfile.v2 > $eachfile.hex
        rm $eachfile.v2
    else
        echo "Warning: File \"$eachfile\" doesn't exist."
    fi
done

##########################################################################
# Move .mem file into /mem/hex
getMem="ls $TESTDIR*.bin"
memnames=`$getMem`

mkdir -p ./bin/

echo "Moving memory files into /mem/hex/"
for eachfile in $memnames
do
    mv $eachfile ./bin/
done

##########################################################################
# moving dump files into /mem/dump
getDump="ls $TESTDIR*.dump"
dumpnames=`$getDump`

mkdir -p ./dump/

echo "Moving dump files into /mem/dump"
for eachfile in $dumpnames
do
    mv $eachfile ./dump/
done

rm rv32ui/*.o
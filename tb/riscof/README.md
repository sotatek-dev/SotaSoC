# Download riscv-arch-test
```bash
git submodule init 
git submodule update
```

# Install riscof
```bash
cd tb/riscof
python -m venv venv
source venv/bin/activate
pip3 install riscof
pip3 install cocotb
```

# Run tests
```bash
riscof run --config=config.ini --suite=./riscv-arch-test/riscv-test-suite/rv32e_m/E --env=./riscv-arch-test/riscv-test-suite/env
riscof run --config=config.ini --suite=./riscv-arch-test/riscv-test-suite/rv32e_m/C --env=./riscv-arch-test/riscv-test-suite/env
riscof run --config=config.ini --suite=./riscv-arch-test/riscv-test-suite/rv32e_m/privilege --env=./riscv-arch-test/riscv-test-suite/env
```
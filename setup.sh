#!/bin/bash
# RV32E Processor Setup Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "=== RV32E Processor Setup ==="
echo ""

# Detect operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Function to install package
install_package() {
    local package=$1
    local install_cmd=$2
    
    if ! command -v $package &> /dev/null; then
        echo "Installing $package..."
        eval $install_cmd
    else
        echo "$package is already installed."
    fi
}

# Install system dependencies
echo "Installing system dependencies..."

if [[ "$OS" == "macos" ]]; then
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    install_package "iverilog" "brew install icarus-verilog"
    install_package "gtkwave" "brew install gtkwave"
    install_package "make" "brew install make"
    
elif [[ "$OS" == "linux" ]]; then
    # Detect package manager
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt-get"
        UPDATE_CMD="sudo apt-get update"
        INSTALL_CMD="sudo apt-get install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        UPDATE_CMD="sudo yum update -y"
        INSTALL_CMD="sudo yum install -y"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        UPDATE_CMD="sudo pacman -Sy"
        INSTALL_CMD="sudo pacman -S --noconfirm"
    else
        echo "Unsupported package manager. Please install the following manually:"
        echo "  - Icarus Verilog (iverilog)"
        echo "  - GTKWave (gtkwave)"
        echo "  - Make (make)"
        exit 1
    fi
    
    echo "Using package manager: $PKG_MANAGER"
    eval $UPDATE_CMD
    
    install_package "iverilog" "$INSTALL_CMD iverilog"
    install_package "gtkwave" "$INSTALL_CMD gtkwave"
    install_package "make" "$INSTALL_CMD make"
fi

echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3.7 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is required but not installed."
    echo "Please install pip3."
    exit 1
fi

echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
echo ""

# Setup project structure
echo "Setting up project structure..."
make setup
echo ""

# Test the setup
echo "Testing the setup..."
echo ""

# Test Icarus Verilog
echo "Testing Icarus Verilog..."
if iverilog -V &> /dev/null; then
    echo "✓ Icarus Verilog is working"
else
    echo "✗ Icarus Verilog test failed"
    exit 1
fi

# Test GTKWave
echo "Testing GTKWave..."
if gtkwave --version &> /dev/null; then
    echo "✓ GTKWave is working"
else
    echo "✗ GTKWave test failed"
    exit 1
fi

# Test Python packages
echo "Testing Python packages..."
python3 -c "import cocotb; print('✓ cocotb is working')" || {
    echo "✗ cocotb test failed"
    exit 1
}

echo ""

# Build the project
echo "Building the project..."
make build
echo ""

echo "=== Setup completed successfully! ==="
echo ""
echo "Next steps:"
echo "1. Run tests: make test"
echo "2. Run specific test: make test-alu"
echo "3. View waveforms: make wave"
echo "4. Clean build: make clean"
echo ""
echo "For more information, see README.md" 
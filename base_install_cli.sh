#!/bin/bash

echo "Installing Foot Trace Processor dependencies..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew already installed"
fi

# Make sure Homebrew is in PATH
eval "$(/opt/homebrew/bin/brew shellenv)"

# Install Python if not present
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    brew install python@3.11
else
    echo "Python already installed"
fi

# Install other required system packages
echo "Installing system dependencies..."
brew install opencv
brew install tcl-tk

# Install Python packages
echo "Installing Python packages..."
pip3 install --user opencv-python numpy Pillow svgwrite watchdog pyyaml

echo "Installation complete!"
echo "You can now run the program with: python3 foot_trace_gui.py"
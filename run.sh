#!/bin/bash

echo "Starting KakaoMap Clone Application..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.12 or later"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Run the application
echo
echo "Launching KakaoMap Clone..."
python3 main.py

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo
    echo "Application exited with error code $exit_code"
fi

exit $exit_code
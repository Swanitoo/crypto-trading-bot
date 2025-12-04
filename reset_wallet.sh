#!/bin/bash

# Script to reset paper trading wallet using the virtual environment

# Activate virtual environment
source venv/bin/activate

# Run the reset script
python3 reset_wallet.py "$@"

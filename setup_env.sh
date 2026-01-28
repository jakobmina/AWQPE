#!/bin/bash

# Configuration
ENV_NAME="awqpe_env"
REQ_FILE="requirements.txt"

echo "=== AWQPE Environment Setup ==="

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment: $ENV_NAME..."
python3 -m venv $ENV_NAME

# Activate and install
echo "Installing dependencies from $REQ_FILE..."
source "$ENV_NAME/bin/activate"
pip install --upgrade pip
pip install -r "$REQ_FILE"

echo ""
echo "=== Setup Complete ==="
echo "To activate the environment, run:"
echo "source $ENV_NAME/bin/activate"

#!/bin/bash

# Exit on error
set -e

# Make this script executable with: chmod +x setup_env.sh

# Check if uv is installed
if ! command -v uv &> /dev/null
then
    echo "Installing uv..."
    # Install uv using the official install script
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to the current PATH
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies using uv
echo "Installing dependencies with uv..."
uv pip install -r requirements.txt

# Run ruff to check code quality
echo "Running ruff to check code quality..."
uv pip install ruff
ruff check .

echo "Setup complete! You can activate the environment with: source .venv/bin/activate"

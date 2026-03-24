#!/bin/bash
set -e

# Self-check for executable permissions and fix if needed
if [ ! -x "$0" ]; then
    echo "Setting executable permissions on install script..."
    chmod +x "$0"
    echo "Re-launching script with proper permissions..."
    exec "$0" "$@"
fi

echo "Installing ai-task-orchestrator..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "Error: Python 3.11 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install the package
echo "Installing package in virtual environment..."
python -m pip install -e .

# Verify installation
if [ -f .venv/bin/ai-task ]; then
    echo "✅ Installation successful!"
    echo ""
    echo "To use ai-task, you need to activate the virtual environment:"
    echo ""
    echo "    source .venv/bin/activate"
    echo ""
    echo "After activation, you can run 'ai-task --help' to get started."
    echo ""
    echo "To activate the environment in the future, run:"
    echo "    source .venv/bin/activate"
    echo ""
    echo "You may want to add this to your shell profile for convenience."
else
    echo "⚠️ Installation completed but 'ai-task' command not found in the virtual environment."
fi

# Deactivate the virtual environment at the end of the script
deactivate

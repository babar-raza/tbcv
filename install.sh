#!/bin/bash
# TBCV Installation Script

set -e

echo "========================================"
echo "TBCV Installation Script"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3.9+ required"; exit 1; }

# Create virtual environment (optional but recommended)
read -p "Create virtual environment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from example
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env to configure your installation"
fi

# Run startup check
echo ""
echo "Running startup validation..."
python startup_check.py

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "To start the server:"
echo "  python main.py --mode api --host 0.0.0.0 --port 8080"
echo ""
echo "Or with Docker:"
echo "  docker-compose up -d"
echo ""
echo "For more information, see QUICKSTART.md"
echo ""

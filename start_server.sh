#!/bin/bash
# Startup script for Infinity Research Portal

echo "∞ Infinity Research Portal - Starting Server ∞"
echo "=============================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Creating .env from .env.example..."
    cp .env.example .env
    echo "   Please edit .env and add your GitHub OAuth credentials"
    echo ""
fi

# Check if Python dependencies are installed
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Build research index
echo "Building research index..."
python3 build_research_index.py

echo ""
echo "Starting authentication server..."
echo "Server will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="

# Start the server
python3 auth_server.py

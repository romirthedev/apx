#!/bin/bash

# Cluely Launcher Script
# This script starts both the backend and frontend components

echo "🧠 Starting Cluely AI Assistant..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: Please run this script from the Cluely project root directory"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

if [ ! -d ".venv" ]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment and install Python dependencies
source .venv/bin/activate
if [ ! -f "backend/.installed" ]; then
    echo "Installing Python dependencies..."
    cd backend
    ../../../.venv/bin/pip install -r requirements.txt
    touch .installed
    cd ..
fi

# Start the application
echo "Starting Cluely..."
npm run dev

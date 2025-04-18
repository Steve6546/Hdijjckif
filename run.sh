#!/bin/bash

# Run script for All-Agents-App
# This script sets up the environment and runs the application

# Set up environment
echo "Setting up environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [ -d "venv/bin" ]; then
    # Linux/Mac
    source venv/bin/activate
elif [ -d "venv/Scripts" ]; then
    # Windows
    source venv/Scripts/activate
else
    echo "Error: Virtual environment not found"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create required directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p data
mkdir -p runtime/generated_projects
mkdir -p runtime/temp
mkdir -p runtime/logs

# Run the application
echo "Starting the application..."
python app.py

# Deactivate virtual environment
deactivate
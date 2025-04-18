#!/bin/bash

# Install script for All-Agents-App
# This script sets up the environment and installs all dependencies

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
pip install --upgrade pip
pip install -r requirements.txt

# Create required directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p data
mkdir -p runtime/generated_projects
mkdir -p runtime/temp
mkdir -p runtime/logs

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env || echo "# API Keys
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Site information
SITE_URL=https://your-site.com
SITE_NAME=Your Site Name

# Authentication
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
SQLITE_DB_PATH=logs/activity.db

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Server
HOST=0.0.0.0
PORT=12000

# Advanced AI
ADVANCED_AI_MODEL=google/gemini-2.5-pro-exp-03-25:free

# Project Settings
PROJECTS_DIR=runtime/generated_projects
TEMP_DIR=runtime/temp
LOGS_DIR=runtime/logs" > .env
fi

echo "Installation complete!"
echo "To run the application, use: ./run.sh"

# Deactivate virtual environment
deactivate
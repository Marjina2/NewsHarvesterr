#!/bin/bash

# News Scraper Dashboard - Startup Script
echo "Starting News Scraper Dashboard..."

# Install Python requirements if they don't exist
if [ ! -d "venv" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start the application
echo "Starting the server..."
npm run dev
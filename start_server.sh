#!/bin/bash

# Audio Denoiser API Startup Script

echo "🚀 Starting Audio Denoiser API Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "server/main.py" ]; then
    echo "❌ Please run this script from the denoiser-server directory"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if denoiser module is available
if [ ! -d "../denoiser" ]; then
    echo "❌ Denoiser module not found. Please make sure the denoiser directory is in the parent directory."
    exit 1
fi

# Start the server
echo "🎵 Starting server on http://localhost:8000"
echo "📖 API documentation will be available at http://localhost:8000/docs"
echo "🔄 Health check available at http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd server
python main.py 
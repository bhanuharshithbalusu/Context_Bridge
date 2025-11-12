#!/bin/bash

echo "======================================"
echo "🚀 CONTEXTBRIDGE PLAYGROUND STARTUP"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "playground_api.py" ]; then
    echo "❌ Error: Please run this script from the 'Cooontext bridge' directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: playground_api.py, test_translation.py"
    exit 1
fi

echo "📂 Current directory: $(pwd)"
echo "📝 Starting ContextBridge Playground API server..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

echo "🐍 Python version: $(python3 --version)"

# Check if virtual environment should be activated (optional)
if [ -d "venv" ]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
fi

# Install requirements if they don't exist
echo "🔧 Checking dependencies..."
pip3 install -q flask flask-cors 2>/dev/null || echo "⚠️  Note: Install flask and flask-cors if needed"

echo ""
echo "🎯 Starting the API server..."
echo "   - API will be available at: http://127.0.0.1:5000"
echo "   - Translation endpoint: http://127.0.0.1:5000/api/translate"
echo "   - Open your playground.html in a browser to use the frontend"
echo ""
echo "💡 Tip: The initial model loading may take 1-2 minutes"
echo "========================================"
echo ""

# Start the server
python3 playground_api.py

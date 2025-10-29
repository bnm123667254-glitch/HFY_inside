#!/bin/bash
# Startup script for Compliance Q&A System

set -e

echo "=================================="
echo "Compliance Q&A System Startup"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Dependencies not installed. Installing..."
    pip install -r requirements.txt
fi

# Check Milvus connection
echo ""
echo "Checking Milvus connection..."
python3 -c "
from pymilvus import connections
import os
from dotenv import load_dotenv

load_dotenv()
host = os.getenv('MILVUS_HOST', 'localhost')
port = int(os.getenv('MILVUS_PORT', 19530))

try:
    connections.connect(host=host, port=port)
    print('✓ Milvus connection successful')
    connections.disconnect('default')
except Exception as e:
    print(f'✗ Milvus connection failed: {e}')
    print('Please ensure Milvus is running')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "Tip: Start Milvus with Docker:"
    echo "  docker run -d --name milvus-standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest"
    exit 1
fi

# Start application
echo ""
echo "Starting application..."
echo "API will be available at http://localhost:8000"
echo "Swagger docs at http://localhost:8000/docs"
echo ""

python3 -m src.api.main

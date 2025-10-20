#!/bin/bash

# Start Local LLM Celery with NVIDIA GPU Acceleration
# This script starts the services using native Ollama with NVIDIA GPU support

set -e

echo "🚀 Starting Local LLM Celery with NVIDIA GPU Acceleration"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed!"
    echo ""
    echo "Please install Ollama first:"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    exit 1
fi

# Check if NVIDIA GPU is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA GPU not detected or nvidia-smi not found!"
    echo ""
    echo "Please ensure:"
    echo "  1. NVIDIA GPU is installed"
    echo "  2. NVIDIA drivers are installed"
    echo "  3. nvidia-smi command is available"
    echo ""
    exit 1
fi

# Check if llama3:8b model exists
if ! ollama list | grep -q "llama3:8b"; then
    echo "❌ Model llama3:8b not found!"
    echo ""
    echo "Pulling model..."
    ollama pull llama3:8b
    echo ""
fi

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Verify Ollama is accessible
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not accessible at http://localhost:11434"
    echo ""
    echo "Please start Ollama manually:"
    echo "  ollama serve"
    echo ""
    exit 1
fi

echo "✅ Ollama running at http://localhost:11434"
echo ""

# Show GPU information
echo "🎮 GPU Information:"
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader | while read -r line; do
    echo "    $line"
done
echo ""

# Build images
echo "🔨 Building Docker images..."
podman-compose -f docker-compose.gpu-nvidia.yml build
echo ""

# Start services (excluding Ollama - it's on host)
echo "🚀 Starting services (using host Ollama with NVIDIA GPU)..."
podman-compose -f docker-compose.gpu-nvidia.yml up -d
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check service status
echo "📊 Service Status:"
podman-compose -f docker-compose.gpu-nvidia.yml ps
echo ""

echo "✅ Services started successfully!"
echo ""
echo "🌐 Web interface: http://localhost:5001"
echo "📝 API endpoint: http://localhost:5001/analyze"
echo ""
echo "💡 GPU mode using NVIDIA GPU acceleration (10-50x faster than CPU)"
echo ""
echo "To stop services:"
echo "  podman-compose -f docker-compose.gpu-nvidia.yml down"
echo ""

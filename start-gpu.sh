#!/bin/bash
# Start services with GPU acceleration (native Ollama)

set -e

echo "🚀 Starting Local LLM Celery with GPU Acceleration"
echo "=================================================="
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Error: Ollama is not installed"
    echo "   Install with: brew install ollama"
    exit 1
fi

# Check if llama3:8b model exists
if ! ollama list | grep -q "llama3:8b"; then
    echo "📥 Model llama3:8b not found. Pulling..."
    ollama pull llama3:8b
fi

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "🔧 Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    echo "✅ Ollama started"
else
    echo "✅ Ollama already running"
fi

# Verify Ollama is accessible
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Error: Cannot connect to Ollama at http://localhost:11434"
    echo "   Make sure Ollama is running: ollama serve"
    exit 1
fi

echo "✅ Ollama accessible at http://localhost:11434"
echo ""

# Check GPU acceleration
echo "🎮 GPU Information:"
system_profiler SPDisplaysDataType | grep -E "Chipset Model|Metal" | head -2
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
podman-compose -f docker-compose.gpu.yml down 2>/dev/null || true

# Build and start services (without Ollama container)
echo "🔨 Building images..."
podman-compose -f docker-compose.gpu.yml build

echo "🚀 Starting services (using host Ollama with GPU)..."
podman-compose -f docker-compose.gpu.yml up -d

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service Status:"
podman-compose -f docker-compose.gpu.yml ps
echo ""
echo "🌐 Web UI: http://localhost:5001"
echo "📝 API: http://localhost:5001/analyze"
echo "🎮 Mode: GPU-Accelerated (Metal)"
echo "⚡ Expected speed: ~1 min per query (10-50x faster)"
echo ""
echo "📋 Useful commands:"
echo "  - View logs: podman logs worker -f"
echo "  - Stop: podman-compose -f docker-compose.gpu.yml down"
echo "  - Status: podman-compose -f docker-compose.gpu.yml ps"
echo ""

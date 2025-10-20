#!/bin/bash
# GPU/CPU Toggle Script for LLM Data Analyst
# Usage: ./start.sh [cpu|gpu]

set -e

MODE="${1:-cpu}"
MODE_UPPER=$(echo "$MODE" | tr '[:lower:]' '[:upper:]')

echo "🚀 Starting LLM Data Analyst in ${MODE_UPPER} mode..."

case "$MODE" in
  cpu)
    echo "✅ CPU-only mode (default)"
    echo "📊 Expected performance: ~5-10 tokens/sec, 4-7 min per query"
    podman-compose up -d
    ;;
  
  gpu)
    echo "🎮 GPU-accelerated mode"
    echo "⚡ Expected performance: ~50-100 tokens/sec, 30-60 sec per query"
    echo "⚠️  Requires: NVIDIA GPU with drivers installed"
    
    # Check for NVIDIA GPU
    if ! command -v nvidia-smi &> /dev/null; then
      echo "❌ ERROR: nvidia-smi not found. GPU mode requires NVIDIA drivers."
      echo "💡 Falling back to CPU mode..."
      podman-compose up -d
      exit 0
    fi
    
    echo "🔍 Detected GPU(s):"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    
    podman-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
    ;;
  
  *)
    echo "❌ Invalid mode: $MODE"
    echo "Usage: $0 [cpu|gpu]"
    echo ""
    echo "Examples:"
    echo "  $0          # Start in CPU mode (default)"
    echo "  $0 cpu      # Start in CPU mode"
    echo "  $0 gpu      # Start in GPU mode"
    exit 1
    ;;
esac

echo ""
echo "⏳ Waiting for services to start..."
sleep 3

echo ""
echo "🔍 Service Status:"
podman-compose ps

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Endpoints:"
echo "   Web UI:  http://localhost:5001/"
echo "   API:     http://localhost:5001/analyze"
echo "   Health:  http://localhost:5001/status/health"
echo "   Ollama:  http://localhost:11434"
echo ""
echo "📚 Documentation:"
echo "   README:   ./README.md"
echo "   Postman:  ./POSTMAN.md"
echo "   Web UI:   Open http://localhost:5001/ in browser"
echo ""
echo "🛑 To stop: podman-compose down"

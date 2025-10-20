#!/bin/bash
# Quick fix for Podman memory issue

echo "🔧 Podman Memory Fix"
echo "===================="
echo ""

# Show current setup
echo "📊 Current Podman Machine:"
podman machine list
echo ""

# Get current memory
current_mem=$(podman machine list | grep 'podman-machine-default' | awk '{print $6}')
echo "Current memory allocation: $current_mem"
echo ""

if [[ "$current_mem" == "2GiB" ]]; then
    echo "⚠️  WARNING: Only 2 GB allocated - llama3:8b needs 4.6 GB minimum!"
    echo ""
    echo "Options:"
    echo ""
    echo "1️⃣  Recreate Podman machine with 8 GB (RECOMMENDED)"
    echo "   ⚠️  This will delete all containers and images!"
    echo "   Commands:"
    echo "   podman machine stop"
    echo "   podman machine rm podman-machine-default"
    echo "   podman machine init --memory 8192 --cpus 4 --disk-size 100"
    echo "   podman machine start"
    echo ""
    echo "2️⃣  Use a smaller model (fits in 2 GB)"
    echo "   Update worker.py to use llama3:3b instead of llama3:8b"
    echo "   Memory needed: ~2 GB (will fit)"
    echo ""
    echo "3️⃣  Run Ollama natively on host (no Podman limit)"
    echo "   brew install ollama"
    echo "   ollama serve &"
    echo "   Update OLLAMA_URL to point to host"
    echo ""
else
    echo "✅ Memory looks good: $current_mem"
    echo ""
    echo "If you still see memory errors, check:"
    echo "  podman exec ollama free -h"
fi

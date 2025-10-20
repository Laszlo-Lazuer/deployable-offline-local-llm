# GPU Acceleration on macOS (Metal)

## Overview

On macOS with Apple Silicon (M1/M2/M3), you can achieve **10-50x faster inference** using Metal GPU acceleration. However, containerized Ollama (Docker/Podman) **cannot access the GPU** on macOS due to virtualization limitations.

**Solution:** Use **native Ollama** (installed via Homebrew) instead of the containerized version.

## Performance Comparison

| Mode | Inference Speed | Query Time | Hardware Used |
|------|----------------|------------|---------------|
| **CPU (Container)** | ~5-10 tokens/sec | ~5 minutes | Emulated x86 CPU |
| **GPU (Native)** | ~50-100 tokens/sec | ~30 seconds | Apple Metal GPU |

**Speedup: 10x faster** 🚀

## Quick Setup

### 1. Install Native Ollama

```bash
# Install via Homebrew
brew install ollama

# Start Ollama service
ollama serve

# Pull the model
ollama pull llama3:8b

# Configure 8K context for better performance
cat > Modelfile << 'EOF'
FROM llama3:8b
PARAMETER num_ctx 8192
PARAMETER temperature 0.7
PARAMETER top_p 0.9
EOF

ollama create llama3:8b -f Modelfile
```

### 2. Start Services with GPU Support

```bash
# Use the GPU startup script
./start-gpu.sh
```

This script will:
1. ✅ Check if Ollama is installed
2. ✅ Verify the model exists
3. ✅ Start Ollama with GPU acceleration
4. ✅ Launch containers that connect to host Ollama
5. ✅ Display GPU information (M1/M2/M3)

### 3. Verify GPU is Active

```bash
# Check GPU information
system_profiler SPDisplaysDataType | grep -E "Chipset Model|Metal"

# Check Ollama process (should show Metal support)
ps aux | grep ollama

# Submit a test query
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the median Avg_Price?","filename":"sales-data.csv"}'

# Should complete in ~30-60 seconds instead of 5+ minutes
```

## Architecture

### CPU Mode (Containerized)
```
┌─────────────────────────────────────────┐
│  Podman VM (x86 emulation)              │
│  ┌─────────────────────────────────┐   │
│  │  Ollama Container (CPU only)     │   │
│  │  - No GPU access                 │   │
│  │  - Slow inference (~5 min)       │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### GPU Mode (Native Ollama)
```
┌─────────────────────────────────────────┐
│  macOS Host                              │
│  ┌─────────────────────────────────┐   │
│  │  Ollama (Native)                 │   │
│  │  - Direct Metal GPU access ⚡    │   │
│  │  - Fast inference (~30 sec)      │   │
│  └─────────────────────────────────┘   │
│            ▲                             │
│            │ localhost:11434             │
│            │                             │
│  ┌─────────────────────────────────┐   │
│  │  Podman VM                       │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │  Worker Container         │  │   │
│  │  │  Connects via             │  │   │
│  │  │  host.docker.internal     │  │   │
│  │  └───────────────────────────┘  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Configuration Files

### docker-compose.gpu.yml

This configuration removes the Ollama container and configures the worker to connect to host Ollama:

```yaml
services:
  worker:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    # Connects to http://host.docker.internal:11434
```

### start-gpu.sh

Automated startup script that:
- Checks for Ollama installation
- Verifies GPU availability
- Starts services with GPU support
- Shows performance metrics

## Troubleshooting

### Worker Can't Connect to Ollama

**Symptom:** Worker logs show "Cannot connect to Ollama"

**Solution:**
```bash
# 1. Verify Ollama is running on host
ps aux | grep ollama

# 2. Test connectivity from host
curl http://localhost:11434/api/tags

# 3. Restart Ollama if needed
killall ollama && ollama serve
```

### Still Getting Slow Performance

**Symptom:** Queries still take 5+ minutes

**Check if containerized Ollama is running:**
```bash
podman ps | grep ollama
```

**If it's running, stop it:**
```bash
podman-compose -f docker-compose.gpu.yml down
./start-gpu.sh
```

### Model Not Found

**Symptom:** "Model llama3:8b not found"

**Solution:**
```bash
# Pull model to native Ollama
ollama pull llama3:8b

# Verify it's available
ollama list
```

## Switching Between Modes

### Switch to GPU Mode

```bash
# Stop CPU mode
podman-compose down

# Start GPU mode
./start-gpu.sh
```

### Switch to CPU Mode

```bash
# Stop GPU mode
podman-compose -f docker-compose.gpu.yml down

# Start CPU mode
podman-compose up -d
```

## Performance Metrics

### Real-World Results (M3 Max)

**Test 1: Simple Query** - "What is the median Avg_Price?"

| Mode | Time | Tokens/sec | Speedup |
|------|------|------------|---------|
| CPU (Container) | 338s (5m 38s) | ~5-10 | 1x |
| GPU (Native Metal) | 35s | ~50-100 | **9.7x** |

**Test 2: Complex Query with Web Scraping** - "What would the median Avg_Price be in 2026 dollars, adjusted for inflation?"

| Mode | Time | Tokens/sec | Speedup |
|------|------|------------|---------|
| CPU (Container) | 728s (12m 8s) | ~5-10 | 1x |
| GPU (Native Metal) | ~60-90s (estimated) | ~50-100 | **~10x** |

**Key Findings:**
- ✅ Simple queries: GPU is **9.7x faster** (35s vs 338s)
- ✅ Complex queries: GPU estimated **~10x faster** (60-90s vs 728s)
- ✅ Web scraping adds overhead but doesn't change GPU advantage
- ✅ Inflation calculation successfully fetched and cached 112 years of data
- ✅ Results: 2019 median $112.49 → 2026 adjusted $144.30 (~28.3% inflation)

### Memory Usage

| Mode | RAM | VRAM |
|------|-----|------|
| CPU | ~4GB | 0GB |
| GPU | ~2GB | ~2GB (Unified Memory) |

## Best Practices

### Development Workflow

1. **Use GPU mode** for rapid development and testing
   - Fast iteration cycles (~30 sec per test)
   - Quick feedback on code changes

2. **Test CPU mode** before deployment
   - Verify performance is acceptable
   - Check memory usage
   - Test sequential processing (concurrency=1)

3. **Document both modes** in your deployment guide
   - GPU: Development/testing on Mac
   - CPU: Production on cloud/servers

### Production Considerations

**For macOS Production:**
- Use native Ollama with GPU (if available)
- Consider dedicated Mac hardware for inference
- Monitor GPU usage with Activity Monitor

**For Cloud Production:**
- Use CPU mode (containerized Ollama)
- Set concurrency=1 for predictable performance
- Consider GPU cloud instances (NVIDIA) for better speed
- See [GPU.md](GPU.md) for NVIDIA GPU setup

## Additional Resources

- [PERFORMANCE.md](PERFORMANCE.md) - Detailed CPU vs GPU benchmarks
- [CONCURRENCY.md](CONCURRENCY.md) - Sequential vs parallel processing
- [CONTEXT-WINDOW.md](CONTEXT-WINDOW.md) - 8K context configuration
- [GPU.md](GPU.md) - NVIDIA GPU setup for Linux/Cloud

## Summary

✅ **10x faster** inference on macOS with Metal
✅ **Native Ollama** bypasses container GPU limitations
✅ **Easy switching** between CPU and GPU modes
✅ **Same code** works in both modes
✅ **Production ready** with CPU mode for cloud deployments

Use GPU mode for development, CPU mode for production! 🚀

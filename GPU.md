# GPU Acceleration Guide

This guide explains how to enable GPU acceleration for significantly faster LLM inference.

## 🚀 Performance Comparison

| Mode | Speed | Query Time | Hardware Required |
|------|-------|------------|-------------------|
| **CPU** | ~5-10 tokens/sec | 4-7 minutes | Any x86_64/ARM64 CPU |
| **GPU** | ~50-100 tokens/sec | 30-60 seconds | NVIDIA GPU |

**Speed improvement: 10-50x faster** ⚡

---

## 📋 Requirements

### For GPU Mode:
- ✅ NVIDIA GPU (GTX 1060 or better, 6GB+ VRAM recommended)
- ✅ NVIDIA drivers installed
- ✅ `nvidia-smi` command available
- ✅ Linux host (or WSL2 on Windows)

### Verify GPU Access:
```bash
nvidia-smi
```

Expected output:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 525.xx.xx    Driver Version: 525.xx.xx    CUDA Version: 12.x   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0  On |                  N/A |
|...
```

---

## 🎮 Using GPU Mode

### Option 1: Using the Start Script (Recommended)

```bash
# Start with GPU acceleration
./start.sh gpu
```

This will:
1. Check for NVIDIA GPU
2. Display detected GPU(s)
3. Start all services with GPU support
4. Fall back to CPU if GPU not available

### Option 2: Manual podman-compose

```bash
# Start with GPU
podman-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# Stop
podman-compose down
```

---

## 💻 Using CPU Mode (Default)

### Option 1: Using the Start Script

```bash
# Start in CPU mode
./start.sh cpu

# Or just (CPU is default)
./start.sh
```

### Option 2: Manual podman-compose

```bash
# Start with CPU-only
podman-compose up -d

# Stop
podman-compose down
```

---

## 🔍 Verify GPU is Being Used

After starting in GPU mode:

### 1. Check Ollama is using GPU
```bash
podman exec ollama nvidia-smi
```

### 2. Monitor GPU usage during a query
```bash
# In one terminal
watch -n 1 nvidia-smi

# In another terminal, submit a query
curl -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is the median Avg_Price?","filename":"sales-data.csv"}' \
  http://localhost:5001/analyze
```

You should see GPU utilization spike to 80-100% during inference.

### 3. Check worker logs
```bash
podman logs worker --tail 50
```

Look for faster response times in the logs.

---

## 📊 Expected Performance

### CPU Mode (llama3:8b)
- Model loading: ~5-6 seconds
- Token generation: ~5-10 tokens/sec
- Query time: 4-7 minutes
- Memory: ~6GB RAM

### GPU Mode (llama3:8b)
- Model loading: ~2-3 seconds
- Token generation: ~50-100 tokens/sec (depends on GPU)
- Query time: 30-90 seconds
- Memory: ~6GB VRAM + 2GB RAM

### GPU Performance by Model

| GPU | VRAM | llama3:8b Speed | llama3:3b Speed |
|-----|------|----------------|----------------|
| RTX 4090 | 24GB | ~100 tokens/sec | ~150 tokens/sec |
| RTX 3080 | 10GB | ~60 tokens/sec | ~90 tokens/sec |
| RTX 3060 | 12GB | ~40 tokens/sec | ~60 tokens/sec |
| GTX 1080 Ti | 11GB | ~30 tokens/sec | ~50 tokens/sec |
| GTX 1060 | 6GB | ~15 tokens/sec | ~25 tokens/sec |

---

## 🐛 Troubleshooting

### "nvidia-smi not found"
**Issue:** NVIDIA drivers not installed

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install nvidia-driver-525

# Fedora/RHEL
sudo dnf install nvidia-driver

# Verify
nvidia-smi
```

### "Failed to initialize NVML"
**Issue:** Podman can't access GPU devices

**Solution:** Make sure you're running as root or in the correct group:
```bash
# Check your user is in the right groups
groups

# Add to video/render group if needed
sudo usermod -a -G video $USER
sudo usermod -a -G render $USER

# Logout and login again
```

### GPU not detected in container
**Issue:** GPU devices not mapped

**Solution:** Check the `docker-compose.gpu.yml` has correct device mappings:
```yaml
devices:
  - /dev/nvidia0:/dev/nvidia0
  - /dev/nvidiactl:/dev/nvidiactl
  - /dev/nvidia-uvm:/dev/nvidia-uvm
```

### Out of memory errors
**Issue:** Model too large for GPU VRAM

**Solutions:**
1. Use smaller model (llama3:3b uses ~3GB VRAM)
2. Reduce context window in worker.py
3. Use CPU mode

### Slower than expected
**Issue:** GPU not fully utilized

**Check:**
```bash
# Monitor GPU usage
nvidia-smi dmon

# Check if CPU is bottleneck
htop
```

**Solutions:**
- Ensure no other GPU-intensive processes running
- Check GPU drivers are up to date
- Verify PCIe bandwidth is sufficient

---

## 🔄 Switching Between Modes

### Stop current mode and switch:
```bash
# Stop everything
podman-compose down

# Start in different mode
./start.sh gpu   # or ./start.sh cpu
```

### No data loss
Data in `/data` directory persists across mode switches.

---

## 🎯 Best Practices

1. **Use GPU for production** - 10-50x faster response times
2. **Use CPU for development** - Works anywhere, no GPU required
3. **Monitor VRAM usage** - Ensure you don't exceed GPU memory
4. **Keep drivers updated** - Better performance and stability
5. **Benchmark your setup** - Performance varies by GPU model

---

## 📚 Additional Resources

- **Main README**: [README.md](README.md)
- **Docker Compose GPU docs**: https://docs.docker.com/compose/gpu-support/
- **Ollama GPU support**: https://github.com/ollama/ollama#gpu-support
- **NVIDIA Container Toolkit**: https://github.com/NVIDIA/nvidia-container-toolkit

---

## 💡 Pro Tips

1. **Pre-warm the model**: Run a quick test query after starting to load the model into VRAM
2. **Use persistent volumes**: Keep Ollama data volume to avoid re-downloading models
3. **Batch queries**: Multiple queries benefit from model already in VRAM
4. **Monitor temperature**: Keep GPU cool for sustained performance

---

**Ready to go fast?** Run `./start.sh gpu` and enjoy 10-50x speedup! ⚡

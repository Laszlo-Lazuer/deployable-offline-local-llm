# Start Script Quick Reference

## 🚀 Usage

```bash
./start.sh [cpu|gpu]
```

## 📋 Commands

| Command | Description | Performance |
|---------|-------------|-------------|
| `./start.sh` | Start in CPU mode (default) | ~5-10 tokens/sec, 4-7 min per query |
| `./start.sh cpu` | Explicitly start in CPU mode | ~5-10 tokens/sec, 4-7 min per query |
| `./start.sh gpu` | Start with GPU acceleration | ~50-100 tokens/sec, 30-90 sec per query |

## 🛑 Stop Services

```bash
podman-compose down
```

## 📊 Check Status

```bash
# See running containers
podman-compose ps

# Check logs
podman logs worker --tail 50
podman logs web-app --tail 20
podman logs ollama --tail 20

# Test API
curl http://localhost:5001/status/health
```

## 🔄 Restart Services

```bash
# Stop
podman-compose down

# Start again (pick mode)
./start.sh cpu   # or ./start.sh gpu
```

## 📍 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Web UI** | http://localhost:5001/ | Interactive web interface |
| **API** | http://localhost:5001/analyze | Submit analysis requests |
| **Health** | http://localhost:5001/status/health | Health check endpoint |
| **Ollama** | http://localhost:11434 | LLM server |
| **Streaming** | http://localhost:5001/status/{task_id}/stream | Real-time progress |

## 🎯 What the Script Does

### CPU Mode:
1. ✅ Starts Redis (message queue)
2. ✅ Starts Ollama (LLM server, CPU-only)
3. ✅ Starts Flask web-app (API + UI)
4. ✅ Starts Celery worker (task processor)

### GPU Mode:
1. ✅ Checks for NVIDIA GPU (`nvidia-smi`)
2. ✅ Shows detected GPU info
3. ✅ Starts all services with GPU access
4. ✅ Falls back to CPU if GPU unavailable

## 💡 Quick Examples

### Start and Test
```bash
# Start services
./start.sh

# Wait a moment for startup
sleep 5

# Test health
curl http://localhost:5001/status/health

# Open web UI
open http://localhost:5001/
```

### Switch from CPU to GPU
```bash
# Stop current
podman-compose down

# Start with GPU
./start.sh gpu
```

### Check GPU Usage (GPU mode only)
```bash
# Monitor GPU in real-time
watch -n 1 nvidia-smi

# Check GPU in Ollama container
podman exec ollama nvidia-smi
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check for port conflicts
lsof -i :5001
lsof -i :11434

# View error logs
podman-compose logs
```

### GPU not working
```bash
# Verify nvidia-smi works
nvidia-smi

# Check GPU devices
ls -la /dev/nvidia*

# See GPU.md for detailed troubleshooting
```

### Slow responses
```bash
# Check if using GPU when expected
podman exec ollama nvidia-smi  # Should show GPU usage

# Check CPU usage
htop

# View worker logs
podman logs worker --tail 100
```

## 📚 More Information

- **GPU Guide**: [GPU.md](GPU.md)
- **API Reference**: [README.md](README.md)
- **Postman Collection**: [POSTMAN.md](POSTMAN.md)
- **Web UI**: Open http://localhost:5001/

---

**Need help?** Check the logs: `podman logs worker --tail 50`

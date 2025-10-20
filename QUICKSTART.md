# Quick Start Guide

This guide will get you up and running with the Local LLM Celery service in under 10 minutes.

## Prerequisites Check

Before starting, ensure you have:

```bash
# Check Podman is installed
podman --version

# Check Ollama is installed
ollama --version

# Check if llama3:8b model is available
ollama list | grep llama3

# Check Podman machine has adequate memory (8GB minimum)
podman machine list
```

**⚠️ Important**: The Podman machine must have **at least 8GB RAM** allocated. The llama3:8b model requires 4.6GB, and you need additional memory for containers and build processes.

If your Podman machine has less than 8GB:
```bash
# Stop and remove existing machine
podman machine stop
podman machine rm

# Create new machine with 8GB RAM
podman machine init --memory 8192 --cpus 4 --disk-size 100
podman machine start
```

If anything else is missing:
- **Podman**: `brew install podman` (macOS) or follow [docs](https://podman.io/getting-started/installation)
- **Ollama**: `brew install ollama` (macOS) or visit [ollama.ai](https://ollama.ai)
- **llama3:8b**: `ollama pull llama3:8b`

## 5-Step Setup

### 1. Start Ollama

```bash
# Start Ollama in the background
ollama serve &

# Or start it in a separate terminal
ollama serve
```

Verify it's running:
```bash
curl http://localhost:11434/api/tags
```

### 2. Clone and Build

```bash
# Clone the repository
git clone https://github.com/Laszlo-Lazuer/local-llm-celery.git
cd local-llm-celery

# Build the image (takes 10-15 minutes first time)
make build
```

### 3. Start All Services

```bash
# This creates network, starts Redis, Flask API, and Celery worker
make start
```

Wait ~10 seconds for all services to initialize.

### 4. Verify Setup

```bash
# Check all containers are running
make ps

# Should show: redis, llm-app, llm-worker
```

### 5. Run a Test Query

```bash
# Submit an analysis task
make test

# Or manually:
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the median Avg_Price?", "filename": "sales-data.csv"}'
```

You'll get a response like:
```json
{"task_id": "abc-123-def"}
```

Check the result:
```bash
curl http://localhost:5001/status/abc-123-def
```

## Monitoring

Watch the worker process your query:
```bash
make logs-worker
```

You should see:
1. Loading llama3:8b model
2. LLM generating Python code
3. Code execution with pandas
4. Final result: "The median Avg_Price is: 112.48"

## Common Commands

```bash
# Stop all services
make stop

# Restart all services
make restart

# View API logs
make logs-app

# View worker logs
make logs-worker

# Clean up everything
make clean

# Rebuild from scratch
make rebuild

# Open shell in worker container
make shell-worker
```

## Troubleshooting

### Problem: "Cannot connect to Ollama"

**Solution**: Ensure Ollama is running on your host:
```bash
ps aux | grep ollama
curl http://localhost:11434/api/tags
```

### Problem: Worker shows errors about missing modules

**Solution**: Rebuild the image:
```bash
make rebuild
```

### Problem: Port 5001 already in use

**Solution**: Either stop the service using that port, or edit the Makefile/command to use a different port:
```bash
# In Makefile, change:
# -p 5001:5000
# to:
# -p 5002:5000
```

### Problem: Task stays in PENDING state

**Solution**: Check worker logs:
```bash
make logs-worker
```

Ensure worker is connected to Redis and can reach Ollama.

## Next Steps

1. **Try more queries**: See example queries in the main README.md
2. **Add your own data**: Place CSV files in the `data/` directory
3. **Integrate into your app**: See Python client examples in README.md
4. **Scale up**: Deploy to Kubernetes (see k8s/README.md)

## Getting Help

- Check the full README.md for detailed documentation
- View logs: `make logs-worker` or `make logs-app`
- Open an issue on GitHub if you encounter problems

## Clean Shutdown

When you're done:

```bash
# Stop all containers
make stop

# Or completely remove everything
make clean

# Stop Ollama (if you started it in background)
killall ollama
```

---

**🎉 Congratulations!** You now have a working AI-powered data analysis service!

Try asking complex questions like:
- "What is the correlation between Attendance and Revenue?"
- "Which city had the highest average ticket price?"
- "Show me the total revenue by country"

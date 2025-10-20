# Fixing the 241 MB Memory Cap Issue

## Problem

The Ollama container reports only 241 MB available memory, causing the error:
```
model requires more system memory (4.6 GiB) than is available (241.5 MiB)
```

## Root Cause

The **Podman machine** is configured with only **2 GB RAM**:
```bash
podman machine list
# Shows: MEMORY = 2GiB
```

Inside the machine:
- Total: 1.9 GB
- Used: 1.8 GB (by system + containers)
- Free: Only 35-99 MB

The llama3:8b model requires **4.6 GB** to run, so it can't fit.

## Solution: Increase Podman Machine Memory

### Option 1: Recreate Podman Machine with More Memory (Recommended)

```bash
# Stop and remove existing machine
podman machine stop
podman machine rm podman-machine-default

# Create new machine with 8GB RAM (adjust based on your system)
podman machine init --memory 8192 --cpus 4 --disk-size 100

# Start the new machine
podman machine start

# Verify
podman machine list
# Should show: MEMORY = 8GiB
```

**Note:** This will delete all existing containers and images. Back up any important data first!

### Option 2: Set Memory for Existing Machine (if supported)

Some Podman versions support setting memory on existing machines:

```bash
# Stop the machine
podman machine stop

# Try to set memory (may not work on all versions)
podman machine set --memory 8192

# Start the machine
podman machine start

# Verify
podman machine list
```

### Option 3: Use a Smaller Model

If you can't increase memory, use a smaller model:

```bash
# Instead of llama3:8b (4.6 GB), use:
podman exec ollama ollama pull llama3:3b  # ~2 GB
# or
podman exec ollama ollama pull phi3:mini  # ~2.3 GB
# or
podman exec ollama ollama pull tinyllama  # ~637 MB
```

Then update `worker.py`:
```python
# Change from:
llm = Ollama(model="llama3:8b", base_url=ollama_url)

# To:
llm = Ollama(model="llama3:3b", base_url=ollama_url)  # or phi3:mini, etc.
```

## Recommended Setup

For this project, recommended Podman machine configuration:

```bash
podman machine init \
  --memory 8192 \    # 8 GB RAM (for llama3:8b)
  --cpus 4 \         # 4 CPUs
  --disk-size 100    # 100 GB disk
```

### Memory Requirements by Model

| Model | Memory Needed | Performance |
|-------|---------------|-------------|
| llama3:8b | ~4.6 GB | Best quality (default) |
| llama3:3b | ~2.0 GB | Good quality, faster |
| phi3:mini | ~2.3 GB | Good quality, efficient |
| tinyllama | ~637 MB | Basic quality, very fast |

## After Fixing

Once you've increased the Podman machine memory:

1. **Rebuild and restart services:**
   ```bash
   cd /Users/squirrel/Documents/repos/ai/local-llm-celery
   podman-compose down
   podman-compose up -d
   ```

2. **Wait for model download:**
   ```bash
   # Check model is downloading
   podman logs worker --follow
   
   # Or check Ollama directly
   podman exec ollama ollama list
   ```

3. **Run tests:**
   ```bash
   ./test-multi-format.sh
   ```

## Verification

Check available memory after restart:

```bash
# Check Podman machine
podman machine list
# Should show 8GiB or more

# Check inside Ollama container
podman exec ollama free -h
# Should show ~7.5 GB total

# Check model loads
podman exec ollama ollama run llama3:8b "test"
# Should respond (not error about memory)
```

## Why 241 MB Specifically?

With a 2 GB Podman machine:
- Total: ~1.9 GB
- Podman system overhead: ~200 MB
- Redis container: ~50 MB
- Ollama base: ~1.4 GB
- Web-app container: ~150 MB
- Worker container: ~150 MB
- **Remaining: ~35-240 MB** ← This is what you're seeing

The llama3:8b model needs 4.6 GB just for itself, which is more than the entire machine has!

## Alternative: Use External Ollama

If you can't allocate enough memory to Podman, run Ollama natively on your host:

```bash
# Install Ollama on macOS
brew install ollama

# Start Ollama
ollama serve &

# Pull model
ollama pull llama3:8b

# Update docker-compose.yml to remove Ollama service
# and point to host:
# OLLAMA_URL=http://host.docker.internal:11434

# Or if using podman-compose:
# OLLAMA_URL=http://10.0.2.2:11434
```

This way Ollama uses your host's full memory, not limited by Podman machine.

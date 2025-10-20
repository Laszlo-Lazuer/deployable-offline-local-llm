# Troubleshooting Guide

This guide covers common issues you may encounter when running the Local LLM Celery system and provides step-by-step solutions based on real debugging sessions.

## Table of Contents

1. [Build Issues](#build-issues)
2. [Memory Issues](#memory-issues)
3. [Container Issues](#container-issues)
4. [LLM/Model Issues](#llmmodel-issues)
5. [Network Issues](#network-issues)
6. [File Loading Issues](#file-loading-issues)
7. [Task Execution Issues](#task-execution-issues)
8. [Diagnostic Commands](#diagnostic-commands)

---

## Build Issues

### Issue: Container Build Fails with Exit 137 (OOM)

**Symptoms:**
```
STEP 6/8: RUN python -m pip install --no-cache-dir -r requirements.txt
Killed
Error: building at STEP "RUN python -m pip install --no-cache-dir -r requirements.txt": 
while running runtime: exit status 137
```

**Cause:** Podman machine has insufficient memory. The build process (especially `pip install`) requires significant memory.

**Solution:**

1. **Check current Podman machine memory:**
```bash
podman machine list
```

Look for the memory allocation (should be 8GB minimum):
```
NAME                     VM TYPE     CREATED      LAST UP            CPUS        MEMORY      DISK SIZE
podman-machine-default*  qemu        2 weeks ago  Currently running  4           8GiB        100GiB
```

2. **If memory < 8GB, recreate the Podman machine:**
```bash
# Stop and remove existing machine
podman machine stop
podman machine rm

# Create new machine with 8GB RAM
podman machine init --memory 8192 --cpus 4 --disk-size 100
podman machine start

# Verify
podman machine list
```

3. **Rebuild the image:**
```bash
podman build -t local-llm-celery:dev --format docker .
```

**Prevention:** Always allocate at least 8GB RAM to the Podman machine when working with LLMs.

**Related:** See [FIX-MEMORY-ISSUE.md](FIX-MEMORY-ISSUE.md) for detailed memory troubleshooting.

---

### Issue: Build Uses Cached Layers (Changes Not Applied)

**Symptoms:**
- You modify a file (e.g., `worker.py`)
- Rebuild the image
- Changes don't appear in the container

**Cause:** Docker/Podman uses layer caching. If `COPY . .` doesn't detect changes, it uses the cached layer.

**Solution:**

1. **Force clean build without cache:**
```bash
podman build --no-cache -t local-llm-celery:dev --format docker .
```

2. **Or rebuild specific service with podman-compose:**
```bash
podman-compose build --no-cache worker
```

3. **Verify the change is in the image:**
```bash
# Start a temporary container
podman run -it --rm local-llm-celery:dev /bin/bash

# Inside container, check the file
cat /app/worker.py | grep "ALWAYS start your code"
```

**Prevention:** Use `--no-cache` when you're sure files have changed but the build seems to skip them.

---

### Issue: I/O Error During Build

**Symptoms:**
```
Error: mounting new container: creating overlay mount: input/output error
```

**Cause:** Podman machine filesystem corruption or stuck processes.

**Solution:**

1. **Restart the Podman machine:**
```bash
podman machine stop
sleep 3
podman machine start
```

2. **If that doesn't work, check for stuck processes:**
```bash
# On macOS
ps aux | grep podman

# Look for processes like:
# - vfkit
# - gvproxy
```

3. **Kill stuck processes (if found):**
```bash
# Replace PID with actual process IDs
kill -9 <PID1> <PID2>
```

4. **Restart machine and try build again:**
```bash
podman machine start
podman build -t local-llm-celery:dev --format docker .
```

**Prevention:** Cleanly stop containers before stopping the machine (`podman-compose down` before `podman machine stop`).

---

## Memory Issues

### Issue: Model Requires 4.6 GiB, Only XXX MiB Available

**Symptoms:**
```
Error: llama runner process has terminated: model requires 4.6 GiB, only 241.5 MiB available
```

**Cause:** Podman machine total RAM is too low. Even if containers have no memory limits, the VM itself limits available memory.

**Diagnosis:**

1. **Check Podman machine allocation:**
```bash
podman machine list
```

2. **Check memory inside container:**
```bash
podman exec worker free -h
```

3. **Check container memory limits:**
```bash
podman inspect worker | grep -i memory
```

**Solution:** See "Container Build Fails with Exit 137" above - same solution (recreate machine with 8GB).

**Why:** The llama3:8b model requires ~4.6GB RAM minimum. With system overhead, you need at least 8GB total VM memory.

---

### Issue: Worker Container Crashes with OOM

**Symptoms:**
```
podman ps -a
# worker shows "Exited (137)"
```

**Diagnosis:**
```bash
# Check worker logs
podman logs worker --tail 100

# Look for:
# - "Killed"
# - "OOMKilled"
# - Memory allocation errors
```

**Solution:**

1. **Increase Podman machine memory** (see above)

2. **Or use smaller model:**
```bash
# In another terminal
ollama pull phi3:mini  # ~2.3GB instead of 4.6GB

# Update worker to use smaller model
# (or let it fall back to smaller model if llama3 fails)
```

3. **Or run Ollama outside containers:**
- See [OLLAMA-DEPLOYMENT.md](OLLAMA-DEPLOYMENT.md) for external Ollama setup

---

## Container Issues

### Issue: Containers Won't Start After Rebuild

**Symptoms:**
```bash
podman-compose up -d
# Containers start but immediately exit
```

**Diagnosis:**

1. **Check container status:**
```bash
podman ps -a
```

2. **Check logs for each service:**
```bash
podman logs redis
podman logs ollama
podman logs web-app
podman logs worker
```

**Solution:**

1. **Clean up old containers:**
```bash
podman-compose down
podman container prune -f
```

2. **Remove old images (if needed):**
```bash
podman image prune -a -f
```

3. **Rebuild and restart:**
```bash
podman-compose build
podman-compose up -d
```

4. **Verify all running:**
```bash
podman ps
# Should show 4 containers: redis, ollama, web-app, worker
```

---

### Issue: Port Already in Use

**Symptoms:**
```
Error: rootlessport cannot expose privileged port 5001
# or
bind: address already in use
```

**Diagnosis:**
```bash
# Check what's using the port
lsof -nP -iTCP:5001 -sTCP:LISTEN
```

**Solution:**

**Option 1: Stop the conflicting service**
```bash
# If it's an old container
podman ps -a | grep 5001
podman stop <container-id>
podman rm <container-id>

# If it's another process
# Kill the process using the port
kill -9 <PID>
```

**Option 2: Use a different port**
```yaml
# Edit docker-compose.yml
web-app:
  ports:
    - "5002:5000"  # Changed from 5001:5000
```

Then access API at `http://localhost:5002` instead.

---

### Issue: Container Can't Connect to Ollama

**Symptoms:**
```
# In worker logs:
ConnectionError: Failed to connect to Ollama at http://host.docker.internal:11434
```

**Diagnosis:**

1. **Check if Ollama is running:**
```bash
# On your host machine
curl http://localhost:11434/api/tags
```

2. **Check from inside worker container:**
```bash
podman exec worker curl http://host.docker.internal:11434/api/tags
```

**Solution:**

**If Ollama isn't running on host:**
```bash
# Start Ollama
ollama serve

# In another terminal, verify
curl http://localhost:11434/api/tags
```

**If Ollama is running but worker can't reach it:**

1. **Check network connectivity:**
```bash
# From inside worker container
podman exec worker ping host.docker.internal
podman exec worker curl -v http://host.docker.internal:11434/api/tags
```

2. **If using Podman on Linux, use `host.containers.internal` instead:**
```yaml
# In docker-compose.yml
environment:
  OLLAMA_HOST: "http://host.containers.internal:11434"
```

3. **Or run Ollama in cluster** (see OLLAMA-DEPLOYMENT.md Option 2)

---

## LLM/Model Issues

### Issue: Model Not Found

**Symptoms:**
```
# In worker logs:
Error: model 'llama3:8b' not found
```

**Diagnosis:**
```bash
# Check available models
ollama list
```

**Solution:**
```bash
# Pull the model
ollama pull llama3:8b

# Verify
ollama list | grep llama3
```

**Alternative models if space/memory constrained:**
```bash
# Smaller models
ollama pull phi3:mini      # ~2.3GB
ollama pull tinyllama      # ~637MB
ollama pull gemma:2b       # ~1.4GB
```

---

### Issue: LLM Generates Code But Doesn't Import Modules

**Symptoms:**
```python
# In task result:
NameError: name 'load_file' is not defined
```

**Cause:** The LLM forgot to include the import statement in the generated code.

**Diagnosis:**
```bash
# Check worker logs to see generated code
podman logs worker --tail 100

# Look for code execution, check if import is present
```

**Solution:**

**Immediate fix - Better prompt (already implemented):**
The worker prompt now explicitly says:
```
2. ALWAYS start your code by importing the file loader:
   
   from file_loader import load_file
```

**For users - Be more explicit in questions:**
```bash
# Instead of:
"What is the total sales from the TSV file?"

# Try:
"Load the TSV file using load_file() after importing it from file_loader, then calculate total sales"
```

**Check if fix is deployed:**
```bash
podman exec worker grep -A 5 "ALWAYS start your code" /app/worker.py
# Should show the explicit import instruction
```

**If not deployed, rebuild:**
```bash
podman-compose down
podman build --no-cache -t local-llm-celery:dev --format docker .
podman-compose up -d
```

---

### Issue: Task Stays in PENDING State Forever

**Symptoms:**
```bash
curl http://localhost:5001/status/<task-id>
# Returns: {"status": "PENDING", "task_id": "..."}
# Never completes
```

**Diagnosis:**

1. **Check worker is running:**
```bash
podman ps | grep worker
```

2. **Check worker logs:**
```bash
podman logs worker -f
# Look for:
# - Task received
# - Code generation started
# - Any errors
```

3. **Check Redis connection:**
```bash
podman exec worker celery -A worker.celery_app inspect active
```

**Solutions:**

**If worker crashed:**
```bash
podman restart worker
```

**If worker can't connect to Redis:**
```bash
# Check Redis is running
podman ps | grep redis

# Restart Redis if needed
podman restart redis

# Restart worker
podman restart worker
```

**If worker is stuck on a task:**
```bash
# Check worker logs for the stuck task
podman logs worker --tail 200

# Restart worker to clear
podman restart worker
```

**If LLM is taking very long (first query):**
- First query can take 5-10 minutes (model download + load + inference)
- Check Ollama logs: `podman logs ollama -f`
- Look for model download progress
- Be patient, especially on first run

---

## Network Issues

### Issue: Can't Access Flask API

**Symptoms:**
```bash
curl http://localhost:5001/status/health
# Connection refused
```

**Diagnosis:**

1. **Check if web-app container is running:**
```bash
podman ps | grep web-app
```

2. **Check web-app logs:**
```bash
podman logs web-app
```

3. **Check port mapping:**
```bash
podman port web-app
# Should show: 5000/tcp -> 0.0.0.0:5001
```

**Solution:**

**If container not running:**
```bash
podman start web-app

# If it won't start, check logs
podman logs web-app
```

**If container running but port not accessible:**
```bash
# Restart with fresh port mapping
podman-compose down
podman-compose up -d

# Verify
curl http://localhost:5001/status/health
```

**If firewall blocking:**
```bash
# macOS - check if blocked
# System Preferences > Security & Privacy > Firewall

# Allow Python/Podman if needed
```

---

### Issue: LLM Can't Fetch External Data (Network Access)

**Symptoms:**
```bash
# In task result:
Failed to fetch data from https://api.example.com
ConnectionError: ...
```

**Diagnosis:**

1. **Check if worker can reach external URLs:**
```bash
podman exec worker curl -I https://api.github.com
```

2. **Check DNS resolution:**
```bash
podman exec worker nslookup api.github.com
```

**Solution:**

**If DNS fails:**
```yaml
# In docker-compose.yml, add DNS servers
worker:
  dns:
    - 8.8.8.8
    - 8.8.4.4
```

**If network blocked:**
- Check corporate firewall/proxy
- Configure proxy in container if needed
- Use internal APIs only

**If API requires authentication:**
- Add API keys via environment variables:
```yaml
worker:
  environment:
    - API_KEY=your-key-here
```

---

## File Loading Issues

### Issue: File Not Found in /app/data

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/data/sales.csv'
```

**Diagnosis:**

1. **Check files in data directory:**
```bash
# From host
ls -la data/

# From container
podman exec worker ls -la /app/data/
```

2. **List via API:**
```bash
curl http://localhost:5001/data
```

**Solution:**

**If file missing:**
```bash
# Upload file via API
curl -X POST http://localhost:5001/data \
  -F "file=@/path/to/your/file.csv"

# Or copy directly
cp /path/to/file.csv data/
```

**If file exists on host but not in container:**
```bash
# Check volume mount
podman inspect worker | grep -A 10 Mounts

# Should show:
# "Source": "/path/to/local-llm-celery/data"
# "Destination": "/app/data"

# If mount missing, recreate container
podman-compose down
podman-compose up -d
```

---

### Issue: Unsupported File Format

**Symptoms:**
```
Error: Unsupported file format: .xyz
```

**Diagnosis:**
```bash
# Check supported formats
podman exec worker python3 -c "from file_loader import SUPPORTED_EXTENSIONS; print(SUPPORTED_EXTENSIONS)"
```

**Solution:**

**Supported formats:**
- CSV (`.csv`)
- JSON (`.json`)
- Excel (`.xlsx`, `.xls`)
- TSV (`.tsv`)
- TXT (`.txt`)

**For unsupported formats:**

1. **Convert to supported format:**
```bash
# Example: Convert .xml to .csv
# Use online converter or Python script
```

2. **Or manually process:**
```python
# In your question, ask LLM to parse manually
"Read the file as text and parse the custom format..."
```

---

### Issue: Excel File Won't Load

**Symptoms:**
```
ModuleNotFoundError: No module named 'openpyxl'
# or
ModuleNotFoundError: No module named 'xlrd'
```

**Diagnosis:**
```bash
# Check if openpyxl/xlrd installed
podman exec worker pip list | grep openpyxl
podman exec worker pip list | grep xlrd
```

**Solution:**

**If modules missing:**
```bash
# Rebuild image (they're in requirements.txt)
podman build --no-cache -t local-llm-celery:dev --format docker .
podman-compose up -d
```

**If .xlsx file corrupted:**
```bash
# Try opening in Excel/LibreOffice first
# Re-save as .xlsx
# Upload again
```

**If .xls (old format) has issues:**
```bash
# Convert to .xlsx in Excel
# Or save as CSV
```

---

## Task Execution Issues

### Issue: Task Returns Empty or Incorrect Result

**Symptoms:**
- Task status shows SUCCESS
- But result is empty, "None", or wrong

**Diagnosis:**

1. **Check worker logs for generated code:**
```bash
podman logs worker --tail 200
```

2. **Look for:**
- What code was generated
- What output was produced
- Any errors in code execution

**Solution:**

**If code didn't execute:**
- LLM may have generated invalid Python
- Check logs for syntax errors
- Simplify your question

**If code executed but wrong logic:**
- Be more specific in your question
- Example: Instead of "analyze sales", say "calculate total sales by summing the Revenue column"

**If output not captured:**
- Ask LLM to explicitly print result
- Example: "Calculate total and print the result"

---

### Issue: Task Fails with Python Error

**Symptoms:**
```json
{
  "status": "FAILURE",
  "result": "NameError: name 'df' is not defined"
}
```

**Common Python errors and solutions:**

**NameError: name 'X' is not defined**
- Missing import or variable not defined
- Solution: Ask LLM to import needed modules first

**KeyError: 'column_name'**
- Column doesn't exist in DataFrame
- Solution: Ask LLM to check df.columns first
- Or use natural language: "revenue" instead of "Revenue" (LLM will map it)

**FileNotFoundError**
- File path wrong
- Solution: Always use `/app/data/filename.ext` format

**TypeError: unsupported operand type(s)**
- Data type mismatch (e.g., trying to sum strings)
- Solution: Ask LLM to convert types first: "convert to numeric then sum"

---

## Diagnostic Commands

### Quick Health Check

```bash
# All-in-one health check script
#!/bin/bash

echo "=== Podman Machine Status ==="
podman machine list

echo -e "\n=== Container Status ==="
podman ps -a

echo -e "\n=== API Health ==="
curl -s http://localhost:5001/status/health | python3 -m json.tool

echo -e "\n=== Available Data Files ==="
curl -s http://localhost:5001/data | python3 -m json.tool

echo -e "\n=== Ollama Models ==="
curl -s http://localhost:11434/api/tags | python3 -m json.tool

echo -e "\n=== Worker Status ==="
podman exec worker celery -A worker.celery_app inspect active

echo -e "\n=== Recent Worker Logs ==="
podman logs worker --tail 20
```

Save as `health-check.sh`, make executable: `chmod +x health-check.sh`, run: `./health-check.sh`

---

### Memory Diagnostic

```bash
#!/bin/bash
# Check memory allocation at all levels

echo "=== Podman Machine Memory ==="
podman machine list | grep -E 'NAME|podman-machine-default'

echo -e "\n=== Container Memory Limits ==="
for container in redis ollama web-app worker; do
  echo "Container: $container"
  podman inspect $container 2>/dev/null | grep -E '"Memory"|"MemoryReservation"' | head -2
done

echo -e "\n=== Available Memory in Worker ==="
podman exec worker free -h 2>/dev/null || echo "Worker not running"

echo -e "\n=== Ollama Model Requirements ==="
echo "llama3:8b requires: 4.6 GB"
echo "Recommended VM memory: 8 GB minimum"
```

Save as `check-memory.sh`, make executable, run: `./check-memory.sh`

---

### Build Diagnostic

```bash
#!/bin/bash
# Check if build will succeed

echo "=== Checking Prerequisites ==="
command -v podman >/dev/null 2>&1 && echo "✓ Podman installed" || echo "✗ Podman not found"
command -v podman-compose >/dev/null 2>&1 && echo "✓ podman-compose installed" || echo "✗ podman-compose not found"

echo -e "\n=== Podman Machine Status ==="
podman machine list

echo -e "\n=== Available Disk Space ==="
df -h | grep -E 'Filesystem|/System/Volumes/Data'

echo -e "\n=== Existing Images ==="
podman images | grep -E 'REPOSITORY|local-llm-celery'

echo -e "\n=== Dockerfile Present ==="
[ -f Dockerfile ] && echo "✓ Dockerfile found" || echo "✗ Dockerfile not found"

echo -e "\n=== Requirements.txt Present ==="
[ -f requirements.txt ] && echo "✓ requirements.txt found" || echo "✗ requirements.txt not found"

echo -e "\n=== File Count Check ==="
echo "Python files: $(find . -name "*.py" -not -path "./.venv/*" | wc -l)"
echo "Data files: $(ls data/ 2>/dev/null | wc -l)"
```

Save as `check-build.sh`, make executable, run: `./check-build.sh`

---

### Network Diagnostic

```bash
#!/bin/bash
# Check network connectivity

echo "=== External Network (from worker) ==="
podman exec worker curl -I https://api.github.com 2>&1 | head -5

echo -e "\n=== Ollama Connectivity (from worker) ==="
podman exec worker curl -s http://host.docker.internal:11434/api/tags 2>&1 | head -10

echo -e "\n=== Redis Connectivity (from worker) ==="
podman exec worker ping -c 2 redis 2>&1

echo -e "\n=== Port Mappings ==="
echo "Web-app ports:"
podman port web-app 2>&1

echo -e "\nOllama ports:"
podman port ollama 2>&1

echo -e "\n=== Host Ports in Use ==="
lsof -nP -iTCP:5001 -sTCP:LISTEN 2>&1
lsof -nP -iTCP:11434 -sTCP:LISTEN 2>&1
```

Save as `check-network.sh`, make executable, run: `./check-network.sh`

---

## Getting Help

### Collect Debug Information

When asking for help, provide:

1. **System info:**
```bash
podman version
podman machine list
uname -a  # or systeminfo on Windows
```

2. **Container status:**
```bash
podman ps -a
podman-compose ps
```

3. **Relevant logs:**
```bash
# Last 100 lines of each service
podman logs redis --tail 100 > redis.log
podman logs ollama --tail 100 > ollama.log
podman logs web-app --tail 100 > web-app.log
podman logs worker --tail 100 > worker.log
```

4. **Error message:**
- Full error text
- When it occurred (build, startup, runtime)
- What you were doing when it happened

5. **What you've tried:**
- List troubleshooting steps already attempted
- Results of diagnostic scripts

### File an Issue

If problem persists:
- Open issue on GitHub
- Include debug information above
- Tag with appropriate label (bug, question, help wanted)

---

## Preventive Maintenance

### Regular Checks

**Weekly:**
```bash
# Clean up unused containers/images
podman system prune -f

# Check disk space
df -h

# Update Ollama models
ollama pull llama3:8b
```

**Monthly:**
```bash
# Update Podman
brew upgrade podman  # macOS

# Rebuild images with latest dependencies
podman build --no-cache -t local-llm-celery:dev --format docker .
```

**Before Important Work:**
```bash
# Verify system health
./health-check.sh

# Test with simple query
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question":"What is 2+2?","filename":"sales-data.csv"}'
```

---

## Related Documentation

- **[FIX-MEMORY-ISSUE.md](FIX-MEMORY-ISSUE.md)** - Detailed memory troubleshooting
- **[QUICKSTART.md](QUICKSTART.md)** - Setup verification steps
- **[README.md](README.md)** - Architecture and system overview
- **[HOW-IT-WORKS.md](HOW-IT-WORKS.md)** - Understanding automatic vs manual operations
- **[OLLAMA-DEPLOYMENT.md](OLLAMA-DEPLOYMENT.md)** - Ollama deployment options

---

**Last Updated:** October 19, 2025  
**Maintained By:** Local LLM Celery Team  
**Feedback:** Please submit issues or improvements via GitHub

# Technology Stack

This document provides a comprehensive overview of all dependencies used in the Local LLM Celery project, organized by category with a one-line summary of each package's purpose.

## Summary

- **Total Dependencies**: 16 packages (core + sub-dependencies)
- **Python Version**: 3.11+
- **Container Runtime**: Podman or Docker
- **Architecture Support**: x86_64, ARM64 (Apple Silicon)
- **GPU Required**: No - 100% CPU-based

---

## Core Application Framework

### Flask
**Purpose**: Lightweight WSGI web framework for building the REST API server  
**Version**: 3.1.2 (auto-installed)  
**Usage**: Provides `/analyze`, `/status`, `/data` endpoints for client requests  
**Documentation**: https://flask.palletsprojects.com/

---

## Task Queue & Messaging

### Celery
**Purpose**: Distributed task queue for asynchronous background job processing  
**Version**: 5.5.3 (pinned)  
**Usage**: Manages analysis tasks, allows horizontal scaling of workers  
**Documentation**: https://docs.celeryproject.org/

### Redis
**Purpose**: In-memory data store used as message broker and result backend  
**Version**: 7 (container image: `redis:7-alpine`)  
**Usage**: Queues tasks from Flask API to Celery workers, stores task results  
**Documentation**: https://redis.io/docs/

---

## LLM & AI Frameworks

### open-interpreter
**Purpose**: Code execution engine that allows LLMs to write and run Python code  
**Version**: 0.4.3 (latest, auto-installed)  
**Usage**: Core of the worker - enables LLM to analyze data by generating/executing code  
**Import Name**: `interpreter` (package name is `open-interpreter`)  
**Documentation**: https://docs.openinterpreter.com/

### langchain
**Purpose**: Framework for developing applications powered by language models  
**Version**: Latest (auto-installed)  
**Usage**: Provides abstractions for LLM interactions, prompt templates, chains  
**Documentation**: https://python.langchain.com/

### langchain-community
**Purpose**: Community-contributed integrations for LangChain (Ollama, APIs, etc.)  
**Version**: Latest (auto-installed)  
**Usage**: Enables Ollama integration via `ChatOllama` class  
**Documentation**: https://python.langchain.com/docs/integrations/platforms/

### ollama
**Purpose**: Python client for Ollama API, manages local LLM inference  
**Version**: Latest (auto-installed)  
**Usage**: Communicates with Ollama service to run llama3:8b model  
**Documentation**: https://github.com/ollama/ollama-python

---

## Data Processing & Analysis

### pandas
**Purpose**: Powerful data manipulation and analysis library for structured data  
**Version**: 2.3.3 (latest, auto-installed)  
**Usage**: Loads/processes CSV/Excel/TSV files, performs statistical analysis, data joins  
**Documentation**: https://pandas.pydata.org/docs/

### openpyxl
**Purpose**: Library for reading and writing Excel 2010+ (.xlsx) files  
**Version**: Latest (auto-installed)  
**Usage**: Enables pandas to load modern Excel files via `load_file()` in file_loader.py  
**Documentation**: https://openpyxl.readthedocs.io/

### xlrd
**Purpose**: Library for reading legacy Excel (.xls) files (Excel 97-2003)  
**Version**: Latest (auto-installed)  
**Usage**: Enables pandas to load older Excel files via `load_file()` in file_loader.py  
**Documentation**: https://xlrd.readthedocs.io/

**Note**: xlrd only supports .xls files up to version 1.2.0. For .xlsx, use openpyxl.

---

## Network & Web Scraping

### requests
**Purpose**: Elegant HTTP library for making API calls and web requests  
**Version**: Latest (auto-installed)  
**Usage**: Used by LLM to fetch live data from APIs (inflation, stock prices, weather, etc.)  
**Documentation**: https://requests.readthedocs.io/

### beautifulsoup4
**Purpose**: HTML/XML parser for web scraping and data extraction  
**Version**: Latest (auto-installed)  
**Usage**: Enables LLM to parse and extract data from HTML pages when APIs aren't available  
**Documentation**: https://www.crummy.com/software/BeautifulSoup/bs4/doc/

### lxml
**Purpose**: Fast XML/HTML processing library, parser backend for BeautifulSoup  
**Version**: Latest (auto-installed)  
**Usage**: Provides efficient XML/HTML parsing for web scraping tasks  
**Documentation**: https://lxml.de/

---

## Build & Performance Optimization

### fastuuid
**Purpose**: High-performance UUID generation library  
**Version**: 0.13.3 (pinned to avoid Rust compilation OOM)  
**Usage**: Used internally by dependencies for generating unique task IDs  
**Why Pinned**: Version 0.13.4+ requires Rust compilation which can cause OOM during build  
**Documentation**: https://github.com/thedrow/fastuuid

**Important**: This pin prevents "exit 137" build failures on systems with limited memory.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Application                      │
│                   (Python, cURL, JavaScript)                │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        Flask API                            │
│               (REST endpoints, request routing)             │
└────────────────────────┬────────────────────────────────────┘
                         │ Task submission
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Redis (Queue)                          │
│            (Message broker, result backend)                 │
└────────────────────────┬────────────────────────────────────┘
                         │ Task dequeue
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Worker                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Open Interpreter                        │   │
│  │  (Code generation & execution engine)                │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│               ▼                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LangChain + Ollama                      │   │
│  │         (LLM orchestration & inference)              │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│               ▼                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Pandas + File Loaders                        │   │
│  │  (CSV, Excel, JSON, TSV, TXT processing)             │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│               ▼                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │     Requests + BeautifulSoup (Optional)              │   │
│  │       (Live data fetching from APIs/web)             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                         │ Inference requests
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ollama Service                           │
│              (llama3:8b model inference)                    │
│                   CPU-only, no GPU                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Resource Requirements by Component

| Component | CPU | Memory | Disk | Purpose |
|-----------|-----|--------|------|---------|
| Flask API | 200m-1000m | 256Mi-1Gi | 100MB | HTTP request handling |
| Celery Worker | 500m-2000m | 1Gi-4Gi | 500MB | Task execution & LLM coordination |
| Redis | 100m-500m | 128Mi-512Mi | 50MB | Message queue |
| Ollama | 1000m-4000m | 4Gi-8Gi | 5GB | LLM model inference (llama3:8b) |

**Total Minimum**: 2 CPUs, 6GB RAM (without Ollama)  
**Recommended**: 4 CPUs, 12GB RAM (with Ollama)  
**No GPU Required**: All inference runs on CPU

---

## Data Flow Example

**User Query: "What is the median Avg_Price?"**

1. **Client** → sends POST request to Flask API `/analyze`
2. **Flask** → validates request, creates Celery task, returns task_id
3. **Celery** → stores task in Redis queue
4. **Worker** → dequeues task from Redis
5. **Open Interpreter** → receives task, prepares to execute
6. **LangChain + Ollama** → LLM generates Python code:
   ```python
   import pandas as pd
   from file_loader import load_file
   df = load_file('/app/data/sales-data.csv')
   median = df['Avg_Price'].median()
   print(f"The median Avg_Price is: {median}")
   ```
7. **Pandas** → executes code, loads CSV, calculates median
8. **Open Interpreter** → captures output, returns to Celery
9. **Celery** → stores result in Redis
10. **Client** → polls `/status/{task_id}`, retrieves result

---

## File Format Support Matrix

| Format | Loader Library | Read Function | Extensions | Notes |
|--------|---------------|---------------|------------|-------|
| CSV | pandas | `pd.read_csv()` | `.csv` | Default format, best tested |
| JSON | pandas | `pd.read_json()` | `.json` | Supports array, nested, lines formats |
| Excel (new) | pandas + openpyxl | `pd.read_excel()` | `.xlsx` | Modern Excel format (2010+) |
| Excel (old) | pandas + xlrd | `pd.read_excel()` | `.xls` | Legacy Excel format (97-2003) |
| TSV | pandas | `pd.read_csv(sep='\t')` | `.tsv` | Tab-separated values |
| TXT | pandas | `pd.read_csv()` | `.txt` | Auto-detects delimiter (comma, tab, pipe, etc.) |

All formats support:
- ✅ Automatic schema detection
- ✅ Natural language column mapping
- ✅ Multi-file analysis
- ✅ Data normalization
- ✅ LLM-powered queries

---

## Environment Variables

The application uses the following environment variables (configured in `docker-compose.yml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string for Celery |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama API endpoint |
| `CELERY_BROKER_URL` | (from REDIS_URL) | Celery message broker |
| `CELERY_RESULT_BACKEND` | (from REDIS_URL) | Celery result storage |

---

## Version Management

### Pinned Versions

Only `fastuuid==0.13.3` is pinned to prevent build failures on memory-constrained systems.

### Auto-Updated Versions

All other packages use the latest compatible versions:
- **Pros**: Get security patches, bug fixes, new features automatically
- **Cons**: Potential breaking changes, requires testing before production deployment

### Production Recommendations

For production deployments, consider pinning all versions:

```bash
# Generate exact version lock
pip freeze > requirements-lock.txt

# Use in Dockerfile
COPY requirements-lock.txt .
RUN pip install -r requirements-lock.txt
```

---

## Security Considerations

### Network Access

⚠️ **Security Warning**: The LLM has network access enabled via `requests` and `beautifulsoup4`.

**Implications**:
- LLM can make HTTP requests to any public URL
- Can fetch external data (APIs, websites)
- Potential for SSRF (Server-Side Request Forgery) if untrusted users have access

**Mitigations**:
1. Run in isolated network environment
2. Use firewall rules to restrict outbound connections
3. Implement request filtering/whitelisting in worker
4. Audit LLM-generated code before execution (requires disabling auto-exec)

### Code Execution

⚠️ **Security Warning**: The LLM generates and executes arbitrary Python code via Open Interpreter.

**Implications**:
- Can read/write files in `/app/data` directory
- Can make system calls within container
- Can install packages (if pip available)

**Mitigations**:
1. Run in containerized environment (done ✅)
2. Use read-only filesystem except for `/app/data`
3. Drop container capabilities (CAP_DROP in Docker/Podman)
4. Use network policies to restrict container egress
5. Implement resource limits (CPU, memory)
6. Consider sandboxing with gVisor or Kata Containers for sensitive environments

---

## Performance Tuning

### CPU Optimization

Since this is CPU-only inference:
- **Scale horizontally**: Add more Celery workers instead of bigger instances
- **CPU affinity**: Use `--cpuset-cpus` in Podman/Docker to dedicate cores
- **Worker concurrency**: Set `CELERYD_CONCURRENCY=1` to avoid contention

### Memory Optimization

- **Model caching**: Ollama caches loaded models (stays in RAM)
- **Pandas chunking**: For large files, use `chunksize` parameter in `pd.read_csv()`
- **Redis persistence**: Disable if not needed (`save ""` in redis.conf)

### Network Optimization

- **Local Ollama**: Use `host.docker.internal` or `host.containers.internal` for lowest latency
- **Shared Redis**: Single Redis instance can handle 10,000+ tasks/second

---

## Upgrading Dependencies

### Safe Upgrade Process

```bash
# 1. Create a test environment
python3 -m venv venv-test
source venv-test/bin/activate

# 2. Install latest versions
pip install --upgrade flask celery pandas langchain open-interpreter

# 3. Test functionality
python app.py &
celery -A worker.celery_app worker --loglevel=info &
# Run test queries

# 4. If successful, freeze versions
pip freeze > requirements-new.txt

# 5. Compare with old
diff requirements.txt requirements-new.txt

# 6. Update and rebuild
mv requirements-new.txt requirements.txt
podman build -t local-llm-celery:dev --format docker .
```

### Breaking Change Alerts

Monitor these repositories for breaking changes:
- **langchain**: Major version bumps (0.x → 1.x)
- **open-interpreter**: API changes in code execution model
- **pandas**: Deprecation warnings in 2.x series

---

## Alternative Stacks

### Smaller Footprint

For systems with <8GB RAM, consider:
- **Model**: Switch to `tinyllama` (~637MB) or `phi3:mini` (~2.3GB)
- **Redis**: Use `redis:7-alpine` image (~10MB vs ~40MB)
- **Framework**: Replace Celery with RQ (simpler, less overhead)

### GPU Acceleration

If GPU is available, modify Ollama deployment:
```yaml
# In docker-compose.yml or k8s manifests
devices:
  - /dev/nvidia0
environment:
  - NVIDIA_VISIBLE_DEVICES=all
```

No code changes needed - Ollama will automatically use GPU if detected.

### Serverless

For serverless deployment (AWS Lambda, Google Cloud Run):
- **Challenge**: Ollama requires persistent model storage (5GB+)
- **Solution**: Use external Ollama service (Option 3 in OLLAMA-DEPLOYMENT.md)
- **Alternative**: Replace Ollama with OpenAI API for stateless deployment

---

## Troubleshooting

### Module Import Errors

**Problem**: `ModuleNotFoundError: No module named 'xyz'`

**Solution**: Rebuild container image:
```bash
podman build -t local-llm-celery:dev --format docker .
```

### Build Fails with Exit 137

**Problem**: Container build OOM during `pip install`

**Solution**: Pin fastuuid is already in requirements.txt, but if issue persists:
```bash
# Increase Podman machine memory
podman machine stop
podman machine rm
podman machine init --memory 8192 --cpus 4
podman machine start
```

### Dependency Conflicts

**Problem**: `ERROR: Cannot install X because Y requires Z`

**Solution**: Use virtual environment to isolate dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
```

---

## See Also

- **[README.md](README.md)** - Main project documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[FILE-FORMAT-SUPPORT.md](FILE-FORMAT-SUPPORT.md)** - Supported file formats
- **[FIX-MEMORY-ISSUE.md](FIX-MEMORY-ISSUE.md)** - Memory troubleshooting guide
- **[OLLAMA-DEPLOYMENT.md](OLLAMA-DEPLOYMENT.md)** - Ollama deployment options

---

**Last Updated**: {{ TODAY }}  
**Project Version**: 1.0 (Multi-Format Support)

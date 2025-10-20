# Local LLM Celery - AI-Powered Data Analysis Service

A microservices-based data analysis platform that uses Open Interpreter with Ollama LLM to analyze data files via natural language queries. Built with Flask, Celery, and Redis for scalable background task processing.

**Multi-Format Support:** Full support for CSV, JSON, Excel, TSV, and TXT files with automatic schema detection, normalization, and natural language understanding.

## 🌟 Features

- **Universal File Support**: Automatic loading for CSV, JSON, Excel (.xlsx, .xls), TSV, and TXT files
- **Natural Language Queries**: Ask questions in plain English - no need to know exact column names (e.g., "average price" works even if column is `Avg_Price`)
- **Multi-File Analysis**: LLM automatically has access to all uploaded data files and can combine them as needed
- **Mixed Format Analysis**: Combine different file formats in a single query (e.g., CSV + Excel + JSON)
- **Intelligent Data Normalization**: LLM inspects and normalizes datasets with different schemas before combining (works across all formats)
- **Live Data Fetching**: LLM can fetch real-time data from APIs and websites (inflation rates, stock prices, weather, etc.)
- **Cached Inflation Data**: Built-in historical US inflation data (1914-present) scraped and cached locally for accurate price predictions
- **Automated Code Generation**: LLM writes and executes Python code to analyze data
- **Asynchronous Processing**: Background task queue using Celery and Redis
- **Local LLM**: Uses Ollama with llama3:8b for complete privacy
- **RESTful API**: Simple HTTP endpoints for integration
- **Containerized**: Fully containerized with Podman/Docker support
- **CPU-Only**: No GPU required - runs on any x86_64 or ARM64 CPU
- **Dynamic Data Management**: Upload, update, and delete datasets via API - no redeployment needed

## ⚙️ System Requirements & Constraints

### Hardware Requirements
- **CPU**: x86_64 or ARM64 (Apple Silicon) multi-core processor
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB for images and models
- **GPU**: **NOT REQUIRED** - This system runs entirely on CPU

### Data Format Support
- ✅ **All formats fully supported**: CSV, JSON, Excel (.xlsx, .xls), TSV, TXT
- ✅ **Automatic file type detection** with universal loader (`file_loader.py`)
- ✅ **Schema detection, normalization, and semantic understanding** for all formats
- ✅ **Natural language queries** work with all formats
- ✅ **Multi-file analysis** with mixed formats (e.g., CSV + Excel + JSON)
- 📄 **File size limit**: 100MB maximum per file
- 📖 See [FILE-FORMAT-SUPPORT.md](FILE-FORMAT-SUPPORT.md) for detailed format information

### Important Constraints
- ✅ **100% CPU-based inference** - No GPU dependencies
- ✅ Works on any cloud provider (AWS, GCP, Azure, etc.)
- ✅ No CUDA, ROCm, or GPU drivers needed
- ✅ Runs on Kubernetes without GPU node pools
- ⚠️ Inference is slower than GPU-accelerated solutions (~5-10 tokens/sec vs 50+ tokens/sec)
- ⚠️ Best for low-to-medium throughput workloads

**Verify CPU-only deployment:**
```bash
./verify-cpu-only.sh
```
This script confirms there are no GPU dependencies in the codebase.

**This makes the system ideal for:**
- Development and testing environments
- Cost-sensitive deployments
- Cloud environments without GPU access
- Edge deployments on standard servers

**Trade-off:**
- CPU inference is slower but more accessible and cost-effective
- For high-throughput production with GPU, consider deploying Ollama on GPU servers (Option 3)

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │─────▶│  Flask API  │─────▶│    Redis    │
│             │◀─────│  (app.py)   │      │   (Queue)   │
└─────────────┘      └─────────────┘      └──────┬──────┘
                                                  │
                                                  ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│    Data     │◀─────│Celery Worker│◀─────│Task Dequeue │
│(All Formats)│      │ (worker.py) │      │             │
└─────────────┘      └──────┬──────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   Ollama    │
                     │  (llama3:8b)│
                     └─────────────┘
```

## 📋 Prerequisites

### Local Development
- **Podman** or **Docker** (this guide uses Podman)
- **Ollama** installed locally with `llama3:8b` model
- **Python 3.11+** (for local development)
- **macOS/Linux** (ARM64 or x86_64)
- **NO GPU REQUIRED** - System runs entirely on CPU

### System Requirements
- **Minimum RAM**: 8GB (16GB recommended for building images)
- **CPU**: Multi-core processor (4+ cores recommended)
- **Disk Space**: 10GB for images and models
- **GPU**: None - CPU-only deployment

## 🚀 Getting Started

### 1. Install Ollama and Pull the Model

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# In another terminal, pull the llama3:8b model
ollama pull llama3:8b

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### 2. Clone the Repository

```bash
git clone https://github.com/Laszlo-Lazuer/local-llm-celery.git
cd local-llm-celery
```

### 3. Build the Container Image

```bash
podman build -t local-llm-celery:dev --format docker .
```

**Note**: Building may take 10-15 minutes on the first run as it installs ~100+ Python dependencies.

### 4. Create a Podman Network

```bash
podman network create llm-net
```

### 5. Start Redis

```bash
podman run -d \
  --name redis \
  --network llm-net \
  redis:7
```

### 6. Start the Flask API Server

```bash
podman run -d \
  --name llm-app \
  --network llm-net \
  -p 5001:5000 \
  -v $(pwd)/data:/app/data:Z \
  local-llm-celery:dev \
  python app.py
```

### 7. Start the Celery Worker

```bash
podman run -d \
  --name llm-worker \
  --network llm-net \
  -v $(pwd)/data:/app/data:Z \
  local-llm-celery:dev \
  celery -A worker.celery_app worker --loglevel=info
```

### 8. Verify Everything is Running

```bash
# Check containers
podman ps

# Test API health
curl http://localhost:5001/status/test

# Check worker logs
podman logs llm-worker --tail 20
```

## 📖 Usage

### Managing Data Files

**No redeployment needed!** Upload, update, and delete data files via API.

#### Upload a New Dataset

```bash
curl -X POST http://localhost:5001/data \
  -F "file=@/path/to/your/data.csv"
```

#### List All Data Files

```bash
curl http://localhost:5001/data
```

**Response:**
```json
{
  "files": [
    {
      "filename": "sales-data.csv",
      "size_bytes": 2048,
      "size_human": "2.00 KB",
      "modified": 1698624000.0
    }
  ],
  "count": 1
}
```

#### Update an Existing File

```bash
curl -X PUT http://localhost:5001/data/sales-data.csv \
  -F "file=@/path/to/updated-data.csv"
```

#### Delete a File

```bash
curl -X DELETE http://localhost:5001/data/old-data.csv
```

> 📘 **Complete Data Management API**: See [DATA-API.md](DATA-API.md) for full documentation including download, file info, Python client examples, and more.

### Sample Data

The project includes sample concert tour data in `data/sales-data.csv`:

```csv
Date,City,Country,Venue,Attendance,Revenue,Min_Price,Max_Price,Avg_Price
2019-03-18,Albany,United States,Times Union Center,11432,1268045.00,39.95,249.95,110.92
...
```

### Making Requests

#### 1. Submit an Analysis Task

**Single File Analysis:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the median Avg_Price?",
    "filename": "sales-data.csv"
  }'
```

**Multi-File Analysis (automatic):**
```bash
# The LLM has access to ALL uploaded files and can use multiple files as needed
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare total revenue between sales-data.csv and q2-sales.csv"
  }'
```

> **Note**: When you upload multiple data files, the LLM automatically knows about all of them and can load/combine any files needed to answer your question. You can specify a primary file with `"filename"`, or omit it to let the LLM work with all available data.

**Response:**
```json
{
  "task_id": "73208592-a4c1-4d56-819f-9eaba5623ffc"
}
```

#### 2. Check Task Status

```bash
curl http://localhost:5001/status/73208592-a4c1-4d56-819f-9eaba5623ffc
```

**Response:**
```json
{
  "task_id": "73208592-a4c1-4d56-819f-9eaba5623ffc",
  "status": "SUCCESS",
  "result": "The median Avg_Price is: 112.48\n\nThe output indicates that the median value of the \"Avg_Price\" column is $112.48."
}
```

### Sample Queries

Try these example questions:

```bash
# Statistical analysis - single file
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the total Revenue across all events?", "filename": "sales-data.csv"}'

# Filtering and grouping
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "Which city had the highest attendance?", "filename": "sales-data.csv"}'

# Multi-file analysis - LLM can access all available data files
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the combined revenue from all uploaded CSV files?"}'

# Cross-file comparison
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare average prices between sales-data.csv and q2-data.csv"}'

# Date-based queries
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "How many events were held in June 2019?", "filename": "sales-data.csv"}'

# Complex analysis
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the correlation between Attendance and Revenue?", "filename": "sales-data.csv"}'
```

**How Multi-File Support Works:**
- The LLM automatically sees all files in `/app/data` directory
- You can specify a `filename` to set a primary focus file
- Or omit `filename` to let the LLM work with all available data
- The LLM can load, join, and analyze multiple files in a single query
- Perfect for comparing datasets, merging data, or aggregate analysis

### Predictive Analysis Examples

#### Inflation-Adjusted Pricing (Using Assumptions)

For quick analysis with assumed inflation rates:

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "If the artist tours Chicago in 2026, what would the expected ticket price be? Calculate the average historical price for Chicago, then adjust for inflation from 2019 to 2026 using 3% annual inflation. Show your calculation steps.",
    "filename": "sales-data.csv"
  }'
```

**Expected Output:**
```json
{
  "task_id": "...",
  "status": "SUCCESS",
  "result": "The average ticket price for Chicago events is approximately $119.85 and the expected ticket price in 2026 after applying a 3% annual inflation rate for 7 years is approximately $147.40."
}
```

**Calculation Details:**
- Historical Average (Chicago): $119.85
- Inflation Factor: (1.03)^7 = 1.2299
- 2026 Expected Price: $119.85 × 1.2299 = **$147.40**

#### Live Data Fetching (Using Real APIs)

⚠️ **Note**: Network access is enabled but APIs may require keys or have rate limits.

For analysis with real-time data from external sources:

```bash
# Attempt to fetch real inflation data (may require valid API key)
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch current US inflation rates from a public source, then use the actual cumulative inflation from 2019-2025 to calculate Chicago 2026 ticket prices. Show the real data you fetched.",
    "filename": "sales-data.csv"
  }'
```

**Example with specific API:**
```bash
# Using a known working endpoint
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Make a GET request to https://api.github.com/repos/python/cpython and show how many stars the Python repository has",
    "filename": "sales-data.csv"
  }'
```

**Key Differences:**
- **With Assumptions**: Fast, predictable, uses specified rates (e.g., "3% inflation")
- **With Live Data**: Slower, requires working API endpoint, uses real current data
- **When to use each**:
  - Use assumptions for quick estimates, testing, or when exact data isn't critical
  - Use live data for production analysis, compliance, or when accuracy is essential

See [NETWORK-ACCESS.md](NETWORK-ACCESS.md) for detailed information on fetching live data.

## 🐍 Embedding in Python Applications

### Basic Integration

```python
import requests
import time

class DataAnalysisClient:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url

    def analyze(self, question, filename, timeout=60):
        """Submit analysis task and wait for result."""
        # Submit task
        response = requests.post(
            f"{self.base_url}/analyze",
            json={"question": question, "filename": filename}
        )
        response.raise_for_status()
        task_id = response.json()["task_id"]

        # Poll for result
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_response = requests.get(
                f"{self.base_url}/status/{task_id}"
            )
            status_response.raise_for_status()
            data = status_response.json()

            if data["status"] == "SUCCESS":
                return data["result"]
            elif data["status"] == "FAILURE":
                raise Exception(f"Task failed: {data.get('result')}")

            time.sleep(2)  # Poll every 2 seconds

        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

# Usage
client = DataAnalysisClient()

result = client.analyze(
    question="What is the median Avg_Price?",
    filename="sales-data.csv"
)
print(result)
```

### Async Integration (asyncio)

```python
import aiohttp
import asyncio

class AsyncDataAnalysisClient:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url

    async def analyze(self, question, filename, timeout=60):
        """Submit analysis task and wait for result asynchronously."""
        async with aiohttp.ClientSession() as session:
            # Submit task
            async with session.post(
                f"{self.base_url}/analyze",
                json={"question": question, "filename": filename}
            ) as response:
                response.raise_for_status()
                task_id = (await response.json())["task_id"]

            # Poll for result
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                async with session.get(
                    f"{self.base_url}/status/{task_id}"
                ) as status_response:
                    status_response.raise_for_status()
                    data = await status_response.json()

                    if data["status"] == "SUCCESS":
                        return data["result"]
                    elif data["status"] == "FAILURE":
                        raise Exception(f"Task failed: {data.get('result')}")

                await asyncio.sleep(2)

            raise TimeoutError(f"Task {task_id} did not complete")

# Usage
async def main():
    client = AsyncDataAnalysisClient()
    result = await client.analyze(
        question="What is the median Avg_Price?",
        filename="sales-data.csv"
    )
    print(result)

asyncio.run(main())
```

## ☸️ Kubernetes Deployment

### Important: Ollama Deployment Options

**This application requires Ollama to be running.** You have three options:

#### Option 1: Ollama Running on Your Local Machine (Development)
- **Best for**: Development and testing
- **Setup**: Ollama runs on your laptop/workstation, K8s workers connect via `host.docker.internal`
- **Pros**: Easy to set up, no cluster resources needed for LLM
- **Cons**: Not suitable for production, requires node-to-host networking

#### Option 2: Ollama Running in Kubernetes (Production)
- **Best for**: Production deployments, self-contained clusters
- **Setup**: Deploy Ollama as a pod in the cluster using `k8s/ollama.yaml`
- **Pros**: Self-contained, scalable, production-ready
- **Cons**: Requires 4-8GB RAM per Ollama pod, increases cluster resource needs

#### Option 3: Ollama as External Service (Production)
- **Best for**: Large-scale production, shared LLM infrastructure
- **Setup**: Ollama runs on dedicated GPU servers outside the cluster
- **Pros**: Best performance, can use GPU acceleration, shared across multiple apps
- **Cons**: Requires separate infrastructure, network connectivity

**The instructions below cover all three options.** Choose based on your environment.

> 📘 **Detailed Ollama Deployment Guide**: See [OLLAMA-DEPLOYMENT.md](OLLAMA-DEPLOYMENT.md) for a complete comparison, decision matrix, and troubleshooting guide for each option.

### Prerequisites

- Kubernetes cluster (minikube, EKS, GKE, AKS, or self-hosted)
- `kubectl` installed and configured
- Ollama deployment (choose one of the three options above)
- **Standard CPU nodes** (GPU nodes NOT required)

### Resource Requirements

**Important: All components run on CPU - no GPU nodes needed**

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit | Notes |
|-----------|-------------|-----------|----------------|--------------|-------|
| Redis | 100m | 500m | 128Mi | 512Mi | Lightweight queue |
| Flask API | 200m | 1000m | 256Mi | 1Gi | Handles API requests |
| Celery Worker | 500m | 2000m | 1Gi | 4Gi | CPU-based LLM inference |
| Ollama (optional) | 1000m | 4000m | 4Gi | 8Gi | CPU-based model inference |

**Total Minimum**: 2 CPUs, 6GB RAM (without Ollama) - **No GPU required**
**Recommended**: 4 CPUs, 12GB RAM (with Ollama) - **Runs on standard nodes**

> 💡 **GPU Note**: While Ollama *can* use GPU if available, this deployment is designed for CPU-only environments. All components work without any GPU acceleration.

### Step-by-Step Deployment

#### 1. Create Kubernetes Manifests

**Create `k8s/namespace.yaml`:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: llm-analysis
```

**Create `k8s/redis.yaml`:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: llm-analysis
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: llm-analysis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Create `k8s/configmap.yaml`:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-config
  namespace: llm-analysis
data:
  REDIS_URL: "redis://redis:6379/0"
  OLLAMA_HOST: "http://host.docker.internal:11434"  # Adjust based on your setup
```

**Create `k8s/pvc.yaml` (for data files):**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
  namespace: llm-analysis
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  # Adjust storageClassName based on your cluster
  # storageClassName: standard
```

**Create `k8s/flask-api.yaml`:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-api
  namespace: llm-analysis
spec:
  selector:
    app: flask-api
  ports:
    - port: 5000
      targetPort: 5000
  type: LoadBalancer  # Use NodePort or Ingress as needed
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-api
  namespace: llm-analysis
spec:
  replicas: 2  # Scale horizontally
  selector:
    matchLabels:
      app: flask-api
  template:
    metadata:
      labels:
        app: flask-api
    spec:
      containers:
      - name: flask-api
        image: local-llm-celery:dev  # Push to your registry
        imagePullPolicy: Always
        command: ["python", "app.py"]
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: llm-config
        volumeMounts:
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /status/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /status/health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: data-pvc
```

**Create `k8s/celery-worker.yaml`:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: llm-analysis
spec:
  replicas: 2  # Scale based on workload
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: celery-worker
        image: local-llm-celery:dev  # Push to your registry
        imagePullPolicy: Always
        command: ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]
        envFrom:
        - configMapRef:
            name: llm-config
        volumeMounts:
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: data-pvc
```

**Create `k8s/ollama.yaml` (optional - if running in cluster):**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: llm-analysis
spec:
  selector:
    app: ollama
  ports:
    - port: 11434
      targetPort: 11434
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: llm-analysis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        resources:
          requests:
            memory: "4Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
      volumes:
      - name: ollama-data
        emptyDir: {}
```

#### 2. Push Image to Container Registry

```bash
# Tag the image for your registry
podman tag local-llm-celery:dev your-registry.io/local-llm-celery:latest

# Login to your registry
podman login your-registry.io

# Push the image
podman push your-registry.io/local-llm-celery:latest
```

Update the `image:` field in `k8s/flask-api.yaml` and `k8s/celery-worker.yaml` to point to your registry.

#### 3. Configure Ollama Connection

**Choose your Ollama deployment option and update `k8s/configmap.yaml`:**

**Option 1: Local Ollama (Development)**
```yaml
# In k8s/configmap.yaml
data:
  OLLAMA_HOST: "http://host.docker.internal:11434"
```
Make sure Ollama is running on your local machine: `ollama serve`

**Option 2: In-Cluster Ollama (Production)**
```yaml
# In k8s/configmap.yaml
data:
  OLLAMA_HOST: "http://ollama:11434"
```
You'll deploy Ollama in step 4 using `k8s/ollama.yaml`

**Option 3: External Ollama Service (Production)**
```yaml
# In k8s/configmap.yaml
data:
  OLLAMA_HOST: "http://ollama.example.com:11434"  # Your external Ollama URL
```

#### 4. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy Redis
kubectl apply -f k8s/redis.yaml

# Create ConfigMap (make sure you've updated OLLAMA_HOST first!)
kubectl apply -f k8s/configmap.yaml

# Create PVC
kubectl apply -f k8s/pvc.yaml

# Deploy Flask API
kubectl apply -f k8s/flask-api.yaml

# Deploy Celery Workers
kubectl apply -f k8s/celery-worker.yaml

# ONLY IF USING OPTION 2: Deploy Ollama in cluster
kubectl apply -f k8s/ollama.yaml

# Wait for Ollama pod to start and pull the model (if using Option 2)
kubectl wait --for=condition=ready pod -l app=ollama -n llm-analysis --timeout=300s
```

**If deploying Ollama in-cluster (Option 2), pull the model:**
```bash
# Get the Ollama pod name
OLLAMA_POD=$(kubectl get pod -n llm-analysis -l app=ollama -o jsonpath='{.items[0].metadata.name}')

# Pull the llama3:8b model
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama pull llama3:8b

# Verify the model is available
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama list
```

#### 5. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n llm-analysis

# Check services
kubectl get svc -n llm-analysis

# View logs
kubectl logs -n llm-analysis -l app=celery-worker --tail=50

# Get Flask API external IP (if using LoadBalancer)
kubectl get svc flask-api -n llm-analysis
```

**Verify Ollama connectivity:**
```bash
# Get a worker pod name
WORKER_POD=$(kubectl get pod -n llm-analysis -l app=celery-worker -o jsonpath='{.items[0].metadata.name}')

# Option 1 (Local): Test connection to host.docker.internal
kubectl exec -n llm-analysis $WORKER_POD -- curl -s http://host.docker.internal:11434/api/tags

# Option 2 (In-Cluster): Test connection to ollama service
kubectl exec -n llm-analysis $WORKER_POD -- curl -s http://ollama:11434/api/tags

# Option 3 (External): Test connection to external service
kubectl exec -n llm-analysis $WORKER_POD -- curl -s http://your-ollama-server.com:11434/api/tags
```

You should see a JSON response listing available models.

#### 6. Upload Data Files

```bash
# Find a Flask API pod
POD=$(kubectl get pod -n llm-analysis -l app=flask-api -o jsonpath='{.items[0].metadata.name}')

# Copy CSV data
kubectl cp data/sales-data.csv llm-analysis/$POD:/app/data/sales-data.csv
```

#### 7. Test the Deployment

```bash
# Port-forward to test locally
kubectl port-forward -n llm-analysis svc/flask-api 5001:5000

# In another terminal, test the API
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the median Avg_Price?", "filename": "sales-data.csv"}'
```

### Scaling

```bash
# Scale Flask API for more request handling
kubectl scale deployment flask-api -n llm-analysis --replicas=3

# Scale workers for more parallel processing
kubectl scale deployment celery-worker -n llm-analysis --replicas=4

# Verify scaling
kubectl get deployments -n llm-analysis
```

### Monitoring

```bash
# Watch pod status
kubectl get pods -n llm-analysis -w

# Stream worker logs
kubectl logs -n llm-analysis -l app=celery-worker -f

# Check resource usage
kubectl top pods -n llm-analysis
```

### Cleanup

```bash
# Delete all resources
kubectl delete namespace llm-analysis
```

## 🛠️ Development

### Project Structure

```
local-llm-celery/
├── app.py              # Flask API server
├── worker.py           # Celery worker with Open Interpreter
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Docker Compose orchestration
├── data/              # CSV data files
│   └── sales-data.csv
└── k8s/               # Kubernetes manifests (create this)
    ├── namespace.yaml
    ├── redis.yaml
    ├── flask-api.yaml
    └── celery-worker.yaml
```

### Local Development Without Containers

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Redis locally
brew install redis
redis-server

# Set environment variable
export REDIS_URL=redis://localhost:6379/0

# Run Flask API
python app.py

# In another terminal, run worker
celery -A worker.celery_app worker --loglevel=info
```

## 🔧 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'interpreter'`
- **Solution**: Rebuild image - the package name is `open-interpreter` but imports as `interpreter`

**Issue**: Worker can't connect to Ollama
- **Solution**: Ensure Ollama is running and accessible at `host.docker.internal:11434`
- Check: `curl http://localhost:11434/api/tags`

**Issue**: Build fails with exit code 137 (OOM)
- **Solution**: Increase Docker/Podman memory limit to 8GB+
- The build process installs 100+ dependencies including large ML libraries

**Issue**: Multi-file analysis only uses one file
- **Solution**: Be explicit in your question about which files to use
- See [Multi-File Analysis Guide](MULTI-FILE-ANALYSIS.md) for examples

## 📚 Additional Documentation

- **[Query Examples & Use Cases](EXAMPLES.md)** - Comprehensive query examples with expected outputs
- **[File Format Support](FILE-FORMAT-SUPPORT.md)** - Supported file formats, limitations, and workarounds
- **[Data Normalization](DATA-NORMALIZATION.md)** - How the LLM handles datasets with different schemas intelligently
- **[Inflation Data Cache](INFLATION-CACHE.md)** - Historical US inflation data (1914-present) for accurate price predictions
- **[Adaptive API Parsing](ADAPTIVE-API-PARSING.md)** - How the LLM handles unknown API structures intelligently
- **[Network Access & Live Data](NETWORK-ACCESS.md)** - Fetch real-time data from APIs and websites
- **[Multi-File Analysis](MULTI-FILE-ANALYSIS.md)** - Complete guide to analyzing multiple datasets simultaneously
- **[Data Management API](DATA-API.md)** - Upload, update, and delete data files via REST API
- **[Ollama Deployment Options](OLLAMA-DEPLOYMENT.md)** - Three deployment strategies for Ollama in Kubernetes
- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Kubernetes Deployment](k8s/README.md)** - Production deployment guide

## 🤝 Contributing

Contributions welcome! This is a reference implementation for:
- Local LLM integration patterns
- Celery task queue architecture
- CPU-only ML deployment strategies
- Multi-file data analysis workflows

## 📄 License

MIT License - Feel free to use this project as a template for your own AI-powered data analysis services.

**Issue**: Task returns NaN or errors
- **Solution**: Ensure CSV has clean numeric data without special characters ($, commas, etc.)

**Issue**: Do I need a GPU for this to work?
- **Solution**: **No!** This entire system runs on CPU. No GPU, CUDA, or specialized hardware is required. GPU is optional for better performance but not needed.

### Viewing Logs

```bash
# Flask API logs
podman logs llm-app -f

# Worker logs
podman logs llm-worker -f

# Redis logs
podman logs redis
```

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📧 Support

For issues and questions, please open a GitHub issue.

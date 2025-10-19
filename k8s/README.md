# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Local LLM Celery service.

## Important: Ollama Deployment Required

**This application requires Ollama to be running.** Choose one deployment option:

1. **Local Development**: Ollama on your laptop, K8s connects via `host.docker.internal:11434`
2. **In-Cluster Production**: Deploy Ollama as a pod using `ollama.yaml` (requires 4-8GB RAM)
3. **External Service**: Ollama on dedicated servers, K8s connects via external URL

See the main README.md for detailed comparison of these options.

## Files

- `namespace.yaml` - Creates the `llm-analysis` namespace
- `redis.yaml` - Redis deployment and service (message queue)
- `configmap.yaml` - **IMPORTANT**: Set `OLLAMA_HOST` based on your deployment option
- `pvc.yaml` - Persistent Volume Claim for data files
- `flask-api.yaml` - Flask API deployment and service
- `celery-worker.yaml` - Celery worker deployment
- `ollama.yaml` - **USE ONLY FOR OPTION 2**: Ollama deployment in-cluster
- `ingress.yaml` - (Optional) Ingress for domain-based access

## Quick Start

### 1. Update Configuration

Before deploying, update the following:

**In `flask-api.yaml` and `celery-worker.yaml`:**
```yaml
image: your-registry.io/local-llm-celery:latest  # Change this
```

**In `configmap.yaml` - CRITICAL STEP:**

Choose based on your Ollama deployment:

```yaml
# Option 1: Local development (Ollama on your machine)
OLLAMA_HOST: "http://host.docker.internal:11434"

# Option 2: In-cluster (using ollama.yaml)
OLLAMA_HOST: "http://ollama:11434"

# Option 3: External service
OLLAMA_HOST: "http://your-ollama-server.com:11434"
```

**In `pvc.yaml`:**
```yaml
# storageClassName: standard  # Uncomment and set for your cluster
```

### 2. Deploy in Order

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Deploy Redis
kubectl apply -f redis.yaml

# Create ConfigMap (ensure OLLAMA_HOST is set correctly!)
kubectl apply -f configmap.yaml

# Create PVC for data
kubectl apply -f pvc.yaml

# Deploy Flask API
kubectl apply -f flask-api.yaml

# Deploy Celery Workers
kubectl apply -f celery-worker.yaml

# ONLY IF USING OPTION 2 (In-Cluster Ollama):
kubectl apply -f ollama.yaml

# (Optional) Setup Ingress
kubectl apply -f ingress.yaml
```

### 2a. If Using In-Cluster Ollama (Option 2)

After deploying `ollama.yaml`, you must pull the model:

```bash
# Wait for Ollama pod to be ready
kubectl wait --for=condition=ready pod -l app=ollama -n llm-analysis --timeout=300s

# Get the Ollama pod name
OLLAMA_POD=$(kubectl get pod -n llm-analysis -l app=ollama -o jsonpath='{.items[0].metadata.name}')

# Pull the llama3:8b model (this may take several minutes)
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama pull llama3:8b

# Verify the model is available
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama list
```

**Expected output:**
```
NAME            ID              SIZE      MODIFIED
llama3:8b       abc123def456    4.7 GB    2 minutes ago
```

### 3. Verify Deployment

```bash
kubectl get all -n llm-analysis
kubectl get pvc -n llm-analysis
```

### 4. Upload Data

```bash
# Get a Flask pod name
POD=$(kubectl get pod -n llm-analysis -l app=flask-api -o jsonpath='{.items[0].metadata.name}')

# Copy your CSV files
kubectl cp ../data/sales-data.csv llm-analysis/$POD:/app/data/sales-data.csv
```

### 5. Test the API

```bash
# Port forward to local machine
kubectl port-forward -n llm-analysis svc/flask-api 5001:5000

# In another terminal, test
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the median Avg_Price?", "filename": "sales-data.csv"}'
```

## Scaling

```bash
# Scale Flask API
kubectl scale deployment flask-api -n llm-analysis --replicas=3

# Scale Celery workers
kubectl scale deployment celery-worker -n llm-analysis --replicas=4
```

## Monitoring

```bash
# View worker logs
kubectl logs -n llm-analysis -l app=celery-worker --tail=50 -f

# Check resource usage
kubectl top pods -n llm-analysis

# Describe a pod for details
kubectl describe pod -n llm-analysis <pod-name>
```

## Troubleshooting Ollama Connectivity

### Check Ollama Connection from Worker

```bash
# Get a worker pod name
WORKER_POD=$(kubectl get pod -n llm-analysis -l app=celery-worker -o jsonpath='{.items[0].metadata.name}')

# Test connectivity to Ollama
kubectl exec -n llm-analysis $WORKER_POD -- curl -s http://ollama:11434/api/tags

# Or if using host.docker.internal:
kubectl exec -n llm-analysis $WORKER_POD -- curl -s http://host.docker.internal:11434/api/tags
```

**Expected output:** JSON response with model list

### Common Ollama Issues

**Problem: Worker logs show "Ollama not reachable"**

Solution 1 (In-Cluster Ollama):
```bash
# Check if Ollama pod is running
kubectl get pod -n llm-analysis -l app=ollama

# Check Ollama logs
kubectl logs -n llm-analysis -l app=ollama

# Verify model is pulled
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama list
```

Solution 2 (Local/External Ollama):
```bash
# Verify OLLAMA_HOST in ConfigMap
kubectl get configmap llm-config -n llm-analysis -o yaml

# Test from your local machine
curl http://localhost:11434/api/tags

# Check if host.docker.internal resolves from worker pod
kubectl exec -n llm-analysis $WORKER_POD -- nslookup host.docker.internal
```

**Problem: Model not found**

```bash
# List available models in Ollama
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama list

# If llama3:8b is missing, pull it
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama pull llama3:8b
```

**Problem: Ollama pod OOMKilled**

```bash
# Check pod events
kubectl describe pod -n llm-analysis -l app=ollama

# Increase memory limits in ollama.yaml:
# limits:
#   memory: "12Gi"  # Increase from 8Gi

# Reapply
kubectl apply -f ollama.yaml
```

## Cleanup

```bash
# Delete everything
kubectl delete namespace llm-analysis
```

## Production Considerations

### Security
- Use Secrets instead of ConfigMap for sensitive data
- Enable RBAC and network policies
- Use private container registry with pull secrets
- Enable pod security policies/standards

### High Availability
- Use multiple replicas for Flask API (already set to 2)
- Consider Redis Sentinel or Redis Cluster for HA
- Use pod anti-affinity to spread across nodes
- Set up horizontal pod autoscaling (HPA)

### Resource Management
- Adjust resource requests/limits based on actual usage
- Use LimitRanges and ResourceQuotas
- Monitor with Prometheus/Grafana
- Set up alerts for OOM events

### Storage
- Use ReadWriteMany storage class for shared data
- Consider using S3/GCS for large datasets
- Backup PVCs regularly
- Use StorageClass with appropriate performance tier

### Networking
- Use Ingress with TLS certificates
- Consider service mesh (Istio/Linkerd) for advanced routing
- Enable network policies for pod-to-pod communication
- Use external DNS for automatic domain management

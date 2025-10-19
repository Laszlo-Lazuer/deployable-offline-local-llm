# Ollama Deployment Options - Quick Reference

## Overview

The Local LLM Celery application **requires Ollama to be running** to process analysis tasks. This document helps you choose and configure the right Ollama deployment option.

## ⚠️ Important: CPU-Only Deployment

**This application is designed to run entirely on CPU without requiring GPU acceleration.**

- ✅ No GPU, CUDA, or specialized hardware required
- ✅ Works on standard CPU nodes (x86_64 or ARM64)
- ✅ Runs on any cloud provider without GPU instances
- ⚠️ Inference is slower than GPU (~5-10 tokens/sec CPU vs 50+ tokens/sec GPU)
- ✅ More cost-effective for low-to-medium throughput workloads

**While Ollama can optionally use GPU if available, all deployment instructions assume CPU-only environments.**

## Three Deployment Options

### 🔵 Option 1: Local Development
**Ollama runs on your laptop/workstation**

**When to use:**
- Local development and testing
- Quick prototyping
- Learning the system

**Configuration:**
```yaml
# k8s/configmap.yaml
OLLAMA_HOST: "http://host.docker.internal:11434"
```

**Setup:**
```bash
# On your local machine:
ollama serve

# Pull the model:
ollama pull llama3:8b

# Verify:
curl http://localhost:11434/api/tags
```

**Pros:**
- ✅ Easy to set up
- ✅ No cluster resources needed
- ✅ Can use your GPU if available (optional)
- ✅ Easy debugging with local logs

**Cons:**
- ❌ Not production-ready
- ❌ Requires node-to-host networking
- ❌ Single point of failure
- ❌ Doesn't work on all cloud providers

**Note**: This deployment works on CPU. GPU is optional and not required.

---

### 🟢 Option 2: In-Cluster Production
**Ollama runs as a pod inside Kubernetes**

**When to use:**
- Production deployments
- Self-contained clusters
- When you need portability
- Cloud environments without GPU

**Configuration:**
```yaml
# k8s/configmap.yaml
OLLAMA_HOST: "http://ollama:11434"
```

**Setup:**
```bash
# Deploy Ollama pod
kubectl apply -f k8s/ollama.yaml

# Wait for pod to start
kubectl wait --for=condition=ready pod -l app=ollama -n llm-analysis --timeout=300s

# Pull the model
OLLAMA_POD=$(kubectl get pod -n llm-analysis -l app=ollama -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama pull llama3:8b

# Verify
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama list
```

**Pros:**
- ✅ Self-contained deployment
- ✅ Works anywhere Kubernetes runs
- ✅ Easy to version control
- ✅ Good for CI/CD pipelines
- ✅ No special hardware requirements

**Cons:**
- ❌ Requires 4-8GB RAM per pod
- ❌ CPU-only inference (slower than GPU)
- ❌ Increases cluster costs
- ❌ No GPU acceleration (by design for portability)

**Resource Requirements:**
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

---

### 🟡 Option 3: External Service
**Ollama runs on dedicated servers outside Kubernetes**

**When to use:**
- Large-scale production
- Need GPU acceleration for performance (optional)
- Multiple applications sharing LLM
- Highest performance requirements

**Configuration:**
```yaml
# k8s/configmap.yaml
OLLAMA_HOST: "http://ollama.production.example.com:11434"
```

**Setup:**
```bash
# On your dedicated Ollama server:
ollama serve

# Pull the model:
ollama pull llama3:8b

# From Kubernetes, test connectivity:
WORKER_POD=$(kubectl get pod -n llm-analysis -l app=celery-worker -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n llm-analysis $WORKER_POD -- curl http://ollama.production.example.com:11434/api/tags
```

**Pros:**
- ✅ Best performance (especially with optional GPU)
- ✅ Shared across multiple apps
- ✅ Dedicated resources
- ✅ Easier to scale independently
- ✅ Can use GPU servers if needed (optional)

**Cons:**
- ❌ Requires separate infrastructure
- ❌ More complex networking
- ❌ Additional operational overhead
- ❌ Network latency considerations

**Note**: Can run on CPU or GPU servers. GPU is optional for better performance but not required.

---

## Decision Matrix

| Criteria | Option 1: Local | Option 2: In-Cluster | Option 3: External |
|----------|-----------------|----------------------|-------------------|
| **Setup Complexity** | 🟢 Easy | 🟡 Medium | 🔴 Complex |
| **Production Ready** | 🔴 No | 🟢 Yes | 🟢 Yes |
| **Performance** | 🟢 Good | 🟡 Medium | 🟢 Good-Best |
| **Cost** | 🟢 Free | 🟡 Cluster RAM | 🔴 Dedicated Infra |
| **Scalability** | 🔴 Limited | 🟡 Medium | 🟢 High |
| **Portability** | 🔴 Low | 🟢 High | 🟡 Medium |
| **GPU Required** | 🟢 No | 🟢 No | 🟢 No |
| **GPU Optional** | 🟢 Yes | 🟡 Complex | 🟢 Yes |

**All options work on CPU-only environments. GPU is never required.**

## Verification Checklist

After deploying Ollama, verify it's working:

### ✅ 1. Ollama Service is Running

**Local:**
```bash
curl http://localhost:11434/api/tags
```

**In-Cluster:**
```bash
kubectl get pod -n llm-analysis -l app=ollama
kubectl logs -n llm-analysis -l app=ollama --tail=20
```

**External:**
```bash
curl http://your-ollama-server.com:11434/api/tags
```

### ✅ 2. Model is Available

```bash
# Local:
ollama list

# In-Cluster:
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama list

# External:
ssh ollama-server "ollama list"
```

Expected output:
```
NAME            ID              SIZE      MODIFIED
llama3:8b       abc123def456    4.7 GB    2 minutes ago
```

### ✅ 3. Workers Can Connect

```bash
WORKER_POD=$(kubectl get pod -n llm-analysis -l app=celery-worker -o jsonpath='{.items[0].metadata.name}')

# Test based on your OLLAMA_HOST setting:
kubectl exec -n llm-analysis $WORKER_POD -- curl -s http://[YOUR-OLLAMA-HOST]:11434/api/tags
```

Should return JSON with model list.

### ✅ 4. End-to-End Test

```bash
# Submit a test task
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What is 2+2?", "filename": "sales-data.csv"}'

# Watch worker logs
kubectl logs -n llm-analysis -l app=celery-worker -f
```

Look for:
- "Loading llama3:8b..."
- "Model loaded."
- Python code execution
- Final result

## Troubleshooting

### Problem: "Ollama not reachable at any candidate host"

**Check ConfigMap:**
```bash
kubectl get configmap llm-config -n llm-analysis -o yaml
```

**Verify OLLAMA_HOST matches your deployment option**

### Problem: Connection refused

**Local Option:**
- Is Ollama running? `ps aux | grep ollama`
- Can nodes reach your host? Check firewall rules
- Try `host.containers.internal` instead of `host.docker.internal`

**In-Cluster Option:**
- Is pod running? `kubectl get pod -n llm-analysis -l app=ollama`
- Check service: `kubectl get svc ollama -n llm-analysis`

**External Option:**
- Network connectivity: `kubectl exec $WORKER_POD -- ping ollama.example.com`
- DNS resolution: `kubectl exec $WORKER_POD -- nslookup ollama.example.com`
- Firewall rules allowing port 11434

### Problem: Model not found

```bash
# Pull the model to Ollama:
ollama pull llama3:8b  # Local
kubectl exec -n llm-analysis $OLLAMA_POD -- ollama pull llama3:8b  # In-Cluster
```

## Performance Comparison

**All measurements below are for CPU-based inference (no GPU):**

| Metric | Local (CPU) | In-Cluster (CPU) | External (CPU) | External (GPU)* |
|--------|-------------|------------------|----------------|-----------------|
| **First Token** | ~1000ms | ~2000ms | ~1000ms | ~200ms |
| **Tokens/sec** | ~5-10 | ~5-10 | ~5-10 | ~50-100 |
| **Concurrent Tasks** | 1-2 | 1 per pod | Many | Many |
| **Model Load Time** | 10-20s | 20-30s | 10-20s | 5s |

*GPU performance shown for comparison - **GPU is optional and not part of the base deployment***

**Note**: Numbers are approximate and vary by hardware. All deployment options work on CPU.

## Migration Guide

### From Local → In-Cluster

1. Deploy Ollama: `kubectl apply -f k8s/ollama.yaml`
2. Pull model: `kubectl exec $OLLAMA_POD -- ollama pull llama3:8b`
3. Update ConfigMap: Change OLLAMA_HOST to `http://ollama:11434`
4. Restart workers: `kubectl rollout restart deployment celery-worker -n llm-analysis`

### From In-Cluster → External

1. Set up dedicated Ollama server
2. Pull model on external server: `ollama pull llama3:8b`
3. Update ConfigMap: Change OLLAMA_HOST to external URL
4. Restart workers: `kubectl rollout restart deployment celery-worker -n llm-analysis`
5. Remove in-cluster Ollama: `kubectl delete -f k8s/ollama.yaml`

## Best Practices

1. **Development**: Start with Option 1 (Local) on CPU
2. **Staging**: Use Option 2 (In-Cluster) to match production on CPU
3. **Production**: Choose based on scale and requirements:
   - Small (<10 concurrent users): Option 2 (In-Cluster CPU)
   - Large (>10 concurrent users): Option 3 (External, CPU or GPU)

4. **Always verify** connectivity after deployment
5. **Monitor** Ollama resource usage (especially RAM and CPU)
6. **Consider** multiple Ollama replicas for high availability
7. **Use** readiness probes to ensure model is loaded
8. **GPU is optional** - only add if you need higher throughput and can justify the cost

## Support

For more help:
- Main README: [README.md](../README.md)
- K8s Guide: [k8s/README.md](k8s/README.md)
- Ollama Docs: https://ollama.ai/docs

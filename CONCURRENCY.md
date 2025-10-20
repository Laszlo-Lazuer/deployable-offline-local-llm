# Celery Concurrency Configuration

## Overview

The Celery worker is configured with **concurrency=1** to ensure tasks are processed **sequentially** rather than in parallel.

## Why Sequential Processing?

### CPU Resource Management

When multiple LLM inference tasks run concurrently on CPU:
- ❌ Both tasks compete for CPU cycles
- ❌ Each task runs **2-3x slower**
- ❌ Total completion time is longer
- ❌ Unpredictable performance

With sequential processing (concurrency=1):
- ✅ One task gets **full CPU resources**
- ✅ Consistent **5-10 min** completion time
- ✅ Predictable queue behavior
- ✅ Better resource utilization

### Real-World Example

**Scenario**: Two median price queries submitted

**With concurrency=4 (default)**:
```
Task 1: Started at 02:32:58, Still running at 02:47:00 (15+ min)
Task 2: Started at 02:35:38, Still running at 02:47:00 (12+ min)
Total: 15+ minutes for both tasks
```

**With concurrency=1**:
```
Task 1: Started at 02:32:58, Completed at 02:38:22 (5m24s) ✅
Task 2: Started at 02:38:23, Completed at 02:43:50 (5m27s) ✅
Total: ~11 minutes for both tasks (30% faster!)
```

## Configuration

### Current Setup

**File**: `docker-compose.yml`
```yaml
worker:
  command: celery -A worker.celery_app worker --loglevel=info --concurrency=1
```

### Verification

Check worker concurrency:
```bash
podman logs worker | grep "concurrency"
```

Expected output:
```
- *** --- * --- .> concurrency: 1 (prefork)
```

## Alternative Configurations

### For GPU Deployment

GPU inference is much faster (~50-100 tokens/sec), so you may want higher concurrency:

```yaml
worker:
  command: celery -A worker.celery_app worker --loglevel=info --concurrency=2
```

**Benefits with GPU**:
- Tasks complete in ~1 minute
- GPU can handle multiple tasks efficiently
- Less queue waiting time

**Recommended**:
- **CPU mode**: `--concurrency=1` (default)
- **GPU mode**: `--concurrency=2` or `--concurrency=4`

### Environment Variable Approach

You can also set concurrency via environment variable:

```yaml
worker:
  environment:
    - CELERYD_CONCURRENCY=1
  command: celery -A worker.celery_app worker --loglevel=info
```

### Dynamic Concurrency

To change concurrency without rebuilding:

```bash
# Stop services
podman-compose down

# Edit docker-compose.yml and change --concurrency=X

# Restart
podman-compose up -d
```

## Performance Impact

### Task Queue Behavior

**With concurrency=1**:
```
Queue: [Task1, Task2, Task3]
→ Task1 runs (5 min) → Complete
→ Task2 runs (5 min) → Complete
→ Task3 runs (5 min) → Complete
Total: 15 minutes
```

**With concurrency=3**:
```
Queue: [Task1, Task2, Task3]
→ All 3 start simultaneously
→ CPU thrashing, context switching
→ Task1 completes (12 min)
→ Task2 completes (13 min)
→ Task3 completes (14 min)
Total: 14 minutes (only 1 min faster, much less predictable)
```

### CPU Utilization

- **Concurrency=1**: 100% CPU per task, serial execution
- **Concurrency>1**: 100% CPU total, divided among tasks

### When to Increase Concurrency

✅ **Increase concurrency when**:
- Using GPU acceleration (faster inference)
- Tasks are I/O bound (network requests, file operations)
- You have many CPU cores (8+) dedicated to the worker

❌ **Keep concurrency=1 when**:
- Using CPU-only inference
- Limited CPU resources (2-4 cores)
- Predictable completion times are important
- You want to avoid resource contention

## Monitoring

### Check Active Tasks

```bash
# View worker logs
podman logs worker --tail 50

# Check task status
curl http://localhost:5001/status/<task_id>

# Monitor Redis queue
podman exec redis redis-cli LLEN celery
```

### Queue Length

```bash
# Check number of pending tasks
podman exec redis redis-cli LLEN celery
```

If queue grows too large with concurrency=1, consider:
1. Adding more worker containers
2. Switching to GPU mode
3. Increasing concurrency (only if using GPU)

## Scaling Options

### Horizontal Scaling (Recommended)

Instead of increasing concurrency, add more worker containers:

```yaml
# docker-compose.yml
worker-1:
  build: .
  container_name: worker-1
  command: celery -A worker.celery_app worker --loglevel=info --concurrency=1

worker-2:
  build: .
  container_name: worker-2
  command: celery -A worker.celery_app worker --loglevel=info --concurrency=1
```

**Benefits**:
- Each worker gets dedicated resources
- Better fault isolation
- Linear scaling (2 workers = 2x throughput)
- No resource contention

### Vertical Scaling

If you have a powerful machine:

```bash
# Give worker more CPU
podman-compose down
# Edit docker-compose.yml to add:
#   resources:
#     limits:
#       cpus: "4.0"
podman-compose up -d
```

Then you can safely increase concurrency to match CPU allocation.

## Troubleshooting

### Symptom: Tasks taking 10-15+ minutes

**Cause**: Multiple tasks running concurrently, competing for CPU

**Solution**: Ensure `--concurrency=1` is set in docker-compose.yml

### Symptom: Tasks stuck in PENDING

**Cause**: Worker not running or crashed

**Solution**:
```bash
podman logs worker --tail 100
podman-compose restart worker
```

### Symptom: Queue growing but tasks not starting

**Cause**: Worker might be overwhelmed

**Solution**:
```bash
# Check worker status
podman logs worker | grep "ready"

# Restart worker
podman-compose restart worker
```

## Best Practices

1. ✅ **Use concurrency=1 for CPU mode** (default)
2. ✅ **Scale horizontally** by adding more workers
3. ✅ **Switch to GPU mode** for better throughput
4. ✅ **Monitor queue length** and adjust if needed
5. ❌ **Don't increase concurrency on CPU** without testing
6. ❌ **Don't expect linear scaling** with higher concurrency on CPU

## See Also

- **[PERFORMANCE.md](PERFORMANCE.md)** - CPU vs GPU performance comparison
- **[GPU.md](GPU.md)** - GPU setup and configuration
- **[README.md](README.md)** - Main project documentation
- **[TECH-STACK.md](TECH-STACK.md)** - Technology overview

---

**Last Updated**: October 19, 2025  
**Default Configuration**: `--concurrency=1` (CPU mode)

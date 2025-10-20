# Context Window Configuration (8K)

## Overview

This application is configured to use an **8K context window** (8192 tokens) instead of the default 4K (4096 tokens). This prevents prompt truncation when processing large datasets or complex multi-file queries.

## Why 8K Context?

**Problem with default 4K context:**
```
[W] prompt_truncated: ... tokens were truncated from the prompt
```

**Symptoms:**
- Truncation warnings in Ollama logs
- Incomplete analysis results
- Missing data when combining multiple files
- Errors with long column lists or large schemas

**Solution with 8K context:**
- ✅ No truncation warnings
- ✅ Full dataset schemas included in prompts
- ✅ Multi-file analysis works reliably
- ✅ Complex queries with detailed instructions succeed

## Configuration

### 1. Create Modelfile

```bash
cat > Modelfile << 'EOF'
FROM llama3:8b
PARAMETER num_ctx 8192
PARAMETER temperature 0.7
PARAMETER top_p 0.9
EOF
```

### 2. Build Model with 8K Context

```bash
ollama create llama3:8b -f Modelfile
```

### 3. Verify Configuration

```bash
# Check model exists
ollama list

# Start a query and check Ollama logs
podman logs ollama --tail 50 | grep n_ctx
```

**Expected output:**
```
n_ctx = 8192
n_ctx_per_seq = 8192
KV buffer size = 1024.00 MiB
8192 cells, 32 layers
```

## Technical Details

### Memory Impact

| Context Size | KV Cache Memory | Cells | Performance Impact |
|--------------|----------------|-------|-------------------|
| 4K (default) | 512 MiB | 4096 | Lower memory, may truncate |
| 8K (configured) | 1024 MiB | 8192 | Double memory, no truncation |

**Trade-off:** 8K context uses ~500MB more RAM but prevents truncation issues.

### Worker Configuration

The worker is already configured to request 8K context:

```python
# worker.py lines 101-103
interpreter.llm.num_ctx = 8192
interpreter.llm.api_params = {"num_ctx": 8192}
```

However, **Ollama must be configured to support 8K** via the Modelfile. Without it, Ollama will load models with 4K context by default, regardless of the worker's request.

## Troubleshooting

### Issue: Still seeing truncation warnings

**Diagnosis:**
```bash
# Check what context Ollama is using
podman logs ollama 2>&1 | grep -E "n_ctx|truncat"
```

**If you see `n_ctx = 4096`:**
1. Rebuild the model: `ollama create llama3:8b -f Modelfile`
2. Restart services: `podman-compose restart ollama worker`
3. Verify: `podman logs ollama --tail 50 | grep n_ctx`

### Issue: Out of memory errors with 8K

**Solution:** Reduce to 6K context:
```bash
# In Modelfile
PARAMETER num_ctx 6144

# And in worker.py
interpreter.llm.num_ctx = 6144
interpreter.llm.api_params = {"num_ctx": 6144}
```

6K provides good balance (768 MiB KV cache, 6144 cells).

## When to Use Different Context Sizes

| Use Case | Recommended Context | Reason |
|----------|-------------------|---------|
| Single small CSV (<100 rows) | 4K | Sufficient, saves memory |
| Multi-file analysis | 8K+ | Prevents truncation |
| Large datasets (1000+ rows) | 8K+ | Full schema + samples |
| API integration queries | 8K+ | Room for instructions + data |
| Simple statistical queries | 4K | Basic operations don't need more |

## Related Documentation

- [CONCURRENCY.md](CONCURRENCY.md) - Sequential processing optimization
- [PERFORMANCE.md](PERFORMANCE.md) - CPU vs GPU performance comparison
- [MULTI-FILE-ANALYSIS.md](MULTI-FILE-ANALYSIS.md) - Why multi-file needs 8K

## Verification Script

```bash
#!/bin/bash
# verify-context.sh - Check if 8K context is active

echo "Checking Ollama context configuration..."
echo

# Submit test query
TASK=$(curl -s -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"question":"What is 2+2?"}' | jq -r .task_id)

echo "Task ID: $TASK"
echo "Waiting for model to load..."
sleep 10

# Check Ollama logs
echo
echo "Ollama Context Configuration:"
podman logs ollama 2>&1 | tail -50 | grep -E "n_ctx|KV buffer|cells" | head -3

# Check for truncation warnings
TRUNCATED=$(podman logs ollama 2>&1 | tail -100 | grep -c "truncat")

echo
if [ "$TRUNCATED" -gt 0 ]; then
  echo "❌ WARNING: Found $TRUNCATED truncation warnings"
  echo "   Solution: Rebuild model with Modelfile"
else
  echo "✅ No truncation warnings found"
fi

# Check n_ctx value
CTX=$(podman logs ollama 2>&1 | tail -50 | grep "n_ctx         =" | tail -1 | awk '{print $3}')

echo
if [ "$CTX" = "8192" ]; then
  echo "✅ Context configured correctly: 8K ($CTX tokens)"
elif [ "$CTX" = "4096" ]; then
  echo "❌ Context too small: 4K ($CTX tokens)"
  echo "   Solution: Run 'ollama create llama3:8b -f Modelfile'"
else
  echo "⚠️  Unknown context size: $CTX"
fi
```

**Usage:**
```bash
chmod +x verify-context.sh
./verify-context.sh
```

## Summary

✅ **8K context is now the default** for this application
✅ Prevents truncation with multi-file analysis
✅ Requires ~1GB KV cache (acceptable trade-off)
✅ Configured via Modelfile + worker.py
✅ Verified via Ollama logs (`n_ctx = 8192`)

The 8K configuration provides the best balance of functionality and resource usage for data analysis workloads.

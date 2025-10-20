# Multi-File Analysis

## Overview

The Local LLM Celery system automatically provides the LLM with access to **all uploaded data files**, enabling sophisticated multi-file analysis without requiring users to explicitly specify which files to use.

## How It Works

### Automatic File Discovery

When you submit an analysis request, the worker:

1. **Scans the data directory** (`/app/data`) for all available files
2. **Lists files in the prompt** with their names and sizes
3. **Gives the LLM full access** to load any combination of files needed
4. **Executes Python code** that can read, merge, and analyze multiple datasets

### Prompt Context

The LLM receives information about all available files:

```
Available data files in /app/data:
  - sales-data.csv (3,233 bytes)
  - q2-sales.csv (204 bytes)
  - inventory.csv (15,482 bytes)
```

The LLM can then write Python code to load and work with any of these files as needed.

## Usage Examples

### Single File Analysis (Traditional)

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the median Avg_Price?",
    "filename": "sales-data.csv"
  }'
```

The `filename` parameter specifies the **primary file** for analysis.

### Multi-File Analysis (Automatic)

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total combined revenue from all CSV files?"
  }'
```

**No filename specified** - the LLM will automatically:
- Use the first available file as the primary reference
- Have access to all other files in the data directory
- Load and combine files as needed to answer the question

### Explicit Multi-File Instructions

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Load sales-data.csv and q2-sales.csv, combine them, and calculate total revenue"
  }'
```

You can explicitly name multiple files in your question for clarity.

### Cross-File Comparison

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare average prices between sales-data.csv and q2-sales.csv"
  }'
```

### Joining Datasets

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Join sales-data.csv with inventory.csv on the City column and show total inventory value by city"
  }'
```

## Python Client Example

```python
import requests
import time

def analyze_multi_file(question):
    """Submit a multi-file analysis query."""
    response = requests.post(
        "http://localhost:5001/analyze",
        json={"question": question}
    )
    task_id = response.json()["task_id"]
    
    # Poll for result
    while True:
        status = requests.get(f"http://localhost:5001/status/{task_id}").json()
        if status["status"] == "SUCCESS":
            return status["result"]
        elif status["status"] == "FAILURE":
            raise Exception(f"Task failed: {status.get('error')}")
        time.sleep(2)

# Example usage
result = analyze_multi_file(
    "Calculate total revenue across all uploaded CSV files and show the breakdown by file"
)
print(result)
```

## Testing Multi-File Analysis

### 1. Upload Multiple Files

```bash
# Upload first file
make data-upload FILE=data/sales-data.csv

# Upload second file
make data-upload FILE=/tmp/q2-sales.csv

# Verify both files are uploaded
make data-list
```

Expected output:
```json
{
    "count": 2,
    "files": [
        {"filename": "sales-data.csv", "size_bytes": 3233},
        {"filename": "q2-sales.csv", "size_bytes": 204}
    ]
}
```

### 2. Run Multi-File Query

```bash
make test-multi
```

Or manually:
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Load all CSV files and calculate the total combined revenue from all files."
  }'
```

### 3. Check Results

```bash
# Get task ID from previous response
curl http://localhost:5001/status/<task_id> | python3 -m json.tool
```

## Real-World Use Cases

### 1. Time-Series Analysis Across Periods

```bash
# Upload Q1, Q2, Q3, Q4 sales files
make data-upload FILE=data/q1-sales.csv
make data-upload FILE=data/q2-sales.csv
make data-upload FILE=data/q3-sales.csv
make data-upload FILE=data/q4-sales.csv

# Analyze year-over-year trends
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Load all quarterly sales files, combine them, and show monthly revenue trends for the entire year"
  }'
```

### 2. Multi-Source Data Integration

```bash
# Upload different data sources
make data-upload FILE=data/sales.csv
make data-upload FILE=data/inventory.csv
make data-upload FILE=data/customers.csv

# Join and analyze
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Join sales with inventory and customers data to calculate customer lifetime value by region"
  }'
```

### 3. Comparative Analysis

```bash
# Upload current and previous year data
make data-upload FILE=data/2023-sales.csv
make data-upload FILE=data/2024-sales.csv

# Compare performance
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare revenue growth between 2023-sales.csv and 2024-sales.csv, show percentage increase by category"
  }'
```

## Technical Details

### File Discovery Implementation

In `worker.py`:

```python
@celery_app.task
def run_analysis_task(question, filename):
    data_dir = "/app/data"
    file_path = os.path.join(data_dir, filename)
    
    # Get list of all available data files
    available_files = []
    if os.path.exists(data_dir):
        available_files = [f for f in os.listdir(data_dir) 
                          if os.path.isfile(os.path.join(data_dir, f))]
```

### LLM Prompt Context

The prompt includes:
- Primary file path (if specified)
- List of all available files with sizes
- Instructions that the LLM can access any file
- Guidance to load/combine files as needed

```python
files_context = f"\nAvailable data files in {data_dir}:\n"
for f in available_files:
    file_size = os.path.getsize(os.path.join(data_dir, f))
    files_context += f"  - {f} ({file_size:,} bytes)\n"

full_prompt = f"""
You are a data analyst with access to multiple data files.

Primary file for this analysis: '{file_path}'
{files_context}

User question: "{question}"

Instructions:
1. You can load and work with ANY of the available data files as needed
2. Use pandas to load CSV files: pd.read_csv('/app/data/filename.csv')
3. If the question requires data from multiple files, load and combine them
...
"""
```

## Limitations

### Current Constraints

1. **File Format**: The LLM works best with CSV, JSON, and structured text files
2. **Memory**: All files must fit in worker container memory (configured in K8s deployment)
3. **Processing Time**: Multi-file analysis takes longer than single-file queries
4. **Volume Mount**: All files must be in the shared `/app/data` volume

### Recommended Practices

1. **Keep files reasonably sized** - Large files (>100MB) may cause timeouts
2. **Use clear filenames** - Helps the LLM understand which files to use
3. **Be specific in questions** - "Compare revenue in sales-data.csv vs q2-sales.csv" is better than "compare revenues"
4. **Monitor worker resources** - Scale workers horizontally for heavy multi-file workloads

## Performance Considerations

### Single File
- **Processing Time**: ~10-30 seconds for typical queries
- **Memory Usage**: Low (~200-500MB)
- **Token Usage**: ~500-2000 tokens

### Multi-File (2-3 files)
- **Processing Time**: ~20-60 seconds (depends on file sizes and complexity)
- **Memory Usage**: Medium (~500MB-2GB)
- **Token Usage**: ~1000-4000 tokens

### Multi-File (4+ files)
- **Processing Time**: ~60-120 seconds
- **Memory Usage**: High (~2-4GB)
- **Token Usage**: ~2000-8000 tokens
- **Recommendation**: Consider increasing worker replicas and resources

## Scaling for Multi-File Workloads

### Kubernetes Resource Adjustments

If you frequently analyze multiple large files, increase worker resources:

```yaml
# k8s/celery-worker.yaml
resources:
  requests:
    memory: "2Gi"    # Increased from 1Gi
    cpu: "1000m"     # Increased from 500m
  limits:
    memory: "8Gi"    # Increased from 4Gi
    cpu: "4000m"     # Increased from 2000m
```

### Horizontal Scaling

Increase worker replicas for parallel processing:

```yaml
spec:
  replicas: 4  # Increased from 2
```

### Redis Configuration

For high-throughput multi-file analysis:

```yaml
# k8s/redis.yaml
resources:
  requests:
    memory: "256Mi"  # Increased from 128Mi
  limits:
    memory: "1Gi"    # Increased from 512Mi
```

## Troubleshooting

### LLM Doesn't Use Multiple Files

**Problem**: LLM only uses one file despite being asked to use multiple.

**Solution**: Be more explicit in your question:
```bash
# Instead of:
"Compare revenue across files"

# Use:
"Load both sales-data.csv AND q2-sales.csv, combine them using pandas concat, then calculate total revenue"
```

### Out of Memory Errors

**Problem**: Worker crashes when loading multiple large files.

**Solution**:
1. Increase worker memory limits in K8s deployment
2. Process files separately and ask for summarized results
3. Consider pre-processing large files into smaller chunks

### Slow Multi-File Queries

**Problem**: Queries take 2+ minutes to complete.

**Solution**:
1. Verify CPU-only inference is expected to be slower
2. Increase worker CPU allocation
3. Consider deploying Ollama on GPU servers (Option 3)
4. Scale out workers horizontally

## See Also

- [Data Management API](DATA-API.md) - Upload, update, delete data files
- [README](README.md) - Main project documentation
- [Ollama Deployment Options](OLLAMA-DEPLOYMENT.md) - Performance tuning

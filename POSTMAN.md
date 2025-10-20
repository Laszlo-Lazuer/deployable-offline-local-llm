# Postman Collection Guide

This directory contains a Postman collection for testing the LLM Data Analyst API.

## 📥 Import the Collection

### Option 1: Import from File
1. Open Postman
2. Click **Import** button
3. Select `postman_collection.json` from this repository
4. Collection will appear in your workspace

### Option 2: Import from URL (if hosted on GitHub)
1. Open Postman
2. Click **Import** → **Link**
3. Paste the raw GitHub URL:
   ```
   https://raw.githubusercontent.com/Laszlo-Lazuer/local-llm-celery/main/postman_collection.json
   ```
4. Click **Continue** → **Import**

## 🎯 Collection Structure

The collection is organized into 5 main folders:

### 1. **Health & Status** (3 requests)
- **Health Check** - Verify API is running
- **Get Task Status** - Check status of a submitted task
- **Stream Task Progress (SSE)** - Real-time streaming updates

### 2. **File Management** (2 requests)
- **List Available Files** - See all files in `/data` directory
- **Upload File** - Upload new CSV/TSV/JSON files

### 3. **Data Analysis - Single File** (7 requests)
Basic queries on a single file:
- Simple Query (median)
- Aggregation (total revenue)
- Grouping (sales by country)
- Top N (highest revenue venues)
- Statistical Analysis (correlation)
- Calculation (revenue per attendee)
- TSV File Query

### 4. **Data Analysis - Multiple Files** (5 requests)
Queries spanning multiple files:
- Compare Two Files
- Multi-File Attendance Differences
- Merge Multiple Files
- Cross-File Analysis
- Multi-File Top N

### 5. **Advanced Queries** (4 requests)
Complex analysis examples:
- Monthly Trends
- Data Quality Checks
- Conditional Analysis
- Percentile Analysis

## ⚙️ Environment Variables

The collection uses 2 variables:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:5001` | API base URL |
| `task_id` | (auto-set) | Task ID from analysis requests |

### Setting Up Environment

1. Create a new environment in Postman called "Local LLM"
2. Add variable `base_url` with value `http://localhost:5001`
3. Select this environment when using the collection

**Or** use the default collection-level variables (no environment needed).

## 🚀 Quick Start

### 1. Start the Services
```bash
podman-compose up -d
```

### 2. Check Health
Run the **Health Check** request to verify services are running.

Expected response:
```json
{
  "status": "healthy"
}
```

### 3. List Available Files
Run **List Available Files** to see what data files are available.

### 4. Submit an Analysis
Run any analysis request, e.g., **Simple Query - Median Price**

Response (202 Accepted):
```json
{
  "task_id": "a529a275-fb80-4ddb-ae34-1df33a0c0bf9"
}
```

The `task_id` is **automatically saved** to the environment variable.

### 5. Check Task Status
Run **Get Task Status** to see if the task completed.

Response when complete:
```json
{
  "status": "SUCCESS",
  "result": "The median Avg_Price is: 112.485",
  "task_id": "a529a275-fb80-4ddb-ae34-1df33a0c0bf9"
}
```

### 6. Stream Real-Time Progress (Optional)
For long-running tasks, use **Stream Task Progress (SSE)** to see live updates.

⚠️ **Note**: Postman's SSE support is limited. For better streaming experience, use:
- Web UI: http://localhost:5001/
- cURL: `curl -N http://localhost:5001/status/{task_id}/stream`
- Browser EventSource API

## 📝 Example Workflow

### Single File Analysis
```
1. Health Check (verify API is up)
2. List Available Files (see files)
3. Simple Query - Median Price (submit task)
   → task_id auto-saved
4. Get Task Status (check result)
```

### Multi-File Analysis
```
1. Health Check
2. List Available Files
3. Compare Two Files - Revenue (submit task)
   → Uses sales-data.csv + concert-sales.csv
4. Stream Task Progress (watch real-time updates)
5. Get Task Status (final result)
```

### Upload and Analyze New File
```
1. Upload File (POST with form-data)
2. List Available Files (verify upload)
3. Any analysis request with new filename
4. Get Task Status
```

## 🎨 Customizing Requests

### Modify Questions
Edit the `question` field in request body:
```json
{
  "question": "Your custom question here",
  "filename": "sales-data.csv"
}
```

### Add Additional Files
Include multiple files in analysis:
```json
{
  "question": "Compare revenue across all datasets",
  "filename": "sales-data.csv",
  "additional_files": ["concert-sales.csv", "q2-sales.csv"]
}
```

### Change File Selection
Update `filename` to any file from `/data`:
- `sales-data.csv`
- `concert-sales.csv`
- `q2-sales.csv`
- `test-sales.tsv`
- `test-sales.json`

## 🔧 Test Scripts

Analysis requests include automatic test scripts that:
1. Check for 202 Accepted status
2. Extract `task_id` from response
3. Save to environment variable `{{task_id}}`

This allows you to:
1. Run an analysis request
2. Immediately run "Get Task Status" using the saved `task_id`

## 📊 Response Formats

### Pending Task
```json
{
  "status": "PENDING",
  "result": null,
  "task_id": "..."
}
```

### Successful Task
```json
{
  "status": "SUCCESS",
  "result": "The median Avg_Price is: 112.485",
  "task_id": "..."
}
```

### Failed Task
```json
{
  "status": "FAILURE",
  "error": "Error message here",
  "task_id": "..."
}
```

### SSE Stream (Server-Sent Events)
```
data: {"status": "PENDING", "progress": "Starting analysis...", "timestamp": 1760924877.7}

data: {"status": "PENDING", "progress": "Generating code...", "timestamp": 1760925153.4}

data: {"status": "SUCCESS", "progress": "Complete", "result": "...", "timestamp": 1760925196.9}
```

## 🐛 Troubleshooting

### "Could not get any response"
- Verify services are running: `podman-compose ps`
- Check health endpoint works
- Verify `base_url` is correct (`http://localhost:5001`)

### Task stays PENDING forever
- Check worker logs: `podman logs worker --tail 50`
- Verify Ollama is running: `podman logs ollama --tail 50`
- Check Redis is accessible

### File not found errors
- Run "List Available Files" to see what's available
- Ensure filename in request matches exactly (case-sensitive)
- Upload file first if needed

### Long response times
- Normal for LLM queries: 4-7 minutes on CPU
- Use streaming endpoint to see progress
- Consider GPU acceleration for faster responses

## 📚 Additional Resources

- **Web UI**: http://localhost:5001/
- **API Documentation**: See README.md
- **Test Script**: `test_streaming.sh` for CLI streaming
- **Health Check**: http://localhost:5001/status/health

## 💡 Tips

1. **Auto-save task IDs**: Test scripts automatically save `task_id` for you
2. **Use streaming**: For tasks >1 minute, use SSE streaming endpoint
3. **Check logs**: `podman logs worker` shows LLM generation progress
4. **Multiple files**: Use `additional_files` array for multi-file analysis
5. **Natural language**: Questions can be conversational, LLM understands context

## 🎯 Next Steps

- Try different question phrasings
- Experiment with multi-file analysis
- Upload your own datasets
- Combine multiple aggregations in one question
- Test complex statistical queries

---

**Happy Testing!** 🚀

For issues or questions, see the main README.md or check the logs.

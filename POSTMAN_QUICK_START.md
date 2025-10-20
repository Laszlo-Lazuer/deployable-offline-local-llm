# Postman Collection - Quick Start

## 🚀 Import & Test in 60 Seconds

### 1. Import
```
Postman → Import → postman_collection.json
```

### 2. Test Health
```
Run: Health Check
Expect: {"status": "healthy"}
```

### 3. Run Your First Analysis
```
Run: Simple Query - Median Price
Response: {"task_id": "abc-123..."}
```

### 4. Check Result
```
Run: Get Task Status
Response: {"status": "SUCCESS", "result": "The median Avg_Price is: 112.485"}
```

## 📁 Collection Structure

```
LLM Data Analyst API/
├── Health & Status/
│   ├── Health Check
│   ├── Get Task Status
│   └── Stream Task Progress (SSE)
├── File Management/
│   ├── List Available Files
│   └── Upload File
├── Data Analysis - Single File/
│   ├── Simple Query - Median Price
│   ├── Aggregation - Total Revenue
│   ├── Grouping - Sales by Country
│   ├── Top N - Highest Revenue Venues
│   ├── Statistical Analysis - Correlation
│   ├── Calculation - Revenue Per Attendee
│   └── TSV File Query
├── Data Analysis - Multiple Files/
│   ├── Compare Two Files - Revenue
│   ├── Multi-File - Attendance Differences
│   ├── Merge Multiple Files
│   ├── Cross-File Analysis - Common Cities
│   └── Multi-File - Top N Analysis
└── Advanced Queries/
    ├── Complex Aggregation - Monthly Trends
    ├── Data Quality - Find Missing Values
    ├── Conditional Analysis - Filter and Aggregate
    └── Percentile Analysis
```

## 🎯 Example Questions You Can Ask

### Simple
- "What is the median Avg_Price?"
- "What is the total revenue?"
- "How many concerts in the dataset?"

### Grouping
- "What are the total sales by country?"
- "Show me revenue by venue"
- "Group concerts by month"

### Analysis
- "Which city had the highest revenue?"
- "Top 5 venues by attendance"
- "What's the correlation between price and attendance?"

### Multi-File
- "Compare revenue between sales-data.csv and concert-sales.csv"
- "Which cities appear in both files?"
- "Combine all files and show total revenue"

## 📊 Typical Response Times

- Health Check: < 100ms
- File List: < 200ms
- Analysis Task Submit: < 500ms
- Task Completion: 4-7 minutes (CPU-based LLM)

## 💡 Pro Tips

1. **Auto-saved task IDs**: Requests automatically save task_id to environment
2. **Use streaming**: For real-time progress updates
3. **Check logs**: `podman logs worker` shows detailed execution
4. **Natural language**: Ask questions conversationally
5. **Multiple files**: Use `additional_files` array

## 📚 Full Documentation

- **Detailed Guide**: [POSTMAN.md](POSTMAN.md)
- **API Reference**: [README.md](README.md)
- **Data Management**: [DATA-API.md](DATA-API.md)

---

**Ready to test?** Import the collection and start with "Health Check"! 🎉

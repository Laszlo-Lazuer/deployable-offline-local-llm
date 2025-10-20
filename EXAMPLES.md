# Query Examples & Use Cases

This document provides comprehensive examples of queries you can run against your data, from simple statistics to complex predictive analysis with live data fetching.

## Table of Contents

1. [Basic Statistics](#basic-statistics)
2. [Data Filtering & Grouping](#data-filtering--grouping)
3. [Multi-File Analysis](#multi-file-analysis)
4. [Predictive Analysis](#predictive-analysis)
5. [Live Data Integration](#live-data-integration)
6. [Advanced Analytics](#advanced-analytics)

---

## Basic Statistics

### Calculate Median Price

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the median Avg_Price?",
    "filename": "sales-data.csv"
  }'
```

**Expected Output:**
```json
{
  "task_id": "73208592-a4c1-4d56-819f-9eaba5623ffc",
  "status": "SUCCESS",
  "result": "The median Avg_Price is: 112.48"
}
```

### Total Revenue

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total Revenue across all events?",
    "filename": "sales-data.csv"
  }'
```

**Expected Output:**
```json
{
  "status": "SUCCESS",
  "result": "The total revenue across all events is $70,182,767.00"
}
```

### Average Attendance

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate the average attendance per event",
    "filename": "sales-data.csv"
  }'
```

---

## Data Filtering & Grouping

### Filter by City

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me all events in Chicago and calculate total revenue for that city",
    "filename": "sales-data.csv"
  }'
```

### Group by Month

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Group events by month and show average revenue per month",
    "filename": "sales-data.csv"
  }'
```

### Top Performers

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which city had the highest attendance? Show top 5 cities by total attendance.",
    "filename": "sales-data.csv"
  }'
```

---

## Multi-File Analysis

### Compare Two Datasets

**Setup:**
```bash
# Upload Q1 data
make data-upload FILE=data/q1-sales.csv

# Upload Q2 data
make data-upload FILE=data/q2-sales.csv
```

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare total revenue between q1-sales.csv and q2-sales.csv. Which quarter performed better?"
  }'
```

### Aggregate Across All Files

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Load all CSV files in the data directory and calculate the combined total revenue across all files"
  }'
```

**Expected Output:**
```json
{
  "status": "SUCCESS",
  "result": "Total combined revenue from all files: $70,182,767.00 (from 2 files: sales-data.csv and q2-sales.csv)"
}
```

### Cross-File Join

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Join sales-data.csv with venue-info.csv on the Venue column and calculate revenue by venue capacity"
  }'
```

---

## Predictive Analysis

### Method 1: Using Assumed Inflation Rates (Fast)

Perfect for quick estimates and scenarios where exact historical rates aren't critical.

#### Simple Inflation Adjustment

**Query:**
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
  "task_id": "af99004f-5e01-4963-8e72-65b3d59cb307",
  "status": "SUCCESS",
  "result": "The average ticket price for Chicago events is approximately $119.85 and the expected ticket price in 2026 after applying a 3% annual inflation rate for 7 years is approximately $147.40."
}
```

**Calculation Details:**
```
Historical Average (Chicago): $119.85
Years: 2019 → 2026 = 7 years
Inflation Rate: 3% per year (compound)
Inflation Factor: (1.03)^7 = 1.2299
2026 Expected Price: $119.85 × 1.2299 = $147.40
Increase: 23% over 7 years
```

#### Multi-City Projections

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate 2026 expected ticket prices for Chicago, New York, and Los Angeles. Use historical average prices and 3% annual inflation. Show results in a table.",
    "filename": "sales-data.csv"
  }'
```

**Expected Output:**
```
City          2019 Avg Price    2026 Projected    Increase
Chicago       $119.85          $147.40           23.0%
New York      $145.20          $178.60           23.0%
Los Angeles   $132.50          $162.96           23.0%
```

#### Different Inflation Scenarios

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show Chicago 2026 prices under three scenarios: 2% inflation, 3% inflation, and 4% inflation. Present results comparing all three.",
    "filename": "sales-data.csv"
  }'
```

**Expected Output:**
```
Scenario              2026 Price    Total Increase
Low (2%)              $137.17       14.4%
Moderate (3%)         $147.40       23.0%
High (4%)             $157.96       31.8%
```

#### Custom Target Year

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Project Miami ticket prices to 2030 using 3.2% annual inflation",
    "filename": "sales-data.csv"
  }'
```

---

### Method 2: Using Live Inflation Data (Accurate)

For production analysis requiring real historical and current data.

#### Attempt to Fetch Real CPI Data

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Try to fetch actual US Consumer Price Index (CPI) data from a free public API for 2019-2025. If successful, use the real cumulative inflation to calculate Chicago 2026 prices. If the API fails, fall back to 3% assumption and note this in your response.",
    "filename": "sales-data.csv"
  }'
```

**Note**: This may fail depending on API availability. The LLM will attempt different sources.

#### Using Specific Known APIs

**Federal Reserve (FRED) - Requires API Key:**
```bash
# Set API key as environment variable in worker deployment
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch CPI data from FRED API using the FRED_API_KEY environment variable. Calculate real inflation from 2019-2025 and project Chicago 2026 prices.",
    "filename": "sales-data.csv"
  }'
```

**World Bank API (Free, No Key):**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch inflation data from World Bank API (https://api.worldbank.org/v2/country/USA/indicator/FP.CPI.TOTL.ZG?format=json) for recent years, then use it to calculate inflation-adjusted Chicago prices for 2026",
    "filename": "sales-data.csv"
  }'
```

---

## Live Data Integration

### Simple API Test

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Make a GET request to https://api.github.com and show the response status code and any rate limit information"
  }'
```

**Expected Output:**
```json
{
  "status": "SUCCESS",
  "result": "GET request to https://api.github.com returned status code 200 (OK). No rate limit information available in headers."
}
```

### Fetch Stock Price

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch current Bitcoin price from a free crypto API and calculate how many BTC the total revenue in the CSV could buy",
    "filename": "sales-data.csv"
  }'
```

### Weather Correlation

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "For the top 3 cities by attendance, try to fetch current weather data and show it alongside historical attendance figures",
    "filename": "sales-data.csv"
  }'
```

---

## Advanced Analytics

### Correlation Analysis

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate the correlation coefficient between Attendance and Revenue. Is there a strong relationship?",
    "filename": "sales-data.csv"
  }'
```

### Price Elasticity

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Analyze the relationship between Avg_Price and Attendance. Does higher pricing lead to lower attendance?",
    "filename": "sales-data.csv"
  }'
```

### Seasonal Trends

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Extract month from the Date column and show revenue trends by month. Which months are most profitable?",
    "filename": "sales-data.csv"
  }'
```

### Outlier Detection

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Identify outlier events where Revenue is more than 2 standard deviations from the mean. List them with details.",
    "filename": "sales-data.csv"
  }'
```

### Revenue Per Attendee Analysis

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate revenue per attendee for each city and rank cities by this metric",
    "filename": "sales-data.csv"
  }'
```

---

## Python Client Examples

### Synchronous Client

```python
import requests
import time

class DataAnalysisClient:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
    
    def analyze(self, question, filename=None, timeout=60):
        """Submit analysis and wait for result."""
        # Submit task
        payload = {"question": question}
        if filename:
            payload["filename"] = filename
        
        response = requests.post(
            f"{self.base_url}/analyze",
            json=payload
        )
        task_id = response.json()["task_id"]
        
        # Poll for result
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_response = requests.get(
                f"{self.base_url}/status/{task_id}"
            )
            status_data = status_response.json()
            
            if status_data["status"] == "SUCCESS":
                return status_data["result"]
            elif status_data["status"] == "FAILURE":
                raise Exception(f"Task failed: {status_data.get('error')}")
            
            time.sleep(2)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

# Usage
client = DataAnalysisClient()

# Simple query
result = client.analyze(
    "What is the median Avg_Price?",
    filename="sales-data.csv"
)
print(result)

# Inflation projection
result = client.analyze(
    "Calculate Chicago 2026 prices with 3% inflation",
    filename="sales-data.csv"
)
print(result)
```

### Asynchronous Client

```python
import asyncio
import httpx

class AsyncDataAnalysisClient:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
    
    async def analyze(self, question, filename=None, timeout=60):
        """Submit analysis and wait for result asynchronously."""
        async with httpx.AsyncClient() as client:
            # Submit task
            payload = {"question": question}
            if filename:
                payload["filename"] = filename
            
            response = await client.post(
                f"{self.base_url}/analyze",
                json=payload
            )
            task_id = response.json()["task_id"]
            
            # Poll for result
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                status_response = await client.get(
                    f"{self.base_url}/status/{task_id}"
                )
                status_data = status_response.json()
                
                if status_data["status"] == "SUCCESS":
                    return status_data["result"]
                elif status_data["status"] == "FAILURE":
                    raise Exception(f"Task failed: {status_data.get('error')}")
                
                await asyncio.sleep(2)
            
            raise TimeoutError(f"Task {task_id} did not complete")

# Usage
async def main():
    client = AsyncDataAnalysisClient()
    
    # Run multiple queries in parallel
    results = await asyncio.gather(
        client.analyze("What is the median price?", "sales-data.csv"),
        client.analyze("What is the total revenue?", "sales-data.csv"),
        client.analyze("Which city had highest attendance?", "sales-data.csv")
    )
    
    for result in results:
        print(result)

asyncio.run(main())
```

---

## Best Practices

### Query Writing Tips

1. **Be Specific**: "Calculate the median of the Avg_Price column" is better than "find the median"
2. **Show Your Work**: Ask for "show calculation steps" to understand the process
3. **Error Handling**: For live data, include fallback: "Try API X, if it fails use 3% assumption"
4. **Structured Output**: Request "show results in a table" or "format as JSON"

### When to Use What

| Scenario | Approach | Why |
|----------|----------|-----|
| Quick estimate | Assumed rates | Fast, predictable |
| Presentation/demo | Assumed rates | Reliable, no API dependencies |
| Compliance/audit | Live data | Accurate, defensible |
| Production reporting | Live data with fallback | Best of both worlds |
| Testing/development | Assumed rates | No external dependencies |

### Performance Expectations

| Query Type | Typical Time | Factors |
|------------|--------------|---------|
| Basic statistics | 10-20s | File size, complexity |
| Multi-file analysis | 20-40s | Number of files, joins |
| Inflation (assumed) | 15-30s | Calculation complexity |
| Live data fetch | 30-60s | API latency, parsing |
| Complex correlation | 20-40s | Data size, calculations |

---

## Troubleshooting

### Query Returns Error

**Problem**: Task completes with error message

**Solutions**:
1. Check column names match exactly (case-sensitive)
2. Verify file exists: `make data-list`
3. Simplify query to isolate issue
4. Check worker logs: `make logs-worker`

### Live Data Fetch Fails

**Problem**: API request returns error or empty data

**Solutions**:
1. Test API manually: `curl <api-url>`
2. Check if API requires authentication
3. Add fallback to assumed values
4. Use alternative data source

### Task Takes Too Long

**Problem**: Query times out or hangs

**Solutions**:
1. Check file size (large files take longer)
2. Simplify the question
3. Increase timeout in client code
4. Check worker CPU/memory usage

---

## See Also

- [Main README](README.md) - Getting started
- [Multi-File Analysis](MULTI-FILE-ANALYSIS.md) - Advanced multi-file techniques
- [Network Access](NETWORK-ACCESS.md) - Live data fetching details
- [Data Management API](DATA-API.md) - Upload/manage files

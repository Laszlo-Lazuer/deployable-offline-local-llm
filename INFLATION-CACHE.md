# Inflation Data Cache

## Overview

The Local LLM Celery project includes a built-in inflation data cache that scrapes and caches historical US inflation rates from [usinflationcalculator.com](https://www.usinflationcalculator.com/inflation/historical-inflation-rates/). This eliminates the need to fetch inflation data repeatedly and provides access to over 100 years of historical data (1914-present).

## Features

- **Automatic Caching**: Data is scraped once and cached locally
- **Smart Refresh**: Cache refreshes only when needed (monthly or new year)
- **Historical Data**: Access to inflation rates from 1914 to present
- **Monthly Granularity**: Average monthly inflation rates for each year
- **Easy Integration**: Simple Python API for use in analysis tasks
- **Fallback Support**: Uses cached data if live scraping fails

## How It Works

### Data Source

The system scrapes inflation data from the US Inflation Calculator website, which maintains a comprehensive table of monthly inflation rates. The data includes:

- **Years**: 1914 to present (112+ years of data)
- **Monthly Rates**: Inflation percentage for each month
- **Annual Averages**: Calculated from monthly data

### Caching Strategy

```python
# Cache location
/app/cache/inflation_data.json

# Cache refresh triggers:
- Cache is more than 30 days old
- It's a new year and cache is from previous year
- Force refresh requested
```

### Cache File Structure

```json
{
  "last_updated": "2025-10-19T23:52:58",
  "data": {
    "2019": {
      "Jan": 1.6,
      "Feb": 1.5,
      "Mar": 1.9,
      ...
    },
    "2020": {
      "Jan": 2.5,
      ...
    }
  }
}
```

## Usage

### Available Functions

The `inflation_cache` module provides several functions:

#### 1. Get Inflation Data

```python
from inflation_cache import get_inflation_data

# Get all historical data (uses cache if available)
data = get_inflation_data()

# Force refresh from website
data = get_inflation_data(force_refresh=True)

# Returns:
# {
#   "2019": {"Jan": 1.6, "Feb": 1.5, ...},
#   "2020": {"Jan": 2.5, "Feb": 2.3, ...}
# }
```

#### 2. Calculate Cumulative Inflation

```python
from inflation_cache import calculate_cumulative_inflation

# Calculate cumulative inflation between two years
cumulative_rate = calculate_cumulative_inflation(2019, 2026)

# Returns decimal (e.g., 0.2827 for 28.27%)

# Apply to a price
original_price = 119.85
future_price = original_price * (1 + cumulative_rate)
# Result: $153.74
```

#### 3. Get Inflation Summary

```python
from inflation_cache import get_inflation_summary

# Get formatted summary with yearly breakdown
summary = get_inflation_summary(2019, 2026)

# Prints:
# Inflation from 2019 to 2026:
# Cumulative rate: 28.27%
# Source: usinflationcalculator.com (cached)
#
# Yearly breakdown:
#   2019: 1.82%
#   2020: 1.23%
#   2021: 4.70%
#   2022: 8.02%
#   2023: 4.13%
#   2024: 2.95%
#   2025: 2.65%
```

## Example Queries

### Basic Price Prediction

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me real inflation data: Use get_inflation_summary(2019, 2026) to display historical US inflation rates with yearly breakdown. Then calculate what $119.85 from 2019 would be worth in 2026.",
    "filename": "sales-data.csv"
  }'
```

**Result:**
```
Cumulative inflation rate: 28.27%
$119.85 in 2019 → $153.74 in 2026

Yearly breakdown:
  2019: 1.82%
  2020: 1.23%
  2021: 4.70%
  2022: 8.02%
  2023: 4.13%
  2024: 2.95%
  2025: 2.65%
```

### Concert Price Prediction

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate 2026 Chicago concert prices using real inflation: 1) Get average Avg_Price for City=Chicago from sales-data.csv, 2) Use calculate_cumulative_inflation(2019, 2026) for real inflation rate, 3) Calculate predicted 2026 price and show all steps.",
    "filename": "sales-data.csv"
  }'
```

**Result:**
```
Average Chicago Price (2019): $119.85
Cumulative Inflation (2019-2026): 28.27%
Predicted 2026 Price: $153.74
```

### Historical Comparison

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare inflation rates: Show cumulative inflation from 1980-1990 vs 2010-2020 vs 2019-2026 using calculate_cumulative_inflation(). Which decade had highest inflation?",
    "filename": "sales-data.csv"
  }'
```

## Real-World Results

### Test Case: Chicago Concert Pricing

**Scenario**: Predict 2026 concert ticket prices for Chicago based on 2019 data

**2019 Baseline**: $119.85 (average from historical data)

**Real Inflation Data (2019-2026)**:
- 2019: 1.82%
- 2020: 1.23%
- 2021: 4.70%
- 2022: 8.02%
- 2023: 4.13%
- 2024: 2.95%
- 2025: 2.65%

**Cumulative Rate**: 28.27%

**2026 Predicted Price**: $153.74

**Comparison**:
- Assumed 3% annual: $147.40 (underestimated by $6.34)
- Real historical data: $153.74 (28.27% vs 21% assumed)

The real data shows higher inflation due to the 2021-2022 spike (COVID-19 pandemic effects).

## Python Client Example

```python
import requests

def predict_price_with_inflation(base_price, start_year, end_year):
    """
    Predict future price using real inflation data
    """
    question = f"""
    Using the inflation_cache module:
    1. Get inflation summary: get_inflation_summary({start_year}, {end_year})
    2. Calculate cumulative inflation: calculate_cumulative_inflation({start_year}, {end_year})
    3. Calculate ${base_price} in {start_year} adjusted to {end_year}
    4. Show yearly breakdown and final price
    """
    
    response = requests.post(
        "http://localhost:5001/analyze",
        json={"question": question, "filename": "sales-data.csv"}
    )
    
    task_id = response.json()["task_id"]
    
    # Poll for result
    import time
    while True:
        status_response = requests.get(f"http://localhost:5001/status/{task_id}")
        status_data = status_response.json()
        
        if status_data["status"] == "SUCCESS":
            return status_data["result"]
        elif status_data["status"] == "FAILURE":
            return f"Error: {status_data.get('result', 'Unknown error')}"
        
        time.sleep(2)

# Example usage
result = predict_price_with_inflation(119.85, 2019, 2026)
print(result)
```

## Cache Management

### View Cache Status

```bash
# Check if cache exists
podman exec llm-worker ls -lh /app/cache/

# View cache contents
podman exec llm-worker cat /app/cache/inflation_data.json | head -50
```

### Force Cache Refresh

```bash
# Run the module directly to refresh cache
podman exec llm-worker python inflation_cache.py
```

### Clear Cache

```bash
# Remove cache file (will be regenerated on next use)
podman exec llm-worker rm /app/cache/inflation_data.json
```

## Technical Details

### Dependencies

The inflation cache requires:
- `requests`: HTTP library for fetching data
- `beautifulsoup4`: HTML parsing
- `lxml`: XML/HTML parser

These are already included in `requirements.txt`.

### Scraping Logic

```python
def scrape_inflation_data():
    # Fetch page
    response = requests.get(INFLATION_URL, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find inflation table
    table = soup.find('table')
    
    # Parse header row (months)
    # Parse data rows (years and rates)
    # Return structured dictionary
```

### Fallback Behavior

If scraping fails:
1. Returns cached data if available
2. If no cache, returns `None`
3. `calculate_cumulative_inflation()` falls back to assumed 3% annual rate

### Performance

- **Initial scrape**: ~2-3 seconds
- **Cache hit**: <10ms
- **Cache file size**: ~29KB (112 years of data)
- **Refresh frequency**: Monthly or on new year

## Kubernetes Deployment

When deploying to Kubernetes, ensure the cache directory persists:

```yaml
# Add volume for cache persistence
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: inflation-cache-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi

---
# Mount in worker deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  template:
    spec:
      containers:
      - name: worker
        volumeMounts:
        - name: cache
          mountPath: /app/cache
      volumes:
      - name: cache
        persistentVolumeClaim:
          claimName: inflation-cache-pvc
```

## Best Practices

### 1. Use Real Data When Accuracy Matters

```python
# Good: Real historical data
from inflation_cache import calculate_cumulative_inflation
rate = calculate_cumulative_inflation(2019, 2026)  # 28.27%

# Acceptable: Assumptions for future projections
# (since we don't have future data yet)
assumed_future_rate = 0.03  # 3% per year
```

### 2. Show Data Source in Results

Always indicate whether you're using real historical data or assumptions:

```python
summary = get_inflation_summary(2019, 2026)
print(summary)  # Includes "Source: usinflationcalculator.com (cached)"
```

### 3. Handle Missing Years Gracefully

The cache handles missing years automatically:
```python
# If 2026 data doesn't exist yet, uses 3% for that year
rate = calculate_cumulative_inflation(2019, 2027)
```

### 4. Refresh Periodically

For production systems, consider refreshing monthly:
```python
# In a scheduled task
from inflation_cache import get_inflation_data
data = get_inflation_data(force_refresh=True)
```

## Troubleshooting

### Cache Not Creating

**Problem**: Cache file not appearing

**Solutions**:
```bash
# Check directory permissions
podman exec llm-worker ls -ld /app/cache

# Manually create if needed
podman exec llm-worker mkdir -p /app/cache

# Test scraping
podman exec llm-worker python inflation_cache.py
```

### Scraping Fails

**Problem**: Website structure changed

**Solutions**:
1. Check if website is accessible
2. Update scraping logic in `inflation_cache.py`
3. Use cached data in the meantime

### Incorrect Results

**Problem**: Inflation calculations seem wrong

**Debug**:
```python
# Check what data was used
from inflation_cache import get_inflation_data
data = get_inflation_data()
print(data["2022"])  # Verify specific year

# Test calculation
from inflation_cache import calculate_cumulative_inflation
rate = calculate_cumulative_inflation(2019, 2026)
print(f"Cumulative: {rate * 100:.2f}%")
```

## Future Enhancements

Potential improvements:
- Support for other countries' inflation data
- Multiple inflation metrics (CPI, PPI, etc.)
- Historical currency exchange rates
- Inflation forecasting/projections
- API for direct cache access
- Cache versioning and migration

## Additional Resources

- [US Inflation Calculator](https://www.usinflationcalculator.com/)
- [Bureau of Labor Statistics](https://www.bls.gov/cpi/)
- [Federal Reserve Economic Data](https://fred.stlouisfed.org/)

## Related Documentation

- [NETWORK-ACCESS.md](NETWORK-ACCESS.md) - How network access is enabled
- [EXAMPLES.md](EXAMPLES.md) - More example queries
- [README.md](README.md) - Main project documentation

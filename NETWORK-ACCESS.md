# Network Access & Live Data Fetching

## Overview

The system is now configured to allow the LLM to fetch live data from the internet, enabling real-time analysis with external data sources like APIs, web scraping, and live databases.

## What's Enabled

### Network Capabilities

With `interpreter.safe_mode = "off"`, the LLM-generated Python code can now:

✅ **Make HTTP/HTTPS requests** to any URL
✅ **Fetch data from REST APIs** (inflation rates, stock prices, weather, etc.)
✅ **Web scraping** with BeautifulSoup and lxml
✅ **Access public databases** and data sources
✅ **Download files** from the internet
✅ **Call external services** and webhooks

### Available Packages

The following packages are pre-installed for network operations:

- `requests` - HTTP library for API calls
- `beautifulsoup4` - HTML/XML parsing for web scraping
- `lxml` - Fast XML/HTML parser
- `urllib3` - Low-level HTTP client
- `httpx` - Modern async HTTP client (via dependencies)

## Security Considerations

### ⚠️ Important Security Notes

**Enabling network access means:**

1. **LLM can make external requests** - The AI-generated code can contact any URL
2. **Data exfiltration risk** - Potentially sensitive data could be sent externally
3. **No request filtering** - All outbound traffic is allowed
4. **Trust-based system** - Relies on LLM behavior, not technical controls

### Recommended Security Measures

#### For Production Deployments:

1. **Network Policies** - Use Kubernetes NetworkPolicies to restrict outbound traffic
2. **Egress Filtering** - Allow only specific domains/IPs
3. **Request Logging** - Monitor all external requests
4. **Rate Limiting** - Limit API calls to prevent abuse
5. **Input Validation** - Sanitize user questions for malicious prompts
6. **Audit Logging** - Track all LLM-generated code execution

#### Kubernetes NetworkPolicy Example:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: celery-worker-egress
  namespace: llm-analysis
spec:
  podSelector:
    matchLabels:
      app: celery-worker
  policyTypes:
  - Egress
  egress:
  # Allow DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
  # Allow specific external APIs
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS
  # Allow access to specific domains (requires DNS-based policies or service mesh)
  - to:
    ports:
    - protocol: TCP
      port: 443
    # Add IP ranges for allowed services
```

## Use Cases

### 1. Real-Time Financial Data

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch current stock prices for AAPL, GOOGL, and MSFT from a free stock API, then calculate their average price change today",
    "filename": "portfolio.csv"
  }'
```

### 2. Live Inflation Rates

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Get actual US inflation data from BLS or Federal Reserve, then adjust historical prices in the CSV to current dollar values",
    "filename": "sales-data.csv"
  }'
```

### 3. Weather Data Integration

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "For each city in the CSV, fetch current weather data and correlate it with historical attendance figures",
    "filename": "events.csv"
  }'
```

### 4. Exchange Rate Conversion

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch current USD to EUR exchange rates and convert all revenue values in the CSV to Euros",
    "filename": "international-sales.csv"
  }'
```

### 5. Web Scraping for Enrichment

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "For each venue in the CSV, scrape their website for current ticket prices and compare with historical data",
    "filename": "venues.csv"
  }'
```

## How It Works

### Configuration in `worker.py`

```python
# Set safe_mode to 'off' to allow network requests
interpreter.safe_mode = "off"
```

This single line enables the LLM to execute code that makes network requests.

### Example LLM-Generated Code

When you ask about live inflation data, the LLM might generate code like:

```python
import requests
import pandas as pd

# Fetch inflation data from FRED API (Federal Reserve Economic Data)
url = "https://api.stlouisfed.org/fred/series/observations"
params = {
    "series_id": "CPIAUCSL",  # Consumer Price Index
    "api_key": "your_api_key",  # Would need actual key
    "file_type": "json"
}

response = requests.get(url, params=params)
inflation_data = response.json()

# Load local CSV data
df = pd.read_csv('/app/data/sales-data.csv')

# Calculate inflation-adjusted prices
# ... analysis code ...
```

## Public Data Sources

### Free APIs (No Authentication)

1. **Inflation Data**
   - [FRED API](https://fred.stlouisfed.org/docs/api/fred/) - Federal Reserve Economic Data
   - [BLS API](https://www.bls.gov/developers/) - Bureau of Labor Statistics
   
2. **Financial Data**
   - [Alpha Vantage](https://www.alphavantage.co/) - Stock prices (free tier)
   - [Yahoo Finance](https://finance.yahoo.com/) - Historical data via libraries
   
3. **Weather Data**
   - [OpenWeatherMap](https://openweathermap.org/api) - Current/forecast weather
   - [NOAA](https://www.ncdc.noaa.gov/cdo-web/webservices/v2) - Historical weather

4. **Exchange Rates**
   - [ExchangeRate-API](https://www.exchangerate-api.com/) - Currency conversion
   - [Open Exchange Rates](https://openexchangerates.org/) - Live rates

5. **Geographic Data**
   - [OpenStreetMap](https://www.openstreetmap.org/) - Location data
   - [GeoNames](http://www.geonames.org/) - Geographic database

### Authentication-Required APIs

For APIs requiring keys, you can:

1. **Pass in questions**: Include API keys in the question (not recommended for production)
2. **Environment variables**: Add API keys to worker container environment
3. **Secrets management**: Use Kubernetes secrets for production

**Example with environment variable:**

```yaml
# k8s/celery-worker.yaml
env:
- name: FRED_API_KEY
  valueFrom:
    secretKeyRef:
      name: api-keys
      key: fred-api-key
```

Then the LLM can access it:

```python
import os
api_key = os.environ.get('FRED_API_KEY')
```

## Testing Network Access

### 1. Simple HTTP Request Test

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Make a GET request to https://api.github.com/repos/python/cpython and show the number of stars the Python repository has"
  }'
```

### 2. Web Scraping Test

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Scrape the latest news headlines from https://news.ycombinator.com/ and list the top 5"
  }'
```

### 3. API Integration Test

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch current Bitcoin price from a free crypto API and calculate how many BTC the total revenue in sales-data.csv could buy",
    "filename": "sales-data.csv"
  }'
```

## Disabling Network Access

If you want to revert to sandboxed (offline) mode:

### 1. Edit `worker.py`

```python
# Comment out or remove this line:
# interpreter.safe_mode = "off"
```

### 2. Rebuild and restart:

```bash
make rebuild
```

### 3. Verify offline mode:

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Try to fetch data from https://google.com - it should fail"
  }'
```

## Performance Implications

### Network Latency

- **Local data**: ~10-30 seconds processing
- **With API calls**: +2-10 seconds per external request
- **With web scraping**: +5-30 seconds depending on site

### Resource Usage

- **Bandwidth**: Minimal for API calls, higher for scraping
- **Memory**: May increase if downloading large datasets
- **CPU**: Parsing HTML/JSON adds overhead

### Recommendations

1. **Cache results** when possible (future enhancement)
2. **Limit concurrent requests** in LLM code
3. **Set timeouts** to prevent hanging requests
4. **Monitor bandwidth** usage in production

## Monitoring & Logging

### Log External Requests

Add logging to worker to track network activity:

```python
import logging
import requests

# Patch requests to log all calls
original_get = requests.get

def logged_get(url, *args, **kwargs):
    logger = logging.getLogger(__name__)
    logger.info(f"External GET request to: {url}")
    return original_get(url, *args, **kwargs)

requests.get = logged_get
```

### Kubernetes Monitoring

Use service mesh (Istio, Linkerd) or network monitoring tools:

```bash
# View worker pod network traffic
kubectl logs -n llm-analysis -l app=celery-worker --tail=100 | grep "External"
```

## Troubleshooting

### Issue: Requests Timeout

**Problem**: External API calls hang or timeout

**Solutions**:
1. Add timeout parameters to requests: `requests.get(url, timeout=10)`
2. Increase worker task timeout in Celery configuration
3. Check firewall/egress rules in Kubernetes

### Issue: SSL Certificate Errors

**Problem**: `SSLError` when accessing HTTPS sites

**Solution**:
```python
import requests
# Disable SSL verification (not recommended for production)
response = requests.get(url, verify=False)
```

Or install certificates in container:
```dockerfile
RUN apt-get update && apt-get install -y ca-certificates
```

### Issue: Rate Limiting

**Problem**: API returns 429 (Too Many Requests)

**Solutions**:
1. Implement retry logic with exponential backoff
2. Cache API responses
3. Use API keys for higher rate limits
4. Distribute requests across time

## Future Enhancements

Potential improvements for network-enabled features:

1. **Response Caching** - Cache API responses to reduce external calls
2. **Request Queue** - Throttle and queue external requests
3. **Whitelist/Blacklist** - Allow only specific domains
4. **Cost Tracking** - Monitor API usage and costs
5. **Fallback Data** - Use cached/default data if external sources fail
6. **Proxy Support** - Route requests through corporate proxies
7. **VPN Integration** - Secure external access via VPN

## See Also

- [Main README](README.md) - Project overview
- [Multi-File Analysis](MULTI-FILE-ANALYSIS.md) - Working with multiple datasets
- [Data Management API](DATA-API.md) - Upload/manage data files
- [Worker Configuration](worker.py) - Source code for task execution

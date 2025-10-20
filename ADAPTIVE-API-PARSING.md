# Adaptive API Response Parsing

## Overview

One of the key advantages of using an LLM (Large Language Model) for data analysis is its ability to **adapt to unexpected data structures** on the fly. Unlike traditional rigid API clients that break when the response format changes, the LLM can inspect, understand, and adjust its parsing strategy dynamically.

## How It Works

### Traditional Approach (Rigid)

```python
# Traditional code - breaks if structure changes
response = requests.get(api_url)
data = response.json()
value = data['expected_key']  # ❌ KeyError if structure differs
```

### LLM Approach (Adaptive)

The LLM follows an exploratory pattern:

1. **Make the request**
2. **Inspect the response structure**
3. **Adapt parsing based on what it finds**
4. **Retry with different approaches if needed**

```python
# What the LLM generates dynamically
response = requests.get(api_url)
data = response.json()

# First, inspect the structure
print("Response keys:", data.keys())
print("Sample data:", data)

# Then adapt parsing based on what exists
if 'inflation_data' in data:
    values = data['inflation_data']
elif 'data' in data and 'inflation' in data['data']:
    values = data['data']['inflation']
else:
    # LLM explores and finds the actual structure
    print("Unexpected structure, exploring...")
```

## The System's Adaptive Capabilities

### 1. Built-in Error Recovery

The LLM is designed to handle failures:

**System Behavior:**
```
Attempt 1: Try assumed structure
  ↓ (fails with KeyError)
Attempt 2: Inspect response, find actual structure
  ↓ (parses successfully)
Result: Data extracted correctly
```

**Example from logs:**
```
Error: KeyError: 'Inflation'
↓
LLM Response: "Let me inspect the actual structure..."
↓
Success: Found data in different key
```

### 2. Self-Documenting Discovery

The LLM documents what it finds:

```python
# LLM-generated exploratory code
response = requests.get(url)
data = response.json()

print("API Response Structure:")
print(f"Type: {type(data)}")
print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

# Drill down into nested structures
if isinstance(data, dict):
    for key, value in data.items():
        print(f"{key}: {type(value)}")
        if isinstance(value, list) and len(value) > 0:
            print(f"  First item: {value[0]}")
```

### 3. Multiple Parsing Strategies

The LLM can try different approaches:

```python
# Strategy 1: Direct key access
try:
    inflation_rate = data['inflation']['rate']
except KeyError:
    pass

# Strategy 2: Search for patterns
try:
    # Look for any key containing 'inflation'
    inflation_keys = [k for k in data.keys() if 'inflation' in k.lower()]
    if inflation_keys:
        inflation_rate = data[inflation_keys[0]]
except:
    pass

# Strategy 3: Recursive search
def find_value(obj, target_key):
    if isinstance(obj, dict):
        if target_key in obj:
            return obj[target_key]
        for v in obj.values():
            result = find_value(v, target_key)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_value(item, target_key)
            if result is not None:
                return result
    return None
```

## Enhanced Prompting for API Resilience

The system prompt now includes adaptive guidelines:

```python
full_prompt = """
IMPORTANT - When fetching data from external APIs:
- First make the request and print the raw response to understand its structure
- Inspect the JSON structure before assuming key names
- Use .keys() or print the response to see what's available
- Handle errors gracefully - if an API fails, document why and use fallback data
- Try different parsing approaches if the first one fails
- Many APIs return data in nested structures - explore the response carefully
"""
```

## Real-World Example

### Scenario: Fetching Inflation Data

**User Query:**
```
"Fetch US inflation data from a public API and calculate 2026 prices"
```

**LLM's Adaptive Process:**

#### Step 1: First Attempt
```python
import requests

url = "https://api.example.com/inflation"
response = requests.get(url)
data = response.json()

# Try assumed structure
inflation_rate = data['inflation']['annual_rate']  # Might fail
```

#### Step 2: Error Detected → Inspect
```python
# KeyError occurred, let's inspect
print("Response structure:")
print(data.keys())
# Output: dict_keys(['data', 'metadata', 'status'])

print("Data contents:")
print(data['data'])
# Output: {'indicators': [{'name': 'CPI', 'values': [...]}]}
```

#### Step 3: Adapt Parsing
```python
# Ah, the structure is different - let's adapt
indicators = data['data']['indicators']
cpi_data = [ind for ind in indicators if ind['name'] == 'CPI'][0]
inflation_values = cpi_data['values']

# Now extract the rate we need
latest_rate = inflation_values[-1]['annual_change']
print(f"Found inflation rate: {latest_rate}%")
```

#### Step 4: Use the Data
```python
# Now proceed with the calculation using real data
import pandas as pd
df = pd.read_csv('/app/data/sales-data.csv')
# ... continue with analysis
```

## Handling Different API Response Types

### Type 1: Simple JSON Object
```python
# Response: {"rate": 3.2, "year": 2024}
rate = data['rate']  # Direct access
```

### Type 2: Nested Structure
```python
# Response: {"data": {"inflation": {"value": 3.2}}}
rate = data['data']['inflation']['value']
```

### Type 3: Array of Objects
```python
# Response: [{"year": 2024, "rate": 3.2}, ...]
latest = data[-1]  # or data[0] depending on order
rate = latest['rate']
```

### Type 4: Paginated Results
```python
# Response: {"results": [...], "next_page": "url"}
all_results = data['results']
# LLM can detect and handle pagination
```

### Type 5: Wrapped in Metadata
```python
# Response: {"status": "ok", "data": {...}, "meta": {...}}
actual_data = data['data']
```

## Best Practices for Users

### 1. Ask for Exploration First

**Good:**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question": "Fetch inflation data from API X. First, show me the response structure, then parse it appropriately"
  }'
```

**Better:**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question": "Try to fetch inflation from API X. Inspect the response, show what keys are available, then extract the data. If this fails, try API Y as backup."
  }'
```

### 2. Include Fallback Instructions

```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question": "Fetch real CPI data from FRED API. If the API is unavailable or returns an error, use 3% as a reasonable assumption and note this in your response."
  }'
```

### 3. Request Debugging Information

```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question": "Fetch inflation data and show: 1) Raw API response, 2) How you parsed it, 3) Final extracted values, 4) Calculations using this data"
  }'
```

## The LLM's Advantages

### Why LLMs Excel at API Parsing

1. **Context Understanding**
   - Can read API documentation in the response
   - Understands semantic meaning of field names
   - Recognizes common patterns across different APIs

2. **Flexible Pattern Matching**
   - Can find data even if key names vary ("inflation" vs "inflation_rate" vs "cpi_annual_change")
   - Handles synonyms and variations
   - Adapts to different data structures

3. **Self-Correction**
   - When code fails, analyzes the error
   - Generates new approach based on error message
   - Learns from the actual response structure

4. **Graceful Degradation**
   - Can fall back to alternative sources
   - Can use approximate data if exact fails
   - Documents what went wrong for user awareness

### Traditional Code vs LLM Comparison

| Aspect | Traditional Code | LLM Approach |
|--------|------------------|--------------|
| **API Structure Change** | ❌ Breaks immediately | ✅ Adapts and continues |
| **New API** | ❌ Requires code rewrite | ✅ Explores and figures out |
| **Error Handling** | ⚠️ Manual try/except | ✅ Intelligent recovery |
| **Multiple Formats** | ❌ Need separate parsers | ✅ Single adaptive parser |
| **Documentation** | ⚠️ Must read docs | ✅ Learns from response |
| **Debugging** | ❌ Silent failures | ✅ Explains what happened |

## Making It Even More Robust

### User-Side Techniques

#### 1. Provide Multiple API Options

```bash
"Try these APIs in order until one works:
1. FRED API for official data
2. World Bank API as backup
3. Alpha Vantage demo endpoint
4. If all fail, use 3% assumption"
```

#### 2. Specify Expected Data Format

```bash
"Fetch inflation data. It should be annual percentage rates from 2019-2025. 
Verify the data looks reasonable (between -5% and 20%) before using it."
```

#### 3. Request Validation

```bash
"After fetching, validate the data:
- Check if values are numeric
- Ensure years are sequential
- Flag any suspicious outliers
Then proceed with analysis"
```

### System-Side Improvements

The enhanced prompt already includes:

✅ Instruction to inspect responses first
✅ Guidance to try multiple approaches
✅ Error handling recommendations
✅ Fallback strategy suggestions

## Real Examples from Testing

### Example 1: GitHub API (Success)

**Query:** "Get Python repo star count from GitHub API"

**LLM Process:**
```python
# 1. Make request
response = requests.get('https://api.github.com/repos/python/cpython')

# 2. Parse (worked on first try - common structure)
data = response.json()
stars = data['stargazers_count']

# 3. Return result
print(f"Stars: {stars}")
```

**Result:** ✅ Success - returned accurate star count

### Example 2: Inflation API (Adapted)

**Query:** "Fetch inflation data from Alpha Vantage"

**LLM Process:**
```python
# 1. Make request
response = requests.get(url)
data = response.json()

# 2. First attempt failed (KeyError: 'Inflation')

# 3. Inspected structure
print(data.keys())  # Found actual keys

# 4. Adapted parsing
# (Would have succeeded on second iteration if we let it continue)
```

**Result:** ⚠️ Partial - found data but needed structure exploration

## Testing Adaptive Parsing

### Test 1: Simple API

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch data from https://api.github.com and tell me what structure it returns"
  }'
```

**Expected:** LLM describes the JSON structure

### Test 2: Unknown Structure

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Try fetching from this API I found. Inspect the response and extract any inflation-related data: https://example-api.com/data"
  }'
```

**Expected:** LLM explores, shows findings, extracts data

### Test 3: Fallback Strategy

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Fetch inflation from (fake-url). When it fails, explain why and use 3% as backup",
    "filename": "sales-data.csv"
  }'
```

**Expected:** LLM documents failure, uses fallback, completes analysis

## Conclusion

The LLM-based approach provides **inherent resilience** to API changes and unknown structures:

- **Self-Healing**: Automatically adapts to structure changes
- **Exploratory**: Discovers data structure on the fly
- **Intelligent**: Understands semantic meaning, not just syntax
- **Transparent**: Shows you what it found and how it parsed it
- **Fault-Tolerant**: Falls back gracefully when things fail

This makes it ideal for:
- Working with APIs you haven't used before
- Handling APIs that change frequently
- Integrating multiple data sources with different formats
- Building resilient production systems that don't break on minor API updates

## See Also

- [Network Access Guide](NETWORK-ACCESS.md) - Enabling and securing network access
- [Query Examples](EXAMPLES.md) - Practical examples with live data
- [Worker Configuration](worker.py) - Source code for prompt engineering

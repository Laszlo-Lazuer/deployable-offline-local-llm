# Multi-Format File Support - Test Plan

## Prerequisites

1. Build the updated container:
```bash
podman build -t local-llm-celery:dev --format docker .
```

2. Start services:
```bash
podman-compose down
podman-compose up -d
```

3. Wait for services to be ready (~30 seconds):
```bash
sleep 30 && curl -s http://localhost:5001/status/health
# Should return: {"status": "healthy"}
```

## Test Files

Create test files in different formats:

### 1. TSV File (Tab-Separated)
```bash
cd data
cat sales-data.csv | head -11 | sed 's/,/\t/g' > test-sales.tsv
```

### 2. JSON File (Array Format)
```bash
cat > data/test-sales.json << 'EOF'
[
  {"Date": "2019-01-15", "City": "New York", "Venue": "MSG", "Attendance": 20000, "Revenue": 2500000, "Avg_Price": 125},
  {"Date": "2019-01-22", "City": "Los Angeles", "Venue": "Staples", "Attendance": 18500, "Revenue": 2220000, "Avg_Price": 120},
  {"Date": "2019-02-05", "City": "Chicago", "Venue": "United Center", "Attendance": 19200, "Revenue": 2400000, "Avg_Price": 125}
]
EOF
```

### 3. Excel File (using Python)
```bash
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/sales-data.csv')
df.head(10).to_excel('data/test-sales.xlsx', index=False)
print("✅ Created test-sales.xlsx")
EOF
```

## Test Scenarios

### Test 1: CSV (Baseline - Verify Backward Compatibility)

**Goal:** Ensure existing CSV functionality still works

```bash
TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is the median Avg_Price?","filename":"sales-data.csv"}' \
  http://localhost:5001/analyze | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# Wait for completion
sleep 30

# Check result
curl -s http://localhost:5001/status/$TASK_ID | jq .
```

**Expected Result:**
- Status: "completed"
- Answer contains the median price (~$135)
- LLM should use `load_file('/app/data/sales-data.csv')`

---

### Test 2: TSV File (New Format)

**Goal:** Verify TSV files load automatically

```bash
TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is the average Avg_Price in the TSV file?","filename":"test-sales.tsv"}' \
  http://localhost:5001/analyze | jq -r '.task_id')

echo "Task ID: $TASK_ID"
sleep 30
curl -s http://localhost:5001/status/$TASK_ID | jq .
```

**Expected Result:**
- Status: "completed"
- LLM loads file with `load_file('/app/data/test-sales.tsv')`
- Automatically detects tab delimiter
- Returns average price

---

### Test 3: JSON File (New Format - Array)

**Goal:** Verify JSON array format loads correctly

```bash
TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"How many events are in the JSON file?","filename":"test-sales.json"}' \
  http://localhost:5001/analyze | jq -r '.task_id')

echo "Task ID: $TASK_ID"
sleep 30
curl -s http://localhost:5001/status/$TASK_ID | jq .
```

**Expected Result:**
- Status: "completed"
- LLM loads with `load_file('/app/data/test-sales.json')`
- Correctly parses JSON array into DataFrame
- Returns count of 3 events

---

### Test 4: Excel File (New Format)

**Goal:** Verify Excel files load automatically

```bash
TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is the total revenue in the Excel file?","filename":"test-sales.xlsx"}' \
  http://localhost:5001/analyze | jq -r '.task_id')

echo "Task ID: $TASK_ID"
sleep 30
curl -s http://localhost:5001/status/$TASK_ID | jq .
```

**Expected Result:**
- Status: "completed"
- LLM loads with `load_file('/app/data/test-sales.xlsx')`
- Loads first sheet automatically
- Returns total revenue

---

### Test 5: Mixed Format Analysis (New Feature)

**Goal:** Verify LLM can combine different file formats

```bash
# Ensure we have multiple formats uploaded
curl -s http://localhost:5001/data | jq -r '.files[].filename'

# Should see: sales-data.csv, test-sales.json, test-sales.tsv, test-sales.xlsx

TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is the total attendance across ALL data files?"}' \
  http://localhost:5001/analyze | jq -r '.task_id')

echo "Task ID: $TASK_ID"
sleep 45  # Longer wait for multi-file analysis
curl -s http://localhost:5001/status/$TASK_ID | jq .
```

**Expected Result:**
- Status: "completed"
- LLM loads multiple files using `load_file()` with different extensions
- Combines data from CSV, JSON, TSV, Excel
- Returns total attendance across all files

---

### Test 6: Natural Language + JSON (Combined Features)

**Goal:** Verify semantic understanding works with JSON files

```bash
TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"What was the average price at all the events?","filename":"test-sales.json"}' \
  http://localhost:5001/analyze | jq -r '.task_id')

echo "Task ID: $TASK_ID"
sleep 30
curl -s http://localhost:5001/status/$TASK_ID | jq .
```

**Expected Result:**
- Status: "completed"
- LLM loads JSON file
- Maps "average price" → "Avg_Price" column
- Returns correct average

---

### Test 7: Schema Normalization + Mixed Formats (Combined Features)

**Goal:** Verify normalization works across different file formats

```bash
# Upload files with different schemas
curl -X POST http://localhost:5001/data -F "file=@data/sales-data.csv"
curl -X POST http://localhost:5001/data -F "file=@data/q2-sales.csv"
curl -X POST http://localhost:5001/data -F "file=@data/test-sales.json"

TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"Combine all files and calculate total revenue. Note that files have different column names."}' \
  http://localhost:5001/analyze | jq -r '.task_id')

echo "Task ID: $TASK_ID"
sleep 60  # Longer wait for normalization
curl -s http://localhost:5001/status/$TASK_ID | jq .
```

**Expected Result:**
- Status: "completed"
- LLM inspects all schemas (CSV + JSON)
- Normalizes column names (Revenue, Total_Sales, etc.)
- Combines data correctly
- Returns total revenue

---

## Verification Checklist

After running all tests, verify:

- [ ] **CSV files** - Still work exactly as before (backward compatibility)
- [ ] **TSV files** - Load automatically without explicit pd.read_csv(sep='\t')
- [ ] **JSON files** - Parse automatically (array, nested, lines formats)
- [ ] **Excel files** - Load first sheet automatically
- [ ] **Mixed formats** - LLM can analyze multiple formats in one query
- [ ] **Natural language** - Works with all file formats
- [ ] **Schema normalization** - Works across different file formats
- [ ] **Error handling** - Clear messages for unsupported formats

## Success Criteria

✅ **All 7 tests pass**
✅ **No regression** - Existing CSV functionality unchanged
✅ **New features work** - All formats load automatically
✅ **Combined features** - Natural language + normalization work with all formats

## Expected Behavior Changes

### Before (CSV-only)
```python
# LLM would see:
Instructions:
2. Use pandas to load CSV files: pd.read_csv('/app/data/filename.csv')

# For Excel, user had to write:
"question": "Load using pd.read_excel('/app/data/file.xlsx') and analyze"
```

### After (Multi-format)
```python
# LLM sees:
Instructions:
2. Use the universal file loader to load ANY supported format:
   - Import: from file_loader import load_file
   - Usage: df = load_file('/app/data/filename.ext')
   - Supported: CSV (.csv), JSON (.json), Excel (.xlsx, .xls), TSV (.tsv), Text (.txt)

# For Excel, user just writes:
"question": "What is the average price?"
"filename": "file.xlsx"
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'file_loader'"
**Cause:** Container not rebuilt with new module
**Solution:** 
```bash
podman build -t local-llm-celery:dev --format docker .
podman-compose down
podman-compose up -d
```

### Issue: "ModuleNotFoundError: No module named 'openpyxl'"
**Cause:** Excel dependencies not installed
**Solution:** Rebuild container (openpyxl is in requirements.txt)

### Issue: JSON parsing fails
**Cause:** Unexpected JSON structure
**Check:** The JSON loader tries multiple strategies:
- Standard array: `[{...}, {...}]`
- Nested object: `{"data": [{...}]}`
- Lines format: One object per line

**Solution:** Check JSON structure and verify it's one of the supported formats

### Issue: Mixed format analysis fails
**Cause:** LLM not detecting all file types
**Check:** Verify all files are in `/app/data`:
```bash
curl -s http://localhost:5001/data | jq -r '.files[].filename'
```

## Performance Notes

- **CSV**: Fastest (native pandas)
- **TSV**: Same as CSV (just different delimiter)
- **JSON**: Slightly slower (parsing overhead)
- **Excel**: Slowest (binary format, needs openpyxl)
- **Mixed formats**: Depends on number and types of files

## Documentation to Update After Testing

If all tests pass:
1. ✅ README.md - Already updated
2. ✅ FILE-FORMAT-SUPPORT.md - Already updated  
3. ✅ DATA-NORMALIZATION.md - May need examples with non-CSV formats
4. ⏳ EXAMPLES.md - Add examples for JSON, Excel, TSV, mixed formats
5. ⏳ QUICKSTART.md - Update with multi-format examples

## Next Steps After Successful Testing

1. Commit all changes
2. Update EXAMPLES.md with new format examples
3. Consider adding automated tests
4. Document any edge cases discovered
5. Update Kubernetes manifests if needed
6. Create demo showing mixed format analysis

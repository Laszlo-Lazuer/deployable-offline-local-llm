# Data File Format Support

## Current Limitations

### Supported File Types

**Currently Fully Supported:**
- ✅ **CSV** (Comma-Separated Values) - `.csv`

**API Accepts But Not Fully Implemented:**
- ⚠️ **JSON** - `.json` (uploaded but requires manual code in query)
- ⚠️ **TSV** (Tab-Separated Values) - `.tsv` (uploaded but requires manual code in query)
- ⚠️ **TXT** (Plain Text) - `.txt` (uploaded but requires manual code in query)
- ⚠️ **XLSX** (Excel) - `.xlsx` (uploaded but requires manual code in query)

### What This Means

**The API allows file uploads** with these extensions:
```python
ALLOWED_EXTENSIONS = {'csv', 'json', 'txt', 'xlsx', 'tsv'}
```

**However, the normalization and semantic understanding features are CSV-specific:**
- Schema detection: Only works with CSV
- Semantic column guide: Only works with CSV
- Normalization guide: Only works with CSV

**The LLM can still analyze non-CSV files**, but you need to provide explicit loading instructions in your query.

## Current Constraints

### 1. File Size Limit
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```
- Maximum file size: **100MB**
- Reason: Memory constraints during analysis
- For larger files: Consider chunking or sampling

### 2. File Format Support

**CSV Files (Full Support):**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{"question":"What is the average price?","filename":"sales-data.csv"}'
```
- ✅ Automatic schema detection
- ✅ Semantic column understanding  
- ✅ Normalization support
- ✅ Natural language queries

**Excel Files (Partial Support):**
```bash
# Upload works
curl -X POST http://localhost:5001/data \
  -F "file=@sales-data.xlsx"

# Analysis requires explicit instructions
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"Load the Excel file using pd.read_excel(\"/app/data/sales-data.xlsx\") and calculate the average price.",
    "filename":"sales-data.xlsx"
  }'
```
- ✅ Can upload
- ⚠️ Requires explicit pandas code in query
- ❌ No automatic schema detection
- ❌ No semantic understanding

**JSON Files (Partial Support):**
```bash
# Upload works
curl -X POST http://localhost:5001/data \
  -F "file=@data.json"

# Analysis requires explicit instructions
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"Load the JSON file using pd.read_json(\"/app/data/data.json\") and analyze it.",
    "filename":"data.json"
  }'
```
- ✅ Can upload
- ⚠️ Requires explicit pandas code
- ❌ No automatic schema detection
- ❌ No semantic understanding

**Parquet Files (Not Supported):**
```
❌ Cannot upload - not in ALLOWED_EXTENSIONS
❌ No built-in support
```

## Working with Non-CSV Files Today

### Option 1: Explicit Instructions

For files that are uploaded but not auto-detected, provide explicit loading code:

**Excel Example:**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question": "Use pd.read_excel(\"/app/data/sales-data.xlsx\", sheet_name=0) to load the data. Then calculate the average of the \"Price\" column.",
    "filename": "sales-data.xlsx"
  }'
```

**JSON Example:**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question": "Load /app/data/data.json using pd.read_json() with orient=\"records\". Then find the maximum value.",
    "filename": "data.json"
  }'
```

**TSV Example:**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question": "Load /app/data/data.tsv using pd.read_csv() with sep=\"\\t\". Calculate the mean.",
    "filename": "data.tsv"
  }'
```

### Option 2: Convert to CSV

The simplest workaround is converting files to CSV before upload:

```python
import pandas as pd

# Excel to CSV
df = pd.read_excel('sales-data.xlsx')
df.to_csv('sales-data.csv', index=False)

# JSON to CSV
df = pd.read_json('data.json')
df.to_csv('data.csv', index=False)

# Parquet to CSV
df = pd.read_parquet('data.parquet')
df.to_csv('data.csv', index=False)
```

## Expanding File Format Support

To add full support for additional formats, you would need to:

### 1. Update `data_normalization.py`

Add a file loader that handles multiple formats:

```python
def load_file_as_dataframe(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Load any supported file format into a pandas DataFrame.
    
    Supports: CSV, Excel, JSON, TSV, Parquet
    """
    ext = filepath.split('.')[-1].lower()
    
    if ext == 'csv':
        return pd.read_csv(filepath, **kwargs)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(filepath, **kwargs)
    elif ext == 'json':
        return pd.read_json(filepath, **kwargs)
    elif ext == 'tsv':
        return pd.read_csv(filepath, sep='\t', **kwargs)
    elif ext == 'parquet':
        return pd.read_parquet(filepath, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
```

### 2. Update `get_file_schema()`

Replace hardcoded `pd.read_csv()` with the new loader:

```python
def get_file_schema(filepath: str) -> Dict[str, Any]:
    try:
        # OLD: df = pd.read_csv(filepath, nrows=5)
        # NEW:
        df = load_file_as_dataframe(filepath, nrows=5)
        
        # Rest of the function stays the same...
```

### 3. Update Worker Prompt

Update instructions to cover all formats:

```python
full_prompt = f"""
...
2. Load data files using appropriate pandas function:
   - CSV: pd.read_csv('/app/data/filename.csv')
   - Excel: pd.read_excel('/app/data/filename.xlsx')
   - JSON: pd.read_json('/app/data/filename.json')
   - TSV: pd.read_csv('/app/data/filename.tsv', sep='\\t')
   - Parquet: pd.read_parquet('/app/data/filename.parquet')
...
"""
```

### 4. Update `requirements.txt`

Add dependencies for additional formats:

```
# Already included:
pandas>=2.0.0

# Would need to add:
openpyxl>=3.0.0      # For Excel (.xlsx)
xlrd>=2.0.0          # For old Excel (.xls)
pyarrow>=12.0.0      # For Parquet
fastparquet>=2023.0.0  # Alternative Parquet engine
```

### 5. Update `ALLOWED_EXTENSIONS`

Add more formats to `app.py`:

```python
ALLOWED_EXTENSIONS = {
    'csv', 'tsv',           # Text formats
    'xlsx', 'xls',          # Excel
    'json', 'jsonl',        # JSON
    'parquet', 'pq',        # Parquet
    'feather',              # Feather
    'hdf', 'h5'            # HDF5
}
```

## Recommended File Formats

### Best for This System
1. **CSV** - Fully supported, best compatibility
2. **TSV** - Works like CSV with tab separator
3. **JSON** - Good for nested data (with explicit loading)

### Not Recommended
1. **Excel (XLSX)** - Heavier, slower, requires openpyxl
2. **Parquet** - Efficient but requires pyarrow
3. **Binary formats** - Not human-readable, harder to debug

### Why CSV is Preferred

**Advantages:**
- ✅ Universal compatibility
- ✅ Human-readable
- ✅ Simple structure
- ✅ Fast to load
- ✅ Small file size (can compress to .csv.gz)
- ✅ No special dependencies

**Disadvantages:**
- ❌ No schema enforcement
- ❌ No data types (everything is text)
- ❌ Less efficient than binary formats

## Workarounds for Common Scenarios

### Multi-Sheet Excel Files

**Problem:** Excel file has multiple sheets

**Solution 1:** Convert to multiple CSV files
```python
import pandas as pd

xls = pd.ExcelFile('sales-data.xlsx')
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    df.to_csv(f'sales-{sheet_name}.csv', index=False)
```

**Solution 2:** Specify sheet in query
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question": "Load sheet \"Q1_Sales\" from /app/data/sales-data.xlsx using pd.read_excel(..., sheet_name=\"Q1_Sales\") and analyze it.",
    "filename": "sales-data.xlsx"
  }'
```

### Large Files (>100MB)

**Problem:** File exceeds 100MB limit

**Solution 1:** Sample the data
```python
import pandas as pd

df = pd.read_csv('huge-file.csv')
sample = df.sample(n=100000)  # Take 100k random rows
sample.to_csv('sampled-data.csv', index=False)
```

**Solution 2:** Split into chunks
```python
chunk_size = 50000
for i, chunk in enumerate(pd.read_csv('huge-file.csv', chunksize=chunk_size)):
    chunk.to_csv(f'chunk-{i}.csv', index=False)
```

**Solution 3:** Filter before uploading
```python
df = pd.read_csv('huge-file.csv')
recent = df[df['Date'] >= '2024-01-01']  # Only recent data
recent.to_csv('recent-data.csv', index=False)
```

### Nested JSON Data

**Problem:** JSON has nested structures

**Solution:** Flatten before converting to CSV
```python
import pandas as pd
from pandas import json_normalize

with open('nested-data.json') as f:
    data = json.load(f)

df = json_normalize(data)  # Flatten nested structure
df.to_csv('flattened-data.csv', index=False)
```

## API Behavior Summary

| File Type | Upload | Auto-Detect | Semantic Understanding | Normalization |
|-----------|--------|-------------|------------------------|---------------|
| CSV       | ✅ Yes | ✅ Yes      | ✅ Yes                | ✅ Yes       |
| TSV       | ✅ Yes | ❌ No       | ❌ No                 | ❌ No        |
| XLSX      | ✅ Yes | ❌ No       | ❌ No                 | ❌ No        |
| JSON      | ✅ Yes | ❌ No       | ❌ No                 | ❌ No        |
| TXT       | ✅ Yes | ❌ No       | ❌ No                 | ❌ No        |
| Parquet   | ❌ No  | ❌ No       | ❌ No                 | ❌ No        |
| Feather   | ❌ No  | ❌ No       | ❌ No                 | ❌ No        |
| HDF5      | ❌ No  | ❌ No       | ❌ No                 | ❌ No        |

## Future Enhancements

Potential improvements:
1. **Auto-detect file format** - Inspect content, not just extension
2. **Universal schema detection** - Work with any tabular format
3. **Binary format support** - Parquet, Feather, HDF5
4. **Compression support** - .csv.gz, .json.gz
5. **Database connections** - PostgreSQL, MySQL, SQLite
6. **Cloud storage** - S3, GCS, Azure Blob
7. **Streaming support** - Handle files larger than memory
8. **Format conversion API** - Auto-convert uploads to CSV

## Best Practices

### For Users

1. **Use CSV when possible** - Full feature support
2. **Convert Excel to CSV** - Before uploading
3. **Flatten JSON data** - Before uploading
4. **Split large files** - Keep under 100MB
5. **Provide explicit load instructions** - For non-CSV formats

### For Production

1. **Implement format detection** - Don't rely on extensions
2. **Add validation** - Check file structure before processing
3. **Set up monitoring** - Track upload sizes and types
4. **Create conversion pipeline** - Auto-convert to CSV
5. **Document limitations** - Clear user guidance

## Related Documentation

- [DATA-API.md](DATA-API.md) - Upload, update, delete files
- [DATA-NORMALIZATION.md](DATA-NORMALIZATION.md) - Schema handling
- [EXAMPLES.md](EXAMPLES.md) - Query examples
- [README.md](README.md) - Main documentation

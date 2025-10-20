# Data File Format Support

## ✅ Full Multi-Format Support

### Supported File Types

**All formats now fully supported with automatic loading:**
- ✅ **CSV** (Comma-Separated Values) - `.csv`
- ✅ **JSON** - `.json`
- ✅ **Excel** - `.xlsx`, `.xls`
- ✅ **TSV** (Tab-Separated Values) - `.tsv`
- ✅ **TXT** (Plain Text) - `.txt`

### What This Means

**The system now provides:**
- ✅ Automatic file type detection for all formats
- ✅ Universal file loader (`file_loader.py`)
- ✅ Schema detection and normalization for all formats
- ✅ Semantic column understanding for all formats
- ✅ Natural language queries for all formats
- ✅ Multi-file analysis with mixed formats

**The API accepts uploads** with these extensions:
```python
ALLOWED_EXTENSIONS = {'csv', 'json', 'txt', 'xlsx', 'tsv'}
```

## Current Constraints

### 1. File Size Limit
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```
- Maximum file size: **100MB**
- Reason: Memory constraints during analysis
- For larger files: Consider chunking or sampling

### 2. File Format Support

**All Supported Files (Full Support):**

**CSV Files:**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{"question":"What is the average price?","filename":"sales-data.csv"}'
```
- ✅ Automatic loading with `load_file()`
- ✅ Schema detection
- ✅ Semantic column understanding  
- ✅ Normalization support
- ✅ Natural language queries

**Excel Files:**
```bash
# Upload works
curl -X POST http://localhost:5001/data \
  -F "file=@sales-data.xlsx"

# Analysis - no explicit instructions needed
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"What is the average price?",
    "filename":"sales-data.xlsx"
  }'
```
- ✅ Automatic loading with `load_file()`
- ✅ Schema detection
- ✅ Semantic column understanding
- ✅ Normalization support
- ✅ Natural language queries
- ℹ️ Loads first sheet by default

**JSON Files:**
```bash
# Upload works
curl -X POST http://localhost:5001/data \
  -F "file=@data.json"

# Analysis - no explicit instructions needed
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"Analyze the data and show trends.",
    "filename":"data.json"
  }'
```
- ✅ Automatic loading with `load_file()`
- ✅ Supports multiple JSON structures (array, object, lines)
- ✅ Schema detection
- ✅ Semantic column understanding
- ✅ Normalization support
- ✅ Natural language queries

**TSV Files:**
```bash
# Same as CSV, automatically detects tab delimiter
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"What is the total revenue?",
    "filename":"data.tsv"
  }'
```
- ✅ Automatic loading with `load_file()`
- ✅ All features same as CSV

**Text Files:**
```bash
# Attempts to auto-detect delimiter
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"Summarize the data.",
    "filename":"data.txt"
  }'
```
- ✅ Automatic delimiter detection (`,`, `\t`, `|`, `;`)
- ✅ Falls back to single column if needed

**Parquet Files (Not Supported):**
```
❌ Cannot upload - not in ALLOWED_EXTENSIONS
❌ No built-in support
```

## Using the Universal File Loader

### How It Works

The system now uses `file_loader.py` which automatically:
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

## Using the Universal File Loader

### How It Works

The system now uses `file_loader.py` which automatically:

1. **Detects file type** from extension
2. **Selects appropriate loader** (CSV, JSON, Excel, TSV, Text)
3. **Returns pandas DataFrame** ready for analysis

### LLM Instructions

The LLM is instructed to use:

```python
from file_loader import load_file

# Load any supported format - same interface
df = load_file('/app/data/sales-data.csv')
df = load_file('/app/data/sales-data.xlsx')
df = load_file('/app/data/data.json')
df = load_file('/app/data/data.tsv')
df = load_file('/app/data/data.txt')
```

### File Loader Features

**CSV Loader:**
```python
def load_csv(filepath: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(filepath, **kwargs)
```

**JSON Loader (Smart Detection):**
```python
def load_json(filepath: str, **kwargs) -> pd.DataFrame:
    # Tries multiple approaches:
    # 1. Standard array: [{"col1": val1}, ...]
    # 2. Lines format: one object per line
    # 3. Nested structure: {"data": [...]}
```

**Excel Loader:**
```python
def load_excel(filepath: str, **kwargs) -> pd.DataFrame:
    # Loads first sheet by default
    return pd.read_excel(filepath, **kwargs)
```

**TSV Loader:**
```python
def load_tsv(filepath: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(filepath, sep='\t', **kwargs)
```

**Text Loader (Auto-Delimiter):**
```python
def load_txt(filepath: str, **kwargs) -> pd.DataFrame:
    # Tries: comma, tab, pipe, semicolon
    # Falls back to single column
```

## Multi-Format Examples

### Mixed Format Analysis

You can now combine files of different formats:

```bash
# Upload different formats
curl -X POST http://localhost:5001/data -F "file=@q1-sales.csv"
curl -X POST http://localhost:5001/data -F "file=@q2-sales.xlsx"
curl -X POST http://localhost:5001/data -F "file=@q3-sales.json"

# Analyze all together
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"What is the total revenue across all quarters?"
  }'
```

The LLM will:
1. Detect all files (CSV, Excel, JSON)
2. Load each with appropriate loader
3. Normalize schemas if needed
4. Combine and analyze

### JSON Structure Support

**Array Format:**
```json
[
  {"date": "2024-01-15", "revenue": 1250},
  {"date": "2024-01-16", "revenue": 1475}
]
```

**Nested Object:**
```json
{
  "data": [
    {"date": "2024-01-15", "revenue": 1250},
    {"date": "2024-01-16", "revenue": 1475}
  ]
}
```

**Lines Format (newline-delimited):**
```json
{"date": "2024-01-15", "revenue": 1250}
{"date": "2024-01-16", "revenue": 1475}
```

All are automatically handled!

## Best Practices

### File Format Selection

**Use CSV when:**
- ✅ Simple tabular data
- ✅ Maximum compatibility
- ✅ Human-readable
- ✅ Version control friendly

**Use Excel when:**
- ✅ Complex formatting needed
- ✅ Multiple sheets (sheet 1 auto-loaded)
- ✅ Non-technical users provide data
- ⚠️ Larger file sizes

**Use JSON when:**
- ✅ Nested/hierarchical data
- ✅ API responses
- ✅ Configuration data
- ⚠️ Can be complex to flatten

**Use TSV when:**
- ✅ Data contains commas
- ✅ Tab-delimited exports

### File Size Management

All formats respect the 100MB limit:

```python
# For large files, consider:
# 1. Sampling
df = load_file('large_file.csv', nrows=10000)

# 2. Chunking
chunks = pd.read_csv('large_file.csv', chunksize=1000)
for chunk in chunks:
    # Process chunk
    pass

# 3. Filtering columns
df = load_file('wide_file.csv', usecols=['col1', 'col2', 'col3'])
```

### Conversion Utilities

If you need to convert formats before upload:

```python
import pandas as pd

# Excel → CSV
df = pd.read_excel('sales.xlsx')
df.to_csv('sales.csv', index=False)

# JSON → CSV
df = pd.read_json('data.json')
df.to_csv('data.csv', index=False)

# CSV → Excel
df = pd.read_csv('sales.csv')
df.to_excel('sales.xlsx', index=False)

# Multiple CSV → One Excel (multiple sheets)
with pd.ExcelWriter('combined.xlsx') as writer:
    pd.read_csv('q1.csv').to_excel(writer, sheet_name='Q1', index=False)
    pd.read_csv('q2.csv').to_excel(writer, sheet_name='Q2', index=False)
```


## File Format Comparison

| Format | Extension | Upload | Auto-Load | Schema Detection | Semantic | Normalization | Speed | Size |
|--------|-----------|---------|-----------|------------------|----------|---------------|-------|------|
| **CSV** | `.csv` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚡⚡⚡ | Small |
| **TSV** | `.tsv` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚡⚡⚡ | Small |
| **JSON** | `.json` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚡⚡ | Medium |
| **Excel** | `.xlsx`, `.xls` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚡ | Large |
| **Text** | `.txt` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚡⚡⚡ | Small |
| **Parquet** | `.parquet` | ❌ | ❌ | ❌ | ❌ | ❌ | N/A | N/A |
| **Feather** | `.feather` | ❌ | ❌ | ❌ | ❌ | ❌ | N/A | N/A |
| **HDF5** | `.h5`, `.hdf` | ❌ | ❌ | ❌ | ❌ | ❌ | N/A | N/A |

**Legend:**
- ✅ Fully supported
- ⚡⚡⚡ Very fast
- ⚡⚡ Fast  
- ⚡ Moderate

## Expanding to Additional Formats

Want to add Parquet, Feather, or HDF5 support? Here's how:

### 1. Add Dependencies

Update `requirements.txt`:
```
# For Parquet
pyarrow>=12.0.0
fastparquet>=2023.0.0

# For Feather
pyarrow>=12.0.0

# For HDF5
tables>=3.8.0
```

### 2. Update File Loader

Add to `file_loader.py`:
```python
def load_parquet(filepath: str, **kwargs) -> pd.DataFrame:
    """Load Parquet file into DataFrame."""
    try:
        return pd.read_parquet(filepath, **kwargs)
    except Exception as e:
        raise ValueError(f"Failed to load Parquet file {filepath}: {str(e)}")

def load_feather(filepath: str, **kwargs) -> pd.DataFrame:
    """Load Feather file into DataFrame."""
    try:
        return pd.read_feather(filepath, **kwargs)
    except Exception as e:
        raise ValueError(f"Failed to load Feather file {filepath}: {str(e)}")

# Update SUPPORTED_EXTENSIONS
SUPPORTED_EXTENSIONS = {
    '.csv': 'CSV',
    '.json': 'JSON',
    '.txt': 'Text',
    '.xlsx': 'Excel',
    '.xls': 'Excel',
    '.tsv': 'TSV',
    '.parquet': 'Parquet',  # NEW
    '.pq': 'Parquet',       # NEW
    '.feather': 'Feather'   # NEW
}

# Update load_file() loaders dict
loaders = {
    '.csv': load_csv,
    '.json': load_json,
    '.xlsx': load_excel,
    '.xls': load_excel,
    '.tsv': load_tsv,
    '.txt': load_txt,
    '.parquet': load_parquet,  # NEW
    '.pq': load_parquet,       # NEW
    '.feather': load_feather   # NEW
}
```

### 3. Update API

Update `app.py`:
```python
ALLOWED_EXTENSIONS = {
    'csv', 'json', 'txt', 'xlsx', 'xls', 'tsv',  # Existing
    'parquet', 'pq', 'feather'                    # New
}
```

### 4. Rebuild Container

```bash
podman build -t local-llm-celery:dev --format docker .
podman-compose down
podman-compose up -d
```

## Common Issues and Solutions

### Issue: Excel file won't load

**Cause:** Missing `openpyxl` dependency

**Solution:** Already included in `requirements.txt`
```
openpyxl
xlrd  # For older .xls files
```

### Issue: JSON parsing fails

**Cause:** Unexpected JSON structure

**Solution:** The JSON loader tries multiple formats, but for complex nested data:
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"Load the JSON using pd.read_json(\"/app/data/file.json\") and extract the nested data from df[\"results\"][\"items\"]"
  }'
```

### Issue: File too large

**Cause:** Exceeds 100MB limit

**Solution:** 
1. Split into smaller files
2. Sample the data
3. Compress (e.g., CSV → CSV.GZ)
4. Filter columns/rows before upload

### Issue: Delimiter not detected in TXT file

**Cause:** Unusual delimiter

**Solution:** Explicitly specify in query:
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{
    "question":"Load /app/data/file.txt using pd.read_csv(file, sep=\"|\") and analyze it"
  }'
```

## Summary

### What's Supported Now ✅

- **CSV, TSV, TXT**: Full support with auto-detection
- **JSON**: Full support with smart structure detection
- **Excel**: Full support (first sheet by default)
- **Schema Detection**: All formats
- **Normalization**: All formats
- **Semantic Understanding**: All formats
- **Natural Language**: All formats
- **Multi-File Mixed Formats**: Supported

### What's Not Supported ❌

- Parquet (requires pyarrow)
- Feather (requires pyarrow)
- HDF5 (requires tables)
- Files > 100MB

### When to Use What

**CSV** - Best for most use cases (speed, size, compatibility)
**Excel** - When receiving data from non-technical users
**JSON** - For nested/hierarchical data or API responses
**TSV** - When data contains commas
**Text** - Auto-detects delimiter

All formats now have **full feature parity** - use whichever fits your workflow!

## Related Documentation

- [DATA-API.md](DATA-API.md) - Upload, update, delete files
- [DATA-NORMALIZATION.md](DATA-NORMALIZATION.md) - Schema handling and natural language support
- [EXAMPLES.md](EXAMPLES.md) - Query examples
- [README.md](README.md) - Main documentation

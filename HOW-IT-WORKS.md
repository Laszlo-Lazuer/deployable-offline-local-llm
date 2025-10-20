# How the System Works - File Loading Explained

## Your Question: "I thought we automatically used any data files available?"

**Short Answer**: The system **automatically discovers** files and **tells the LLM about them**, but the LLM still needs to **write code** to load them.

---

## What IS Automatic ✅

### 1. File Discovery
```python
# In worker.py - this runs automatically
available_files = os.listdir('/app/data')
# Result: ['sales-data.csv', 'test-sales.tsv', 'test-sales.json']
```

The system automatically:
- Scans the `/app/data` directory
- Lists all files with sizes
- Detects file formats
- Includes this information in the LLM prompt

### 2. File Information in Prompt
```
Available data files in /app/data:
  - sales-data.csv (3,233 bytes) [CSV format]
  - test-sales.tsv (948 bytes) [TSV format]
  - test-sales.json (567 bytes) [JSON format]
```

The LLM automatically **knows** about all files.

### 3. Format Detection
```python
# file_loader.py automatically detects format
df = load_file('/app/data/test-sales.tsv')
# ↑ This function auto-detects it's TSV format and loads it correctly
```

The universal loader automatically:
- Detects file type from extension
- Chooses the right parser (CSV, JSON, Excel, TSV, TXT)
- Loads into a pandas DataFrame

---

## What is NOT Automatic ❌

### The LLM Must Write Code to Load Files

**Think of it like this:**

You're asking an assistant (the LLM) to analyze data. The files are sitting on a desk (in `/app/data`). The assistant can **see** the files (automatic discovery), but they still need to **pick up** and **open** each file (write code to load).

**Analogy:**
```
Automatic:  "Here are the files on your desk: sales.csv, data.tsv, info.json"
Not Automatic: The assistant must still write: "df = load_file('sales.csv')"
```

### Example: What the LLM Generates

When you ask: **"What is the total sales from the TSV file?"**

The system automatically tells the LLM:
```
Available files: test-sales.tsv (948 bytes) [TSV format]

Instructions:
- ALWAYS import: from file_loader import load_file
- Then use: df = load_file('/app/data/test-sales.tsv')
```

The LLM should generate this code:
```python
# Step 1: Import the loader (LLM must write this!)
from file_loader import load_file

# Step 2: Load the file (LLM must write this!)
df = load_file('/app/data/test-sales.tsv')

# Step 3: Answer the question (LLM must write this!)
total_sales = df['Sales'].sum()
print(f"Total sales: ${total_sales:,.2f}")
```

### Why the TSV Test Failed

The LLM tried to skip the import:
```python
# ❌ What it generated:
df = load_file('/app/data/test-sales.tsv')  # ERROR: load_file not defined!

# ✅ What it should have generated:
from file_loader import load_file  # MUST import first!
df = load_file('/app/data/test-sales.tsv')
```

**Result**: `NameError: name 'load_file' is not defined`

---

## Why It Works This Way

### 1. **Open Interpreter Design**
Open Interpreter executes LLM-generated Python code in an isolated environment. Each code cell starts fresh, so imports must be included.

### 2. **Flexibility**
The LLM can choose:
- Which files to load
- When to load them
- How to combine them
- What analysis to perform

If we pre-loaded all files automatically, it would:
- Use unnecessary memory
- Remove flexibility
- Limit what the LLM can do

### 3. **Transparency**
Users can see exactly what code is executing:
```python
from file_loader import load_file  # Clear what's being imported
df = load_file('/app/data/sales.csv')  # Clear what file is loaded
result = df['Revenue'].sum()  # Clear what calculation is done
```

---

## Comparison: Old vs New

### Before (CSV only)
```python
# LLM had to write:
import pandas as pd
df = pd.read_csv('/app/data/sales-data.csv')  # Manual CSV loading
```

### After (Universal Loader - All Formats)
```python
# LLM now writes:
from file_loader import load_file
df = load_file('/app/data/sales-data.csv')  # Auto-detects CSV
df2 = load_file('/app/data/data.json')       # Auto-detects JSON
df3 = load_file('/app/data/info.xlsx')       # Auto-detects Excel
df4 = load_file('/app/data/test.tsv')        # Auto-detects TSV
# All formats work the same way!
```

**What's better:**
- ✅ Same code for all formats (just change filename)
- ✅ No need to remember `pd.read_csv()` vs `pd.read_json()` vs `pd.read_excel()`
- ✅ Format detection is automatic

**What's the same:**
- ❌ Still need to import the loader
- ❌ Still need to write code to load files
- ❌ Still need to write analysis code

---

## The Improved Prompt (Just Updated)

To reduce LLM errors, we made the prompt more explicit:

**Before:**
```
2. Use the universal file loader:
   - Import: from file_loader import load_file
```

**After:**
```
2. ALWAYS start your code by importing the file loader:
   
   from file_loader import load_file
   
3. Use the universal file loader to load ANY supported format:
   - Usage: df = load_file('/app/data/filename.ext')
   - Example: df = load_file('/app/data/test-sales.tsv')  # Auto-detects TSV
```

This makes it **crystal clear** to the LLM: "Step 1 is ALWAYS import the loader first!"

---

## Summary

| What | Automatic? | Explanation |
|------|-----------|-------------|
| **File discovery** | ✅ YES | System scans `/app/data` automatically |
| **File list in prompt** | ✅ YES | LLM knows about all files |
| **Format detection** | ✅ YES | `load_file()` auto-detects format |
| **DataFrame creation** | ✅ YES | `load_file()` returns pandas DataFrame |
| **Import statement** | ❌ NO | LLM must write: `from file_loader import load_file` |
| **Load statement** | ❌ NO | LLM must write: `df = load_file('/app/data/file.ext')` |
| **Analysis code** | ❌ NO | LLM must write: `df['col'].sum()`, etc. |

**Bottom line**: The system does the **heavy lifting** (discovery, detection, parsing), but the LLM still writes the **glue code** (imports, loading, analysis).

---

## Why This Is Actually Good

### Benefits of LLM-Generated Code:

1. **Transparency** - You see exactly what's happening
2. **Flexibility** - LLM can load files conditionally
3. **Debuggable** - If something fails, you can see the code
4. **Teachable** - LLM learns from errors and improves
5. **Auditable** - Code execution is logged

### If Everything Was Automatic:

1. ❌ Black box - no visibility into what's loaded
2. ❌ Memory waste - all files loaded even if not needed
3. ❌ Less flexible - can't choose when/how to load
4. ❌ Harder to debug - errors hidden inside system
5. ❌ No learning - LLM doesn't improve

---

## What Happens Next

With the improved prompt (just updated), the LLM should:

1. ✅ Remember to import `load_file` first
2. ✅ Use it to load any format automatically
3. ✅ Combine multiple formats easily
4. ✅ Generate cleaner, more reliable code

**Next test should succeed!** The prompt now explicitly says "ALWAYS start your code by importing the file loader" with the import statement shown prominently.

---

## Still Confused?

Think of it like using a library in your own code:

```python
# You wouldn't write:
result = requests.get('https://api.example.com')  # ❌ ERROR: requests not imported!

# You'd write:
import requests  # ✅ Import first
result = requests.get('https://api.example.com')  # ✅ Then use it

# Same principle here:
from file_loader import load_file  # ✅ Import first
df = load_file('/app/data/sales.csv')  # ✅ Then use it
```

The system makes the `file_loader` module **available**, but Python still requires you to **import** it before using it. The LLM is writing Python code, so it follows Python's rules!

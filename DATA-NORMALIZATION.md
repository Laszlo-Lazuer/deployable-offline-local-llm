# Data Normalization & Natural Language Column Understanding

## Overview

The Local LLM Celery project includes intelligent data normalization capabilities that enable the LLM to handle datasets with different schemas, column names, and formats. Additionally, it provides **natural language column understanding**, allowing users to refer to columns using plain English instead of exact technical names.

## Key Features

### 1. Natural Language Column Mapping (Single File)
Users don't need to know exact column names:
- User says: **"average price"** → System finds: `Avg_Price`, `AVG_PRICE`, or `avg_price`
- User says: **"when"** or **"date"** → System finds: `Date`, `Event_Date`, `timestamp`
- User says: **"location"** or **"where"** → System finds: `City`, `Location`, `Venue`
- User says: **"people attended"** → System finds: `Attendance`, `Attendees`, `Count`

### 2. Multi-File Schema Normalization
When working with multiple datasets:
- **Different column names**: `City` vs `Location` vs `Venue_City`
- **Different data formats**: `2019-01-01` vs `01/01/2019` vs `1/1/19`
- **Different schemas**: One file has 5 columns, another has 9
- **Different value formats**: `Chicago` vs `CHICAGO` vs ` Chicago `
- **Missing columns**: File A has `Country`, File B doesn't

Traditional ETL pipelines require predefined schemas and rigid transformations. This system **leverages the LLM's intelligence** to handle both natural language queries and schema variations automatically.

## Natural Language Column Understanding

### How It Works

When you submit a query, the system automatically generates a **Semantic Column Guide** for your data:

```
🔍 SEMANTIC COLUMN GUIDE
================================================================================

📌 Column: 'Avg_Price'
   User might say: "avg price", "average price", "mean price", "avg cost"
   Sample values: [110.92, 127.24, 101.71]
   Data type: float64

📌 Column: 'Attendance'
   User might say: "attendance", "count", "attendees", "people", "crowd"
   Sample values: [11432, 13125, 14459]
   Data type: int64
```

The LLM uses this guide to map your natural language to actual column names.

### Example Queries

**Instead of this (technical):**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{"question":"Calculate the mean of the Avg_Price column"}'
```

**You can say this (natural):**
```bash
curl -X POST http://localhost:5001/analyze \
  -d '{"question":"What is the average price?"}'
```

Both work! The system understands semantic meaning.

### Supported Natural Language Patterns

| You Say | System Finds |
|---------|--------------|
| "average price", "mean price", "avg cost" | `Avg_Price`, `AVG_PRICE`, `average_price` |
| "minimum price", "lowest price" | `Min_Price`, `MIN_PRICE`, `minimum_price` |
| "maximum price", "highest price" | `Max_Price`, `MAX_PRICE`, `maximum_price` |
| "date", "when", "time" | `Date`, `Event_Date`, `Timestamp` |
| "location", "where", "place" | `City`, `Location`, `Venue`, `Place` |
| "sales", "revenue", "earnings" | `Revenue`, `Sales`, `Total_Sales`, `Income` |
| "people", "attendance", "crowd" | `Attendance`, `Attendees`, `Count` |
| "event", "show", "concert" | `Event`, `Event_Name`, `Show`, `Concert` |

### Real-World Examples

**Example 1: Price Analysis**
```bash
# Natural language
{"question": "What's the average price across all shows?"}

# LLM Process:
# 1. Sees semantic guide: "average price" → Avg_Price
# 2. Loads data: df = pd.read_csv('sales-data.csv')
# 3. Checks columns: ['Date', 'City', 'Avg_Price', ...]
# 4. Maps: "average price" → 'Avg_Price'
# 5. Calculates: df['Avg_Price'].mean()

# Result: $135.19
```

**Example 2: Attendance Query**
```bash
# Natural language
{"question": "How many people attended the shows in total?"}

# LLM Process:
# 1. Sees semantic guide: "people attended" → Attendance
# 2. Maps: "people" → 'Attendance'
# 3. Calculates: df['Attendance'].sum()

# Result: 594,807 total attendees
```

**Example 3: Location Analysis**
```bash
# Natural language
{"question": "Which location had the highest sales?"}

# LLM Process:
# 1. Maps: "location" → 'City', "sales" → 'Revenue'
# 2. Groups: df.groupby('City')['Revenue'].sum()
# 3. Finds max

# Result: Miami with highest sales
```

## Multi-File Schema Normalization

### LLM-Driven Normalization

Instead of hardcoded ETL rules, the LLM:

1. **Inspects** each file's schema automatically
2. **Understands** which columns represent the same data
3. **Normalizes** data to a consistent format
4. **Combines** files only after proper alignment

### How It Works

```
┌─────────────────┐
│  File 1.csv     │ → Schema: {Event_Date, Location, Ticket_Cost}
│  File 2.csv     │ → Schema: {Date, City, Avg_Price}
│  File 3.csv     │ → Schema: {Date, City, Revenue, Attendance}
└─────────────────┘
         │
         ▼
  ┌──────────────┐
  │  LLM Inspect │ → "I see 3 files with different schemas..."
  └──────────────┘
         │
         ▼
  ┌──────────────┐
  │  LLM Map     │ → Event_Date → date
  │  Columns     │    Location → city
  └──────────────┘    Ticket_Cost → price
         │
         ▼
  ┌──────────────┐
  │  LLM         │ → Apply .rename(), .str.title(), etc.
  │  Normalize   │
  └──────────────┘
         │
         ▼
  ┌──────────────┐
  │  Combined    │ → All files aligned with same schema
  │  Dataset     │
  └──────────────┘
```

## Multi-File Schema Normalization

### LLM-Driven Normalization

Instead of hardcoded ETL rules, the LLM:

1. **Inspects** each file's schema automatically
2. **Understands** which columns represent the same data
3. **Normalizes** data to a consistent format
4. **Combines** files only after proper alignment

### How It Works

```
┌─────────────────┐
│  File 1.csv     │ → Schema: {Event_Date, Location, Ticket_Cost}
│  File 2.csv     │ → Schema: {Date, City, Avg_Price}
│  File 3.csv     │ → Schema: {Date, City, Revenue, Attendance}
└─────────────────┘
         │
         ▼
  ┌──────────────┐
  │  LLM Inspect │ → "I see 3 files with different schemas..."
  └──────────────┘
         │
         ▼
  ┌──────────────┐
  │  LLM Map     │ → Event_Date → date
  │  Columns     │    Location → city
  └──────────────┘    Ticket_Cost → price
         │
         ▼
  ┌──────────────┐
  │  LLM         │ → Apply .rename(), .str.title(), etc.
  │  Normalize   │
  └──────────────┘
         │
         ▼
  ┌──────────────┐
  │  Combined    │ → All files aligned with same schema
  │  Dataset     │
  └──────────────┘
```

## Why This Matters

### Problem Scenarios

**Scenario 1: Non-Technical Users**
```
❌ User has to know: "Calculate mean of Avg_Price column"
✅ User can ask: "What's the average price?"
```

**Scenario 2: Acronyms and Abbreviations**
```
Data has columns: AVG_PRICE, MIN_PRICE, MAX_PRICE
❌ User must use exact: "What is the AVG_PRICE?"
✅ User can ask naturally: "What's the average price?"
```

**Scenario 3: Varying Column Names**
```
Different files use: Avg_Price, avg_price, AveragePrice, average_price
❌ Traditional: Requires exact matching
✅ With LLM: Understands all variations
```

**Scenario 4: Multiple Data Sources**
```
Marketing team: Event_Date, Location, Ticket_Cost
Finance team: Date, City, Revenue
Operations: show_date, venue_city, gross_sales
❌ Traditional: Rigid ETL pipeline required
✅ With LLM: Automatic normalization
```

## Features

### Automatic Schema Detection

The system automatically generates schema information for all files:

```python
📊 DATA SCHEMA ANALYSIS
================================================================================

📁 concert-sales.csv
   Rows: 5 | Columns: 5

   Columns:
   - Event_Date           (object    ) → ['2019-03-15', '2019-04-20']
   - Location             (object    ) → ['Chicago', 'New York']
   - Ticket_Cost          (float64   ) → [125.0, 135.5]

📁 sales-data.csv
   Rows: 36 | Columns: 9

   Columns:
   - Date                 (object    ) → ['2019-03-18', '2019-03-20']
   - City                 (object    ) → ['Albany', 'Boston']
   - Avg_Price            (float64   ) → [110.92, 127.24]
```

### Intelligent Column Mapping

The system suggests which columns across files represent similar data:

```
Date Columns:
  - concert-sales.csv:Event_Date
  - sales-data.csv:Date
  - q2-sales.csv:Date

Price Columns:
  - concert-sales.csv:Ticket_Cost
  - sales-data.csv:Avg_Price
  - q2-sales.csv:Avg_Price

Location Columns:
  - concert-sales.csv:Location
  - sales-data.csv:City
  - q2-sales.csv:City
```

### LLM Normalization Workflow

The LLM follows a systematic approach:

1. **Load** each file individually
2. **Inspect** schema and print columns
3. **Map** columns to standard names
4. **Rename** columns using `.rename()`
5. **Standardize** values (strip, case, types)
6. **Align** schemas (add missing columns)
7. **Combine** with `pd.concat()`

## Usage Examples

### Example 1: Different Column Names

**Files:**
```
concert-sales.csv: Event_Date, Location, Ticket_Cost
sales-data.csv:    Date,       City,     Avg_Price
```

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Combine concert-sales.csv and sales-data.csv. They have different column names - normalize first, then calculate average price across all data.",
    "filename": "sales-data.csv"
  }'
```

**LLM Process:**
```python
# Step 1: Load and inspect
df1 = pd.read_csv('/app/data/concert-sales.csv')
df2 = pd.read_csv('/app/data/sales-data.csv')

print("File 1 columns:", df1.columns.tolist())
# ['Event_Date', 'Location', 'Ticket_Cost']

print("File 2 columns:", df2.columns.tolist())
# ['Date', 'City', 'Avg_Price']

# Step 2: Normalize column names
df1 = df1.rename(columns={
    'Event_Date': 'date',
    'Location': 'city',
    'Ticket_Cost': 'price'
})

df2 = df2.rename(columns={
    'Date': 'date',
    'City': 'city',
    'Avg_Price': 'price'
})

# Step 3: Standardize values
df1['city'] = df1['city'].str.strip().str.title()
df2['city'] = df2['city'].str.strip().str.title()

# Step 4: Align schemas (add missing columns)
for col in df2.columns:
    if col not in df1.columns:
        df1[col] = None

for col in df1.columns:
    if col not in df2.columns:
        df2[col] = None

# Step 5: Combine
combined = pd.concat([df1, df2], ignore_index=True)

# Step 6: Analyze
average_price = combined['price'].mean()
```

**Result:** Successfully combines files with different schemas.

### Example 2: Complete Multi-File Analysis

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Combine ALL data files and calculate total revenue. The files have different schemas - inspect and normalize them first. Show your normalization steps.",
    "filename": "sales-data.csv"
  }'
```

**LLM Output:**
```
Step 1: Loading files
- sales-data.csv: 36 rows
- q2-sales.csv: 3 rows
- concert-sales.csv: 5 rows

Step 2: Schema Inspection
sales-data.csv: ['Date', 'City', 'Revenue', 'Attendance', ...]
q2-sales.csv: ['Date', 'City', 'Revenue', 'Attendance', ...]
concert-sales.csv: ['Event_Date', 'Location', 'Total_Sales', 'Attendees', ...]

Step 3: Normalization
- Renamed Event_Date → Date
- Renamed Location → City
- Renamed Total_Sales → Revenue
- Renamed Attendees → Attendance

Step 4: Combining
Combined dataset: 44 rows

Step 5: Analysis
Total Revenue: $70,182,767
```

### Example 3: Date Format Standardization

**Query:**
```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "The files have different date formats. Normalize all dates to YYYY-MM-DD, then find all events in March 2019.",
    "filename": "sales-data.csv"
  }'
```

**LLM Code:**
```python
# Load files
df1 = pd.read_csv('/app/data/file1.csv')
df2 = pd.read_csv('/app/data/file2.csv')

# Inspect date formats
print("File 1 dates:", df1['date'].head())
# 2019-03-15, 2019-04-20 (already YYYY-MM-DD)

print("File 2 dates:", df2['event_date'].head())
# 03/15/2019, 04/20/2019 (MM/DD/YYYY)

# Normalize to datetime
df1['date'] = pd.to_datetime(df1['date'])
df2['date'] = pd.to_datetime(df2['event_date'])

# Standardize format
df1['date'] = df1['date'].dt.strftime('%Y-%m-%d')
df2['date'] = df2['date'].dt.strftime('%Y-%m-%d')

# Filter for March 2019
combined = pd.concat([df1, df2])
march_events = combined[combined['date'].str.startswith('2019-03')]
```

## Normalization Strategies

The LLM applies these strategies automatically:

### 1. Column Renaming
```python
# Different names, same meaning
df.rename(columns={
    'Event_Date': 'date',
    'Location': 'city',
    'Ticket_Cost': 'price',
    'Attendees': 'attendance',
    'Total_Sales': 'revenue'
})
```

### 2. Value Standardization
```python
# Normalize string values
df['city'] = df['city'].str.strip()      # Remove whitespace
df['city'] = df['city'].str.title()      # Consistent case
df['name'] = df['name'].str.upper()       # Uppercase
```

### 3. Type Conversion
```python
# Ensure consistent types
df['date'] = pd.to_datetime(df['date'])
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['count'] = df['count'].astype(int)
```

### 4. Schema Alignment
```python
# Add missing columns
all_columns = set(df1.columns) | set(df2.columns)
for col in all_columns:
    if col not in df1.columns:
        df1[col] = None
    if col not in df2.columns:
        df2[col] = None
```

### 5. Null Handling
```python
# Consistent null values
df = df.fillna({
    'country': 'Unknown',
    'revenue': 0,
    'attendance': 0
})
```

## Real-World Example

### Scenario: Concert Ticket Sales Analysis

You have three files from different departments:

**marketing_data.csv:**
```csv
Event_Date,Location,Ticket_Cost
2019-03-15,Chicago,125.00
```

**finance_data.csv:**
```csv
Date,City,Revenue,Attendance
2019-03-18,Albany,1268045,11432
```

**ops_data.csv:**
```csv
show_date,venue_city,gross_sales,headcount
03/20/2019,Boston,1670045,13125
```

**Question:** "What's the total revenue across all departments?"

**Without Normalization:**
```python
# ❌ This would fail - different column names!
total = (
    df1['Ticket_Cost'].sum() +  # Not the same as revenue
    df2['Revenue'].sum() +
    df3['gross_sales'].sum()
)
```

**With LLM Normalization:**
```python
# ✅ LLM handles it automatically

# Step 1: Inspect
print("marketing:", df1.columns)  # Event_Date, Location, Ticket_Cost
print("finance:", df2.columns)     # Date, City, Revenue, Attendance
print("ops:", df3.columns)          # show_date, venue_city, gross_sales, headcount

# Step 2: Map columns
# Event_Date / Date / show_date → date
# Location / City / venue_city → city
# Ticket_Cost / Revenue / gross_sales → revenue (but Ticket_Cost needs calculation!)

# Step 3: Normalize
df1 = df1.rename(columns={'Event_Date': 'date', 'Location': 'city'})
df2 = df2.rename(columns={'Date': 'date', 'City': 'city', 'Revenue': 'revenue'})
df3 = df3.rename(columns={'show_date': 'date', 'venue_city': 'city', 'gross_sales': 'revenue'})

# Step 4: Handle dates
df1['date'] = pd.to_datetime(df1['date'])
df2['date'] = pd.to_datetime(df2['date'])
df3['date'] = pd.to_datetime(df3['show_date'], format='%m/%d/%Y')

# Step 5: Calculate revenue where needed
# Ticket_Cost is per-ticket, not total - need attendance!
# This file doesn't have total revenue, skip for total calc

# Step 6: Combine and calculate
total_revenue = df2['revenue'].sum() + df3['revenue'].sum()
```

## Benefits

### 1. Flexibility
- ✅ No need to pre-standardize data
- ✅ Works with any column names
- ✅ Handles missing columns gracefully

### 2. Intelligence
- ✅ LLM understands semantic meaning
- ✅ Recognizes `Location` = `City` = `venue_city`
- ✅ Adapts to data structure

### 3. Transparency
- ✅ Shows normalization steps
- ✅ Prints before/after schemas
- ✅ Explains transformations

### 4. Robustness
- ✅ Handles errors gracefully
- ✅ Validates transformations
- ✅ Falls back when needed

## Technical Implementation

### Normalization Module

```python
from data_normalization import (
    get_file_schema,           # Get schema for one file
    generate_schema_summary,    # Summary of all files
    suggest_column_mappings,    # Suggest which columns match
    generate_normalization_guide # Complete guide for LLM
)

# Get schema for specific file
schema = get_file_schema('/app/data/sales.csv')
# Returns: {columns: {...}, row_count: 36, sample_data: [...]}

# Get summary for all files
summary = generate_schema_summary('/app/data')
# Returns formatted string with all schemas

# Get column mapping suggestions
mappings = suggest_column_mappings('/app/data')
# Returns: {date_columns: [...], price_columns: [...], ...}
```

### LLM Integration

When multiple files exist, the worker automatically includes normalization guidance in the prompt:

```python
if len(available_files) > 1:
    normalization_context = generate_normalization_guide(data_dir)
    # LLM receives complete schema analysis and normalization strategies
```

## Best Practices

### 1. Always Inspect First
```python
# ✅ Good: Inspect before combining
df1 = pd.read_csv('file1.csv')
df2 = pd.read_csv('file2.csv')
print("File 1:", df1.columns)
print("File 2:", df2.columns)
# Then normalize...

# ❌ Bad: Assume structure
combined = pd.concat([df1, df2])  # Might fail!
```

### 2. Validate After Normalization
```python
# ✅ Good: Verify alignment
print("After normalization:")
print("File 1:", df1.columns)
print("File 2:", df2.columns)
assert df1.columns.tolist() == df2.columns.tolist()

# Then combine
combined = pd.concat([df1, df2])
```

### 3. Handle Missing Data
```python
# ✅ Good: Explicit handling
df1['country'] = df1.get('country', 'Unknown')
df2['country'] = df2.get('country', 'Unknown')

# ❌ Bad: Ignore missing columns
# Will cause issues during concat
```

### 4. Document Transformations
```python
# ✅ Good: Show your work
print("Normalizing concert-sales.csv:")
print("- Renamed Event_Date → date")
print("- Renamed Location → city")
print("- Renamed Ticket_Cost → price")
```

## Troubleshooting

### Files Won't Combine

**Problem:** `pd.concat()` fails with column mismatch

**Solution:**
```python
# Check schemas first
print("DF1 columns:", df1.columns.tolist())
print("DF2 columns:", df2.columns.tolist())

# Align before combining
all_cols = set(df1.columns) | set(df2.columns)
for col in all_cols:
    if col not in df1:
        df1[col] = None
    if col not in df2:
        df2[col] = None
```

### Data Types Mismatch

**Problem:** Same column name but different types

**Solution:**
```python
# Check types
print(df1['price'].dtype)  # float64
print(df2['price'].dtype)  # object (string!)

# Convert to same type
df2['price'] = pd.to_numeric(df2['price'], errors='coerce')
```

### Values Don't Match

**Problem:** `Chicago` vs `CHICAGO` vs ` Chicago `

**Solution:**
```python
# Standardize string values
df['city'] = df['city'].str.strip().str.title()
```

## Related Documentation

- [MULTI-FILE-ANALYSIS.md](MULTI-FILE-ANALYSIS.md) - Multi-file analysis guide
- [EXAMPLES.md](EXAMPLES.md) - More query examples
- [DATA-API.md](DATA-API.md) - Data management API
- [README.md](README.md) - Main documentation

## Future Enhancements

- Automatic schema learning across queries
- Schema versioning and migration
- Custom normalization rules
- Data quality scoring
- Anomaly detection during normalization

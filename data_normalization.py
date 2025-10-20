"""
Data Normalization Module

Provides LLM-driven intelligent data normalization and schema detection
for handling datasets with varying structures and formats.

This module helps the LLM:
1. Inspect and understand data structure
2. Detect schema and column mappings
3. Normalize data into consistent formats
4. Handle common data quality issues
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional


# Cache directory for schema mappings
SCHEMA_CACHE_DIR = Path("/app/cache/schemas")


def ensure_schema_cache():
    """Create schema cache directory if it doesn't exist."""
    SCHEMA_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_file_schema(filepath: str) -> Dict[str, Any]:
    """
    Analyze a file and extract its schema information.
    
    Args:
        filepath: Path to the data file
        
    Returns:
        dict: Schema information including columns, types, sample data
    """
    try:
        df = pd.read_csv(filepath, nrows=5)  # Read first 5 rows for inspection
        
        schema = {
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "row_count": len(pd.read_csv(filepath)),
            "column_count": len(df.columns),
            "columns": {},
            "sample_data": df.head(3).to_dict('records')
        }
        
        # Analyze each column
        for col in df.columns:
            schema["columns"][col] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "sample_values": df[col].dropna().head(3).tolist()
            }
        
        return schema
        
    except Exception as e:
        return {
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "error": str(e)
        }


def generate_schema_summary(data_dir: str = "/app/data") -> str:
    """
    Generate a comprehensive schema summary for all files in data directory.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        str: Formatted schema summary for LLM consumption
    """
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not files:
        return "No CSV files found in data directory."
    
    summary = "📊 DATA SCHEMA ANALYSIS\n"
    summary += "=" * 80 + "\n\n"
    
    for filename in sorted(files):
        filepath = os.path.join(data_dir, filename)
        schema = get_file_schema(filepath)
        
        if "error" in schema:
            summary += f"❌ {filename}: ERROR - {schema['error']}\n\n"
            continue
        
        summary += f"📁 {filename}\n"
        summary += f"   Rows: {schema['row_count']:,} | Columns: {schema['column_count']}\n\n"
        
        summary += "   Columns:\n"
        for col_name, col_info in schema["columns"].items():
            summary += f"   - {col_name:20s} ({col_info['dtype']:10s})"
            if col_info['sample_values']:
                samples = str(col_info['sample_values'][:2])
                summary += f" → {samples}\n"
            else:
                summary += " → [no data]\n"
        
        summary += "\n"
    
    return summary


def suggest_column_mappings(data_dir: str = "/app/data") -> Dict[str, Dict[str, str]]:
    """
    Suggest column mappings across different files to help normalize data.
    
    Returns a mapping suggesting which columns might represent the same data
    across different files, even if named differently.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        dict: Suggested column mappings between files
    """
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    schemas = {}
    
    # Get all schemas
    for filename in files:
        filepath = os.path.join(data_dir, filename)
        schemas[filename] = get_file_schema(filepath)
    
    # Common column name patterns
    mappings = {
        "date_columns": [],
        "price_columns": [],
        "location_columns": [],
        "revenue_columns": [],
        "quantity_columns": []
    }
    
    for filename, schema in schemas.items():
        if "error" in schema:
            continue
            
        for col_name in schema["columns"].keys():
            col_lower = col_name.lower()
            
            # Detect date columns
            if any(word in col_lower for word in ['date', 'time', 'year', 'month', 'day']):
                mappings["date_columns"].append(f"{filename}:{col_name}")
            
            # Detect price columns
            if any(word in col_lower for word in ['price', 'cost', 'amount', 'rate']):
                mappings["price_columns"].append(f"{filename}:{col_name}")
            
            # Detect location columns
            if any(word in col_lower for word in ['city', 'location', 'venue', 'place', 'country']):
                mappings["location_columns"].append(f"{filename}:{col_name}")
            
            # Detect revenue columns
            if any(word in col_lower for word in ['revenue', 'sales', 'income', 'earnings']):
                mappings["revenue_columns"].append(f"{filename}:{col_name}")
            
            # Detect quantity columns
            if any(word in col_lower for word in ['count', 'quantity', 'attendance', 'volume']):
                mappings["quantity_columns"].append(f"{filename}:{col_name}")
    
    return mappings


def generate_normalization_guide(data_dir: str = "/app/data") -> str:
    """
    Generate a comprehensive guide for the LLM to normalize data.
    
    This provides the LLM with:
    1. Schema information for all files
    2. Suggested column mappings
    3. Normalization strategies
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        str: Complete normalization guide
    """
    guide = "🔧 DATA NORMALIZATION GUIDE\n"
    guide += "=" * 80 + "\n\n"
    
    # Schema summary
    guide += generate_schema_summary(data_dir)
    
    # Column mappings
    mappings = suggest_column_mappings(data_dir)
    
    guide += "\n📋 SUGGESTED COLUMN MAPPINGS\n"
    guide += "=" * 80 + "\n\n"
    
    for category, columns in mappings.items():
        if columns:
            guide += f"{category.replace('_', ' ').title()}:\n"
            for col in columns:
                guide += f"  - {col}\n"
            guide += "\n"
    
    # Normalization strategies
    guide += "\n💡 NORMALIZATION STRATEGIES\n"
    guide += "=" * 80 + "\n\n"
    
    guide += """
1. COLUMN RENAMING:
   - Identify columns with similar meanings across files
   - Rename to a standard naming convention
   - Example: 'City', 'Location', 'Venue_City' → 'city'

2. DATA TYPE CONVERSION:
   - Ensure consistent data types for similar columns
   - Convert dates to datetime format
   - Convert prices/amounts to float
   - Example: '2019-01-01' vs '01/01/2019' → pd.to_datetime()

3. VALUE STANDARDIZATION:
   - Normalize string values (case, whitespace)
   - Handle missing values consistently
   - Example: 'Chicago', 'CHICAGO', ' Chicago ' → 'Chicago'

4. SCHEMA ALIGNMENT:
   - Add missing columns with default values
   - Ensure all files have the same columns
   - Example: If file1 has 'Country' but file2 doesn't, add 'Country' = None to file2

5. CONCATENATION:
   - Only combine files after normalization
   - Use pd.concat() with proper handling of indices
   - Verify data integrity after combination

EXAMPLE NORMALIZATION CODE:
```python
# Load files
df1 = pd.read_csv('/app/data/file1.csv')
df2 = pd.read_csv('/app/data/file2.csv')

# Inspect schemas first
print("File1 columns:", df1.columns.tolist())
print("File2 columns:", df2.columns.tolist())

# Rename columns to match
df1 = df1.rename(columns={'Location': 'city', 'Price': 'price'})
df2 = df2.rename(columns={'City': 'city', 'Amount': 'price'})

# Standardize values
df1['city'] = df1['city'].str.strip().str.title()
df2['city'] = df2['city'].str.strip().str.title()

# Convert types
df1['price'] = pd.to_numeric(df1['price'], errors='coerce')
df2['price'] = pd.to_numeric(df2['price'], errors='coerce')

# Ensure same columns
all_columns = set(df1.columns) | set(df2.columns)
for col in all_columns:
    if col not in df1.columns:
        df1[col] = None
    if col not in df2.columns:
        df2[col] = None

# Now combine
combined = pd.concat([df1, df2], ignore_index=True)
```
"""
    
    return guide


def generate_semantic_column_guide(filepath: str) -> str:
    """
    Generate a semantic understanding guide for a single file's columns.
    
    This helps the LLM understand what users mean when they use natural language
    instead of exact column names.
    
    Args:
        filepath: Path to the data file
        
    Returns:
        str: Semantic column guide for LLM
    """
    schema = get_file_schema(filepath)
    
    if "error" in schema:
        return f"Error analyzing file: {schema['error']}"
    
    guide = f"🔍 SEMANTIC COLUMN GUIDE for {schema['filename']}\n"
    guide += "=" * 80 + "\n\n"
    
    guide += "The file contains these columns. Users may refer to them using natural language:\n\n"
    
    for col_name, col_info in schema["columns"].items():
        guide += f"📌 Column: '{col_name}'\n"
        
        # Generate semantic alternatives
        alternatives = generate_column_semantics(col_name)
        guide += f"   User might say: {', '.join(alternatives)}\n"
        
        # Show sample values to help LLM understand
        if col_info['sample_values']:
            guide += f"   Sample values: {col_info['sample_values'][:3]}\n"
        
        guide += f"   Data type: {col_info['dtype']}\n\n"
    
    guide += "\n💡 NATURAL LANGUAGE MAPPING:\n"
    guide += "When user asks about data, map their natural language to actual columns:\n"
    guide += "- 'average price' → look for Avg_Price, AVG_PRICE, avg_price, or similar\n"
    guide += "- 'date' or 'when' → look for Date, Event_Date, date, timestamp, etc.\n"
    guide += "- 'location' or 'where' → look for City, Location, Venue, Place, etc.\n"
    guide += "- 'revenue' or 'sales' → look for Revenue, Sales, Total_Sales, etc.\n"
    guide += "- 'attendance' or 'count' → look for Attendance, Count, Attendees, etc.\n\n"
    
    guide += "ALWAYS inspect df.columns.tolist() first, then use the actual column names.\n"
    
    return guide


def generate_column_semantics(column_name: str) -> list:
    """
    Generate semantic alternatives for a column name.
    
    Args:
        column_name: The actual column name
        
    Returns:
        list: Natural language alternatives
    """
    col_lower = column_name.lower().replace('_', ' ').replace('-', ' ')
    alternatives = [f'"{col_lower}"']
    
    # Common semantic mappings
    semantic_map = {
        'avg': ['average', 'mean'],
        'min': ['minimum', 'lowest'],
        'max': ['maximum', 'highest'],
        'price': ['cost', 'amount', 'rate'],
        'date': ['when', 'time', 'timestamp'],
        'city': ['location', 'where', 'place'],
        'venue': ['location', 'place', 'arena', 'stadium'],
        'attendance': ['count', 'attendees', 'people', 'crowd'],
        'revenue': ['sales', 'income', 'earnings', 'total'],
        'event': ['show', 'concert', 'performance'],
    }
    
    # Check each word in column name
    words = col_lower.split()
    for word in words:
        if word in semantic_map:
            for sem in semantic_map[word]:
                alt_phrase = col_lower.replace(word, sem)
                if alt_phrase not in alternatives:
                    alternatives.append(f'"{alt_phrase}"')
    
    return alternatives[:5]  # Limit to 5 alternatives


def save_normalization_schema(schema_name: str, schema: Dict[str, Any]):
    """
    Save a normalization schema for reuse.
    
    Args:
        schema_name: Name for the schema
        schema: Schema definition
    """
    ensure_schema_cache()
    schema_file = SCHEMA_CACHE_DIR / f"{schema_name}.json"
    
    with open(schema_file, 'w') as f:
        json.dump(schema, f, indent=2)
    
    print(f"Saved normalization schema: {schema_name}")


def load_normalization_schema(schema_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a saved normalization schema.
    
    Args:
        schema_name: Name of the schema to load
        
    Returns:
        dict: Schema definition or None if not found
    """
    schema_file = SCHEMA_CACHE_DIR / f"{schema_name}.json"
    
    if not schema_file.exists():
        return None
    
    with open(schema_file, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    # Test the module
    print("Testing Data Normalization Module")
    print("=" * 80)
    
    # Generate schema summary
    print("\n" + generate_schema_summary())
    
    # Generate normalization guide
    print("\n" + generate_normalization_guide())

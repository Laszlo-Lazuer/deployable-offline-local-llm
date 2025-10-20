"""
File Loader Module

Provides universal file loading capabilities for all supported formats:
- CSV (.csv)
- JSON (.json)
- Excel (.xlsx, .xls)
- TSV (.tsv)
- Text (.txt)

Automatically detects file type and loads into pandas DataFrame.
"""

import os
import pandas as pd
import json
from pathlib import Path
from typing import Optional, Dict, Any


# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.csv': 'CSV',
    '.json': 'JSON',
    '.txt': 'Text',
    '.xlsx': 'Excel',
    '.xls': 'Excel',
    '.tsv': 'TSV'
}


def get_file_type(filepath: str) -> str:
    """
    Determine the file type from extension.
    
    Args:
        filepath: Path to the file
        
    Returns:
        str: File type (CSV, JSON, Excel, TSV, Text)
    """
    ext = Path(filepath).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext, 'Unknown')


def load_csv(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Load CSV file into DataFrame.
    
    Args:
        filepath: Path to CSV file
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        pd.DataFrame: Loaded data
    """
    try:
        return pd.read_csv(filepath, **kwargs)
    except Exception as e:
        raise ValueError(f"Failed to load CSV file {filepath}: {str(e)}")


def load_json(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Load JSON file into DataFrame.
    Supports multiple JSON structures:
    - Array of objects: [{"col1": val1, "col2": val2}, ...]
    - Object with data key: {"data": [...]}
    - Lines format: one JSON object per line
    
    Args:
        filepath: Path to JSON file
        **kwargs: Additional arguments for pd.read_json
        
    Returns:
        pd.DataFrame: Loaded data
    """
    try:
        # Try standard JSON array
        df = pd.read_json(filepath, **kwargs)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
    except:
        pass
    
    try:
        # Try lines format (one JSON per line)
        df = pd.read_json(filepath, lines=True, **kwargs)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
    except:
        pass
    
    try:
        # Try loading raw JSON and extracting data
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # If it's a dict with a common data key
        if isinstance(data, dict):
            for key in ['data', 'records', 'rows', 'items', 'results']:
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key])
            
            # If dict has consistent structure, treat as single record
            return pd.DataFrame([data])
        
        # If it's a list
        if isinstance(data, list):
            return pd.DataFrame(data)
            
    except Exception as e:
        raise ValueError(f"Failed to load JSON file {filepath}: {str(e)}")
    
    raise ValueError(f"Could not parse JSON file {filepath} into DataFrame")


def load_excel(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Load Excel file into DataFrame.
    
    Args:
        filepath: Path to Excel file
        **kwargs: Additional arguments for pd.read_excel
        
    Returns:
        pd.DataFrame: Loaded data from first sheet
    """
    try:
        # Load first sheet by default
        return pd.read_excel(filepath, **kwargs)
    except Exception as e:
        raise ValueError(f"Failed to load Excel file {filepath}: {str(e)}")


def load_tsv(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Load TSV (Tab-Separated Values) file into DataFrame.
    
    Args:
        filepath: Path to TSV file
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        pd.DataFrame: Loaded data
    """
    try:
        return pd.read_csv(filepath, sep='\t', **kwargs)
    except Exception as e:
        raise ValueError(f"Failed to load TSV file {filepath}: {str(e)}")


def load_txt(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Load text file into DataFrame.
    Attempts to detect delimiter automatically.
    
    Args:
        filepath: Path to text file
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        pd.DataFrame: Loaded data
    """
    try:
        # Try common delimiters
        for sep in [',', '\t', '|', ';']:
            try:
                df = pd.read_csv(filepath, sep=sep, **kwargs)
                # Check if parsing was successful (more than 1 column)
                if len(df.columns) > 1:
                    return df
            except:
                continue
        
        # Fall back to reading as single column
        return pd.read_csv(filepath, **kwargs)
        
    except Exception as e:
        raise ValueError(f"Failed to load text file {filepath}: {str(e)}")


def load_file(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Universal file loader - automatically detects type and loads accordingly.
    
    Supported formats:
    - CSV (.csv)
    - JSON (.json) 
    - Excel (.xlsx, .xls)
    - TSV (.tsv)
    - Text (.txt)
    
    Args:
        filepath: Path to the file
        **kwargs: Additional arguments passed to specific loader
        
    Returns:
        pd.DataFrame: Loaded data
        
    Raises:
        ValueError: If file type is not supported or loading fails
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    file_type = get_file_type(filepath)
    ext = Path(filepath).suffix.lower()
    
    loaders = {
        '.csv': load_csv,
        '.json': load_json,
        '.xlsx': load_excel,
        '.xls': load_excel,
        '.tsv': load_tsv,
        '.txt': load_txt
    }
    
    loader = loaders.get(ext)
    if not loader:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
    
    try:
        df = loader(filepath, **kwargs)
        
        # Validate result
        if df is None or df.empty:
            raise ValueError("Loaded DataFrame is empty")
        
        return df
        
    except Exception as e:
        raise ValueError(f"Failed to load file {filepath}: {str(e)}")


def get_file_info(filepath: str) -> Dict[str, Any]:
    """
    Get basic information about a file without fully loading it.
    
    Args:
        filepath: Path to the file
        
    Returns:
        dict: File information (size, type, extension, etc.)
    """
    if not os.path.exists(filepath):
        return {"error": "File not found"}
    
    stat = os.stat(filepath)
    ext = Path(filepath).suffix.lower()
    
    return {
        "filename": os.path.basename(filepath),
        "filepath": filepath,
        "extension": ext,
        "file_type": get_file_type(filepath),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "exists": True
    }


def preview_file(filepath: str, rows: int = 5) -> Dict[str, Any]:
    """
    Load a preview of the file (first N rows).
    
    Args:
        filepath: Path to the file
        rows: Number of rows to preview
        
    Returns:
        dict: File info + preview data
    """
    try:
        info = get_file_info(filepath)
        
        # Load preview
        df = load_file(filepath, nrows=rows)
        
        info.update({
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview": df.head(rows).to_dict('records')
        })
        
        return info
        
    except Exception as e:
        return {
            **get_file_info(filepath),
            "error": str(e)
        }

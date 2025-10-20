"""
Inflation Data Cache Module

Scrapes historical US inflation data from usinflationcalculator.com
and caches it locally to avoid repeated fetches.

The data is stored in a JSON file and refreshed only when needed.
"""

import json
import os
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup


# Cache file location
CACHE_DIR = Path("/app/cache")
CACHE_FILE = CACHE_DIR / "inflation_data.json"

# URL to scrape
INFLATION_URL = "https://www.usinflationcalculator.com/inflation/historical-inflation-rates/"


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def scrape_inflation_data():
    """
    Scrape historical inflation data from usinflationcalculator.com
    
    Returns:
        dict: Dictionary with years as keys and monthly inflation rates
              Example: {
                  "2019": {"Jan": 1.6, "Feb": 1.5, ...},
                  "2020": {"Jan": 2.5, "Feb": 2.3, ...}
              }
    """
    print(f"Fetching inflation data from {INFLATION_URL}...")
    
    try:
        response = requests.get(INFLATION_URL, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the inflation table
        table = soup.find('table')
        if not table:
            print("Error: Could not find inflation table on page")
            return None
        
        inflation_data = {}
        
        # Parse all rows
        all_rows = table.find_all('tr')
        
        if not all_rows:
            print("Error: No rows found in table")
            return None
        
        # First row should be headers
        headers = []
        header_row = all_rows[0]
        for cell in header_row.find_all(['th', 'td']):
            headers.append(cell.text.strip())
        
        # Process data rows (skip header row)
        for row in all_rows[1:]:
            cells = row.find_all(['th', 'td'])
            if len(cells) < 2:
                continue
            
            year = cells[0].text.strip()
            
            # Skip if not a valid year
            try:
                int(year)
            except ValueError:
                continue
            
            inflation_data[year] = {}
            
            # Parse monthly rates
            for i, cell in enumerate(cells[1:], start=1):
                if i < len(headers):
                    month = headers[i]
                    rate_text = cell.text.strip().replace('%', '')
                    
                    try:
                        rate = float(rate_text) if rate_text and rate_text != '-' else None
                        inflation_data[year][month] = rate
                    except ValueError:
                        inflation_data[year][month] = None
        
        print(f"Successfully scraped inflation data for {len(inflation_data)} years")
        return inflation_data
        
    except Exception as e:
        print(f"Error scraping inflation data: {e}")
        return None


def save_to_cache(data):
    """
    Save inflation data to cache file
    
    Args:
        data (dict): Inflation data to cache
    """
    ensure_cache_dir()
    
    cache_content = {
        "last_updated": datetime.now().isoformat(),
        "data": data
    }
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_content, f, indent=2)
    
    print(f"Inflation data cached to {CACHE_FILE}")


def load_from_cache():
    """
    Load inflation data from cache file
    
    Returns:
        tuple: (data dict, last_updated datetime) or (None, None) if cache doesn't exist
    """
    if not CACHE_FILE.exists():
        return None, None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_content = json.load(f)
        
        last_updated = datetime.fromisoformat(cache_content["last_updated"])
        data = cache_content["data"]
        
        print(f"Loaded cached inflation data (last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')})")
        return data, last_updated
        
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None, None


def should_refresh_cache(last_updated):
    """
    Determine if cache should be refreshed
    
    Cache is refreshed if:
    - It's more than 30 days old
    - It's a new year and cache is from last year
    
    Args:
        last_updated (datetime): When cache was last updated
        
    Returns:
        bool: True if cache should be refreshed
    """
    if not last_updated:
        return True
    
    now = datetime.now()
    days_old = (now - last_updated).days
    
    # Refresh if more than 30 days old
    if days_old > 30:
        print(f"Cache is {days_old} days old, refreshing...")
        return True
    
    # Refresh if it's a new year
    if now.year > last_updated.year:
        print(f"New year detected, refreshing cache...")
        return True
    
    return False


def get_inflation_data(force_refresh=False):
    """
    Get inflation data, using cache if available and fresh
    
    Args:
        force_refresh (bool): If True, bypass cache and fetch fresh data
        
    Returns:
        dict: Inflation data or None if unavailable
    """
    # Check cache first
    if not force_refresh:
        cached_data, last_updated = load_from_cache()
        
        if cached_data and not should_refresh_cache(last_updated):
            return cached_data
    
    # Fetch fresh data
    data = scrape_inflation_data()
    
    if data:
        save_to_cache(data)
        return data
    else:
        # If scraping failed, return cached data if available
        cached_data, _ = load_from_cache()
        if cached_data:
            print("Scraping failed, using cached data as fallback")
            return cached_data
        
        return None


def calculate_cumulative_inflation(start_year, end_year, data=None):
    """
    Calculate cumulative inflation between two years
    
    Args:
        start_year (int): Starting year
        end_year (int): Ending year
        data (dict, optional): Inflation data. If None, will fetch/load from cache
        
    Returns:
        float: Cumulative inflation rate as a decimal (e.g., 0.23 for 23%)
    """
    if data is None:
        data = get_inflation_data()
    
    if not data:
        print("No inflation data available, using assumed 3% annual rate")
        years = end_year - start_year
        return ((1 + 0.03) ** years) - 1
    
    cumulative = 1.0
    
    for year in range(start_year, end_year):
        year_str = str(year)
        
        if year_str not in data:
            print(f"No data for {year}, using 3% for that year")
            cumulative *= 1.03
            continue
        
        # Calculate average inflation for the year
        monthly_rates = [rate for rate in data[year_str].values() if rate is not None]
        
        if not monthly_rates:
            print(f"No monthly data for {year}, using 3% for that year")
            cumulative *= 1.03
            continue
        
        avg_rate = sum(monthly_rates) / len(monthly_rates)
        cumulative *= (1 + avg_rate / 100)
    
    return cumulative - 1


def get_inflation_summary(start_year, end_year):
    """
    Get a formatted summary of inflation between two years
    
    Args:
        start_year (int): Starting year
        end_year (int): Ending year
        
    Returns:
        str: Formatted summary with inflation details
    """
    data = get_inflation_data()
    
    if not data:
        return f"Unable to fetch inflation data. Using assumed 3% annual rate."
    
    cumulative_rate = calculate_cumulative_inflation(start_year, end_year, data)
    
    summary = f"Inflation from {start_year} to {end_year}:\n"
    summary += f"Cumulative rate: {cumulative_rate * 100:.2f}%\n"
    summary += f"Source: usinflationcalculator.com (cached)\n"
    
    # Show yearly breakdown
    summary += f"\nYearly breakdown:\n"
    for year in range(start_year, end_year):
        year_str = str(year)
        if year_str in data:
            monthly_rates = [rate for rate in data[year_str].values() if rate is not None]
            if monthly_rates:
                avg_rate = sum(monthly_rates) / len(monthly_rates)
                summary += f"  {year}: {avg_rate:.2f}%\n"
    
    return summary


if __name__ == "__main__":
    # Test the module
    print("Testing Inflation Cache Module")
    print("=" * 50)
    
    # Fetch and cache data
    data = get_inflation_data(force_refresh=True)
    
    if data:
        print(f"\nAvailable years: {min(data.keys())} to {max(data.keys())}")
        
        # Test cumulative inflation calculation
        print("\nExample: Inflation from 2019 to 2026")
        summary = get_inflation_summary(2019, 2026)
        print(summary)
        
        # Calculate what $119.85 becomes
        cumulative = calculate_cumulative_inflation(2019, 2026, data)
        original_price = 119.85
        future_price = original_price * (1 + cumulative)
        print(f"\n${original_price:.2f} in 2019 → ${future_price:.2f} in 2026")
    else:
        print("Failed to fetch inflation data")

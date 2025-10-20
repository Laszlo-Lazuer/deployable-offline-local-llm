import os
import logging
import requests
from requests.exceptions import RequestException
from celery import Celery
from langchain_community.llms import Ollama
from inflation_cache import get_inflation_data, calculate_cumulative_inflation, get_inflation_summary
from data_normalization import (
    generate_normalization_guide, 
    get_file_schema, 
    suggest_column_mappings,
    generate_semantic_column_guide
)
from file_loader import load_file, get_file_type, SUPPORTED_EXTENSIONS

# The PyPI package is named `open-interpreter`, but it installs a top-level
# package called `interpreter`. Support both import names for compatibility.
try:
    # preferred: installed package provides `interpreter`
    from interpreter import interpreter
except ImportError:
    try:
        # older/alternate import name
        from open_interpreter import interpreter
    except ImportError as e:
        raise ImportError(
            "open-interpreter package not found in the image. Install `open-interpreter` "
            "or ensure the package is on PYTHONPATH."
        ) from e

# --- Celery Configuration ---
# The Redis URL tells Celery where the queue is.
# The 'redis' hostname is the name of our service in docker-compose.yml.
REDIS_URL = "redis://redis:6379/0"

# We use Redis as both the broker (the queue) and the backend (to store results).
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# --- The Analysis Task ---
@celery_app.task(bind=True)
def run_analysis_task(self, question, filename):
    """
    This is the core task. It runs in the background on a worker process.
    """
    data_dir = "/app/data"
    file_path = os.path.join(data_dir, filename)
    
    # Get list of all available data files
    available_files = []
    if os.path.exists(data_dir):
        available_files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]

    # Configure Open Interpreter (The Sandbox)
    # The 'ollama' hostname is the name of our Ollama service.
    logger = logging.getLogger(__name__)
    interpreter.llm.model = "ollama/llama3:8b"
    interpreter.auto_run = True
    interpreter.llm.api_base = "http://ollama:11434"
    # If the default 'ollama' hostname isn't resolvable in this container
    # (common when Ollama runs on the mac host), try a small set of fallbacks
    # and pick the first reachable base URL.
    def _find_ollama_base(candidates):
        for base in candidates:
            try:
                resp = requests.get(base.rstrip('/') + "/api/tags", timeout=2)
                if resp.status_code < 500:
                    return base
            except RequestException:
                continue
        return None

    candidates = [
        "http://ollama:11434",
        "http://host.docker.internal:11434",
        "http://127.0.0.1:11434",
    ]
    working = _find_ollama_base(candidates)
    if working:
        interpreter.llm.api_base = working
        logger.debug("Using Ollama API base: %s", working)
    else:
        logger.warning(
            "Ollama not reachable at any candidate host; LLM calls will likely fail. Tried: %s",
            candidates,
        )
    # Some versions of the interpreter expose a `sandbox` attribute while others
    # don't. Create the sandbox directory and try to set it safely; if the
    # attribute is missing, continue without failing the task.
    sandbox_path = "/app/sandbox"
    try:
        os.makedirs(sandbox_path, exist_ok=True)
    except Exception as e:
        logger.debug("failed to create sandbox dir %s: %s", sandbox_path, e)

    # Configure sandbox settings
    # Set safe_mode to 'off' to allow network requests (for fetching inflation data, APIs, etc.)
    # WARNING: This allows LLM-generated code to make external network requests
    interpreter.safe_mode = "off"
    
    # Increase context window to 8K (llama3 supports up to 8K)
    # This prevents prompt truncation warnings
    interpreter.llm.num_ctx = 8192
    interpreter.llm.api_params = {"num_ctx": 8192}  # Also pass to Ollama API
    
    try:
        interpreter.sandbox.path = sandbox_path  # Isolate file changes
    except AttributeError:
        logger.debug("interpreter has no 'sandbox' attribute; attempting fallback")
        # Try a common alternative API if present; otherwise, continue.
        try:
            if hasattr(interpreter, "set_sandbox"):
                interpreter.set_sandbox(sandbox_path)
                logger.debug("set sandbox via interpreter.set_sandbox()")
        except Exception as e:
            logger.debug("fallback sandbox setup failed: %s", e)

    # Formulate the full prompt for the LLM
    files_context = f"\nAvailable data files in {data_dir}:\n"
    for f in available_files:
        file_size = os.path.getsize(os.path.join(data_dir, f))
        files_context += f"  - {f} ({file_size:,} bytes)\n"
    
    # Always generate semantic column guide for the primary file (helps with natural language)
    semantic_context = ""
    try:
        semantic_context = "\n" + generate_semantic_column_guide(file_path) + "\n"
    except Exception as e:
        logger.warning("Failed to generate semantic column guide: %s", e)
    
    # Generate full normalization guide if multiple files exist
    normalization_context = ""
    if len(available_files) > 1:
        try:
            normalization_context = "\n" + generate_normalization_guide(data_dir) + "\n"
        except Exception as e:
            logger.warning("Failed to generate normalization guide: %s", e)
            normalization_context = ""
    
    full_prompt = f"""
    You are a data analyst with access to multiple data files and the internet.
    
    Primary file for this analysis: '{file_path}'
    {files_context}
    {semantic_context}
    
    User question: "{question}"
    {normalization_context}
    
    Instructions:
    1. You can load and work with ANY of the available data files as needed to answer the question
    2. ALWAYS start your code by importing the file loader:
       
       from file_loader import load_file
       
    3. Use the universal file loader to load ANY supported format:
       - Usage: df = load_file('/app/data/filename.ext')
       - Supported: CSV (.csv), JSON (.json), Excel (.xlsx, .xls), TSV (.tsv), Text (.txt)
       - This automatically detects the file type and loads it into a pandas DataFrame
       - Example: df = load_file('/app/data/test-sales.tsv')  # Auto-detects TSV format
    4. If the question requires data from multiple files, load and combine them
    5. Write and execute Python code to answer the question
    6. Show your work and calculations
    7. Provide the final answer
    
    CRITICAL - NATURAL LANGUAGE COLUMN UNDERSTANDING:
    - Users may refer to columns using natural language, NOT exact column names
    - Example: User says "average price" but column is "Avg_Price" or "AVG_PRICE"
    - ALWAYS inspect actual column names first: df.columns.tolist()
    - Map user's natural language to actual columns using the semantic guide above
    - Don't assume exact column names - check what actually exists
    - Example workflow:
      1. User asks: "What's the average price?"
      2. Load data: df = load_file('/app/data/sales.csv')
      3. Check columns: print(df.columns.tolist())
      4. Find match: "Avg_Price" matches user's "average price"
      5. Use actual name: df['Avg_Price'].mean()
    
    CRITICAL - DATA NORMALIZATION (when working with multiple files):
    - Files may have different schemas, column names, and data formats
    - ALWAYS inspect each file's schema FIRST before combining:
      * Print column names: df.columns.tolist()
      * Check data types: df.dtypes
      * View samples: df.head()
    - Normalize data BEFORE analysis:
      * Rename columns to match (use .rename())
      * Standardize values (use .str.strip(), .str.title())
      * Convert data types (use pd.to_datetime(), pd.to_numeric())
      * Align schemas (add missing columns with None)
    - Use the normalization guide above if provided
    - Example workflow:
      1. Load each file individually: df = load_file('/app/data/filename.ext')
      2. Inspect and print schemas
      3. Create normalization mapping
      4. Apply transformations
      5. Verify alignment
      6. Then combine with pd.concat()
    
    IMPORTANT - When fetching data from external APIs:
    - First make the request and print the raw response to understand its structure
    - Inspect the JSON structure before assuming key names
    - Use .keys() or print the response to see what's available
    - Handle errors gracefully - if an API fails, document why and use fallback data if appropriate
    - Try different parsing approaches if the first one fails
    - Many APIs return data in nested structures - explore the response carefully
    
    INFLATION DATA - For US inflation calculations:
    - Use the inflation_cache module which has cached historical US inflation data
    - Available functions:
      * from inflation_cache import get_inflation_data, calculate_cumulative_inflation, get_inflation_summary
      * get_inflation_data() - Returns dict of historical rates by year/month (auto-cached)
      * calculate_cumulative_inflation(start_year, end_year) - Returns cumulative rate as decimal
      * get_inflation_summary(start_year, end_year) - Returns formatted summary string
    - This data is scraped from usinflationcalculator.com and cached locally (refreshes monthly)
    - Example: To adjust $100 from 2019 to 2026:
      cumulative = calculate_cumulative_inflation(2019, 2026)
      future_price = 100 * (1 + cumulative)
    
    Execute the code now.
    """

    # Enable streaming to see progress
    # Store task ID for progress updates
    task_id = self.request.id if self.request else None
    
    # Initialize progress tracking
    if task_id:
        redis_client = celery_app.backend.client
        progress_key = f"task_progress:{task_id}"
        redis_client.setex(progress_key, 3600, "Starting analysis...")  # Expires in 1 hour
    
    # The .chat() method triggers the analysis with streaming enabled
    response_stream = interpreter.chat(full_prompt, stream=True)

    # Collect the full response while sending progress updates
    full_messages = []
    current_content = ""
    
    for chunk in response_stream:
        full_messages.append(chunk)
        
        # Update progress in Redis for real-time monitoring
        if task_id and chunk.get('type') == 'message':
            content = chunk.get('content', '')
            current_content += content
            
            # Send progress update
            if chunk.get('role') == 'assistant':
                # Truncate for progress display (show last 200 chars)
                preview = current_content[-200:] if len(current_content) > 200 else current_content
                redis_client.setex(progress_key, 3600, f"Generating code... {preview}")
            elif chunk.get('format') == 'active_line':
                # Execution progress
                redis_client.setex(progress_key, 3600, f"Executing: {content}")
    
    # Extract the final answer from the response
    final_answer = "Could not determine a final answer."
    if full_messages and len(full_messages) > 0:
        # Get the last message content
        for msg in reversed(full_messages):
            if msg.get('type') == 'message' and msg.get('content'):
                final_answer = msg['content']
                break
    
    # Clear progress tracking
    if task_id:
        redis_client.delete(progress_key)

    return final_answer
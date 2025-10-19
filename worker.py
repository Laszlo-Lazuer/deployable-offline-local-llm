import os
import logging
import requests
from requests.exceptions import RequestException
from celery import Celery
from langchain_community.llms import Ollama

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
@celery_app.task
def run_analysis_task(question, filename):
    """
    This is the core task. It runs in the background on a worker process.
    """
    file_path = os.path.join("/app/data", filename)

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
    full_prompt = f"""
    You are a data analyst. Write Python code to analyze the CSV file located at '{file_path}'.
    
    User question: "{question}"
    
    Instructions:
    1. Load the CSV file using pandas
    2. Write and execute Python code to answer the question
    3. Show your work and calculations
    4. Provide the final answer
    
    Execute the code now.
    """

    # The .chat() method triggers the analysis
    response_stream = interpreter.chat(full_prompt, stream=False)

    # Extract the final answer from the response
    final_answer = "Could not determine a final answer."
    if response_stream and len(response_stream) > 0:
        final_answer = response_stream[-1]['content']

    return final_answer
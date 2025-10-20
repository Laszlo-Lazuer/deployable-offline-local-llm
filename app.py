"""
Local LLM Celery - AI-Powered Data Analysis Service
Flask API for AI-powered data analysis using Celery and Open Interpreter.

Author: Laszlo Lazuer
Email: laszlo@squirrelyeye.com
Copyright (c) 2025 Laszlo Lazuer. All rights reserved.
"""
import warnings

# Suppress noisy pkg_resources deprecation warning coming from a dependency
# (pkg_resources is deprecated by setuptools; this silences that single message).
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html.",
)

import os
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from werkzeug.utils import secure_filename
from worker import run_analysis_task
from celery.result import AsyncResult
import redis
import time
import json

app = Flask(__name__)

# Configuration
DATA_DIR = os.environ.get('DATA_DIR', '/app/data')
ALLOWED_EXTENSIONS = {'csv', 'json', 'txt', 'xlsx', 'tsv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Redis client for progress tracking
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
redis_client = redis.from_url(REDIS_URL)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(filename):
    """Get file metadata."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return None
    
    stats = os.stat(filepath)
    return {
        'filename': filename,
        'size_bytes': stats.st_size,
        'size_human': format_bytes(stats.st_size),
        'modified': stats.st_mtime,
        'created': stats.st_ctime
    }

def format_bytes(bytes_num):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.2f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.2f} TB"

@app.route('/')
def index():
    """Serve the web UI"""
    return send_file('static/index.html')

@app.route('/analyze', methods=['POST'])
def start_analysis():
    """
    This endpoint kicks off an analysis task.
    It takes a JSON payload with a 'question' and optionally a 'filename'.
    If filename is not provided, the LLM will work with all available files.
    """
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "Please provide a 'question'"}), 400

    question = data['question']
    # Make filename optional - if not provided, use a default or let LLM choose
    filename = data.get('filename', '')
    
    # If no filename provided, check if any files exist and use the first one as primary
    # (LLM will still have access to all files)
    if not filename:
        if os.path.exists(DATA_DIR):
            files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
            if files:
                filename = files[0]
            else:
                return jsonify({"error": "No data files available. Please upload a file first."}), 400
        else:
            return jsonify({"error": "Data directory not found."}), 500

    # This is the key part: instead of running the task here,
    # we add it to the queue using .delay().
    task = run_analysis_task.delay(question, filename)

    # Return the task ID so the client can check the status later.
    return jsonify({"task_id": task.id}), 202

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """
    This endpoint checks the status of a previously submitted task.
    """
    task_result = AsyncResult(task_id, app=run_analysis_task.app)

    response = {
        "task_id": task_id,
        "status": task_result.state
    }

    if task_result.successful():
        response['result'] = task_result.get()
    elif task_result.failed():
        response['error'] = str(task_result.info) # Get traceback

    return jsonify(response)

@app.route('/status/<task_id>/stream', methods=['GET'])
def stream_progress(task_id):
    """
    Server-Sent Events endpoint to stream real-time progress updates.
    Usage: Connect with EventSource in JavaScript or curl with text/event-stream
    
    Example:
        curl -N http://localhost:5001/status/{task_id}/stream
    """
    def generate():
        """Generator function that yields SSE-formatted progress updates."""
        task_result = AsyncResult(task_id, app=run_analysis_task.app)
        progress_key = f"task_progress:{task_id}"
        last_message = None
        
        while True:
            # Check task status
            state = task_result.state
            
            # Get progress message from Redis
            progress_msg = redis_client.get(progress_key)
            if progress_msg:
                progress_msg = progress_msg.decode('utf-8')
                
                # Only send if message changed
                if progress_msg != last_message:
                    last_message = progress_msg
                    data = {
                        "status": state,
                        "progress": progress_msg,
                        "timestamp": time.time()
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            
            # Check if task completed
            if state in ['SUCCESS', 'FAILURE']:
                final_data = {
                    "status": state,
                    "progress": "Complete" if state == 'SUCCESS' else "Failed",
                    "timestamp": time.time()
                }
                
                if state == 'SUCCESS':
                    final_data['result'] = task_result.get()
                elif state == 'FAILURE':
                    final_data['error'] = str(task_result.info)
                
                yield f"data: {json.dumps(final_data)}\n\n"
                break
            
            # Wait before checking again
            time.sleep(0.5)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/status/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Kubernetes liveness/readiness probes.
    """
    return jsonify({"status": "healthy"}), 200

# ============================================
# Data Management Endpoints
# ============================================

@app.route('/data', methods=['GET'])
def list_data_files():
    """
    List all data files in the data directory.
    """
    try:
        if not os.path.exists(DATA_DIR):
            return jsonify({"files": [], "count": 0}), 200
        
        files = []
        for filename in os.listdir(DATA_DIR):
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.isfile(filepath):
                info = get_file_info(filename)
                if info:
                    files.append(info)
        
        return jsonify({
            "files": files,
            "count": len(files),
            "data_dir": DATA_DIR
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<filename>', methods=['GET'])
def get_data_file(filename):
    """
    Download a specific data file.
    """
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(DATA_DIR, safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({"error": f"File '{filename}' not found"}), 404
        
        return send_file(filepath, as_attachment=True, download_name=safe_filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<filename>/info', methods=['GET'])
def get_data_file_info(filename):
    """
    Get metadata about a specific data file.
    """
    try:
        safe_filename = secure_filename(filename)
        info = get_file_info(safe_filename)
        
        if not info:
            return jsonify({"error": f"File '{filename}' not found"}), 404
        
        return jsonify(info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data', methods=['POST'])
def upload_data_file():
    """
    Upload a new data file.
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Secure the filename
        safe_filename = secure_filename(file.filename)
        filepath = os.path.join(DATA_DIR, safe_filename)
        
        # Check if file already exists
        overwrite = request.form.get('overwrite', 'false').lower() == 'true'
        if os.path.exists(filepath) and not overwrite:
            return jsonify({
                "error": f"File '{safe_filename}' already exists. Use overwrite=true to replace it."
            }), 409
        
        # Create data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Save the file
        file.save(filepath)
        
        info = get_file_info(safe_filename)
        return jsonify({
            "message": "File uploaded successfully",
            "file": info
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<filename>', methods=['PUT'])
def update_data_file(filename):
    """
    Update/replace an existing data file.
    """
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(DATA_DIR, safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({"error": f"File '{filename}' not found"}), 404
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Save the file (overwrites existing)
        file.save(filepath)
        
        info = get_file_info(safe_filename)
        return jsonify({
            "message": "File updated successfully",
            "file": info
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<filename>', methods=['DELETE'])
def delete_data_file(filename):
    """
    Delete a data file.
    """
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(DATA_DIR, safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({"error": f"File '{filename}' not found"}), 404
        
        os.remove(filepath)
        
        return jsonify({
            "message": f"File '{safe_filename}' deleted successfully"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Bind to 0.0.0.0 so the app is reachable from the host when run inside a container
    app.run(host="0.0.0.0", port=5000)
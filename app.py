import warnings

# Suppress noisy pkg_resources deprecation warning coming from a dependency
# (pkg_resources is deprecated by setuptools; this silences that single message).
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html.",
)

from flask import Flask, request, jsonify
from worker import run_analysis_task
from celery.result import AsyncResult

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def start_analysis():
    """
    This endpoint kicks off an analysis task.
    It takes a JSON payload with a 'question' and 'filename'.
    """
    data = request.get_json()
    if not data or 'question' not in data or 'filename' not in data:
        return jsonify({"error": "Please provide a 'question' and 'filename'"}), 400

    question = data['question']
    filename = data['filename']

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


if __name__ == "__main__":
    # Bind to 0.0.0.0 so the app is reachable from the host when run inside a container
    app.run(host="0.0.0.0", port=5000)
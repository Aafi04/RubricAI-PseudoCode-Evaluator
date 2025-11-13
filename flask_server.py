"""
Simple Flask web server with one POST /evaluate endpoint.

This script expects a JSON body with a single key "pseudocode" and
returns it back in the response to confirm receipt.

Run directly with:
    python flask_server.py

Or install dependencies and run:
    pip install -r requirements.txt
    python flask_server.py

The server listens on 0.0.0.0:5000 by default.
"""

from flask import Flask, request, jsonify
import os
import json
import datetime
import logging
import google.generativeai as genai
from flask import send_from_directory

# Create the Flask application
app = Flask(__name__)

# Configure logging to file before routes are registered
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'rubricai.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

# Configure the Gemini API key if available. Warn if not set so errors are clearer.
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("Warning: GOOGLE_API_KEY not set. GenAI calls will fail until configured.")

# The master prompt for evaluating student pseudocode submissions.
# This prompt is intentionally verbose and will be used as a template
# where the student's pseudocode will be inserted for automated evaluation.
master_prompt = """
You are RubricAI, a helpful and fair Computer Science TA. Your task is to evaluate a student's pseudocode against the provided rubric. You MUST respond with only a valid JSON object. Do not include any text or markdown formatting before or after the JSON.

Your JSON output must strictly follow this structure:
{{
    "logic_score": <int>,
    "logic_feedback": "<string>",
    "readability_score": <int>,
    "readability_feedback": "<string>",
    "total_score": <int>,
    "final_summary": "<string>"
}}

---
THE RUBRIC (All scores out of 5):
1.  **Logic (Score: /5):** Is the core logic correct? Does it solve the problem? (5=Perfect, 3=Mostly correct, 1=Major flaws)
2.  **Readability (Score: /5):** Is the pseudocode easy to read? Are variable names clear? (5=Very clear, 3=Okay, 1=Confusing)
---

Here are two examples of how to evaluate:

EXAMPLE 1 (Good Submission):
---
Student Pseudocode:
FUNCTION factorial(n):
        IF n == 0:
                RETURN 1
        ELSE:
                RETURN n * factorial(n - 1)
---
Your JSON Evaluation:
{{
    "logic_score": 5,
    "logic_feedback": "The recursive logic for the factorial is perfectly correct.",
    "readability_score": 5,
    "readability_feedback": "Excellent use of indentation and clear function/variable naming.",
    "total_score": 10,
    "final_summary": "Excellent work. The logic is sound and the code is very readable."
}}

EXAMPLE 2 (Poor Submission):
---
Student Pseudocode:
function do_math(num):
        total = num
        FOR i FROM 1 TO num:
                total = total * i
        RETURN total
---
Your JSON Evaluation:
{{
    "logic_score": 1,
    "logic_feedback": "The logic is incorrect. For factorial(5), this calculates 5*1*2*3*4*5. The initial 'total' should be 1.",
    "readability_score": 2,
    "readability_feedback": "The function name 'do_math' is too vague. 'total' should be initialized to 1, not 'num'.",
    "total_score": 3,
    "final_summary": "The submission has a major logical flaw and needs a more descriptive function name. Please review and resubmit."
}}

---
END OF EXAMPLES
---

Now, evaluate the following student submission. Remember to only output the JSON.

Student Pseudocode:
{student_pseudocode}
"""


def save_to_jsonl(pseudocode, evaluation, model_used):
    """Append an evaluation record to evaluations.jsonl as a single JSON line.

    The function swallows any exception and only prints an error message so it
    doesn't interfere with the main request flow.
    """
    record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "model": model_used,
        "pseudocode": pseudocode,
        "evaluation": evaluation,
    }
    try:
        path = os.path.join(os.path.dirname(__file__), 'evaluations.jsonl')
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + '\n')
        # Log success to the configured app logger
        try:
            app.logger.info("Successfully saved evaluation.")
        except Exception:
            # If app isn't available for some reason, fall back to root logger
            logging.getLogger().info("Successfully saved evaluation.")
    except Exception as e:
        # Log error but do not raise; persistence is best-effort for MVP
        try:
            app.logger.error(f"Failed to save evaluation to {path}: {e}")
        except Exception:
            logging.getLogger().error(f"Failed to save evaluation to {path}: {e}")


@app.route('/evaluate', methods=['POST'])
def evaluate():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    try:
        # Follow the new contract: read the pseudocode directly from the payload
        student_code = data['pseudocode']
    except Exception:
        return jsonify({"error": "Missing or invalid 'pseudocode' field"}), 400

    if not student_code or not isinstance(student_code, str):
        return jsonify({"error": "Missing or invalid 'pseudocode' field"}), 400

    # Log pseudocode receipt (length only for privacy)
    try:
        app.logger.info("Received pseudocode of length %d", len(student_code))
    except Exception:
        # If logger is not available for some reason, write to root logger
        logging.getLogger().info("Received pseudocode (length unknown)")

    try:
        # 1. Prepare the full prompt by formatting the master prompt with the student's code
        prompt_for_ai = master_prompt.format(student_pseudocode=student_code)

        # 2. Select the fully-qualified model and generate content
        # Default to a model we confirmed exists in the account: 'models/gemini-flash-latest'
        # Allow overriding with the environment variable GENAI_MODEL if needed.
        model_id = os.environ.get('GENAI_MODEL', 'models/gemini-flash-latest')
        print(f"Using Generative model: {model_id}")
        model = genai.GenerativeModel(model_id)

        # 3. Ensure the model only outputs JSON
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )

        # 4. Call the API with the formatted prompt
        response = model.generate_content(prompt_for_ai, generation_config=generation_config)

        # 5. Parse the response as JSON
        evaluation_json = json.loads(response.text)

        # Persist the evaluation (best-effort)
        try:
            save_to_jsonl(student_code, evaluation_json, model_id)
        except Exception:
            # save_to_jsonl itself should swallow exceptions, but be defensive
            pass

        # Return the parsed JSON to the caller
        return jsonify(evaluation_json), 200

    except json.JSONDecodeError:
        # This happens if the model's response is not valid JSON
        try:
            raw = response.text
        except Exception:
            raw = None
        # Log the parse failure
        try:
            app.logger.error("Failed to parse AI JSON response; raw response length=%s", len(raw) if raw is not None else 'None')
        except Exception:
            logging.getLogger().error("Failed to parse AI JSON response; raw response length=%s", len(raw) if raw is not None else 'None')
        return (
            jsonify({"error": "AI response was not valid JSON", "ai_raw_response": raw}),
            502,
        )
    except Exception as e:
        # For any other errors (e.g., API issues)
        # Log exception with stack trace
        try:
            app.logger.exception("An unexpected error occurred while evaluating pseudocode")
        except Exception:
            logging.getLogger().exception("An unexpected error occurred while evaluating pseudocode: %s", e)
        return jsonify({"error": "An internal server error occurred"}), 500


@app.route('/history', methods=['GET'])
def get_history():
    """Reads the JSONL file and returns a list of all evaluations."""
    history = []
    path = os.path.join(os.path.dirname(__file__), 'evaluations.jsonl')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    history.append(json.loads(line))
                except json.JSONDecodeError:
                    app.logger.warning(f"Skipping corrupted line in JSONL: {line}")
    except FileNotFoundError:
        app.logger.info("evaluations.jsonl not found, returning empty history.")
        return jsonify([])
    except Exception as e:
        app.logger.error(f"Error reading history file: {e}")
        return jsonify({"error": "Could not read history"}), 500

    history.reverse()  # Show newest first
    return jsonify(history)


@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Deletes the evaluations.jsonl file."""
    # If an ADMIN_TOKEN is set, require the same token in the X-Admin-Token header
    admin_token = os.environ.get('ADMIN_TOKEN')
    if admin_token:
        # Accept either header 'X-Admin-Token' or Authorization: Bearer <token>
        header_token = request.headers.get('X-Admin-Token')
        if not header_token:
            auth = request.headers.get('Authorization', '')
            if auth.startswith('Bearer '):
                header_token = auth.split(' ', 1)[1].strip()
        if header_token != admin_token:
            app.logger.warning('Unauthorized attempt to clear history')
            return jsonify({"error": "Unauthorized"}), 401

    file_path = os.path.join(os.path.dirname(__file__), 'evaluations.jsonl')
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            app.logger.info("History file cleared successfully.")
            return jsonify({"message": "History cleared"}), 200
        else:
            app.logger.info("History file not found, nothing to clear.")
            return jsonify({"message": "History already clear"}), 200
    except Exception as e:
        app.logger.error(f"Error clearing history file: {e}")
        return jsonify({"error": "Could not clear history"}), 500


@app.route('/')
def serve_index():
    """Serve the index.html file from the project directory so the UI is available at '/'."""
    # Assumes index.html is located in the same directory as this script
    return send_from_directory(os.path.dirname(__file__), 'index.html')


if __name__ == '__main__':
    # Run the Flask development server. Do not use this in production.
    app.run(host='0.0.0.0', port=5000, debug=True)

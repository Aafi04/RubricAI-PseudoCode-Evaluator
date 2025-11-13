# RubricAI PseudoCode Evaluator

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75FF?logo=google&logoColor=white)

A lightweight toolkit made using Python, Flask and Gemini to automatically score student pseudocode against structured instructor rubrics — focused on interpretability, flexibility, and easy integration.

![Image 1](images/image1.png)
![Image 2](images/image2.png)
![Image 3](images/image3.png)

---

## Table of contents

- [Project status](#project-status)
- [Features](#features)
- [How it works (high-level)](#how-it-works-high-level)
- [Quickstart](#quickstart)
  - [Installation](#installation)
  - [CLI examples](#cli-examples)
  - [Python API examples](#python-api-examples)
- [Rubric format](#rubric-format)
- [Scoring heuristics & examples](#scoring-heuristics--examples)
- [Configuration & extending matchers](#configuration--extending-matchers)
- [Running tests](#running-tests)
- [Contributing](#contributing)
- [License](#license)

---

## Project status

Stable for core rule-based evaluation. Actively developed for structural matching and richer rubric syntaxes. Includes unit tests and example rubrics/submissions in `examples/`.

## Features

- Structured rubrics (JSON/YAML) with weights, required items, and tolerant matching.
- Multiple matchers: keyword, phrase, structure, regex, and extensible semantic matchers.
- Structural/heuristic partial credit and detailed per-item evidence.
- CLI for batch scoring and a Python API for embedding in pipelines or notebooks.

## How it works (high-level)

1. Load rubric (JSON/YAML) that defines items, points, and matchers.
2. Normalize the submission (tokenize, normalize identifiers, remove noise).
3. For each rubric item: run matcher → produce match boolean, confidence (0..1), and evidence snippets.
4. Aggregate item scores using weighting/partial-credit rules.
5. Emit itemized report (JSON/CSV/HTML) with evidence and feedback templates.

---

## Quickstart

### Requirements

- Python 3.8+
- Works on Linux, macOS, Windows

### Installation (local)

```bash
# create & activate venv
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### CLI examples

Run batch evaluation:

```bash
python -m rubricai_evaluator.cli evaluate \
  --rubric examples/rubrics/sample_rubric.json \
  --submissions examples/submissions/ \
  --output reports/report.csv \
  --format csv --verbose
```

Single-file example:

```bash
python -m rubricai_evaluator.cli evaluate \
  --rubric examples/rubrics/sample_rubric.json \
  --submissions examples/submissions/student_001.txt \
  --output reports/student_001_report.json \
  --format json --verbose
```

### Python API examples

```python
# from rubricai_evaluator import Evaluator
# ev = Evaluator(rubric_path="examples/rubrics/sample_rubric.json")
# report = ev.evaluate_text(student_text)
# print(report.summary())
```

---

## Rubric format

Each rubric item supports:

- id (string)
- name (string)
- description (string)
- max_points (number)
- required (bool, optional)
- matcher (type + config)
- partial_credit (optional rules)

Matcher types: keyword, phrase, structure, regex, semantic (extensible).

---

## Scoring heuristics & examples

- Binary matches: full points when confident.
- Partial matches: points = max_points \* confidence (0..1).
- Required items: configurable penalties or zeroing behavior.
- Aggregation: default is summed then optionally normalized.

### Sample pseudocode examples

Perfect submission (should score highly):

```text
FUNCTION find_max(numbers):
  IF numbers IS EMPTY:
    RETURN NULL

  max_val = numbers[0]
  FOR i FROM 1 TO length(numbers) - 1:
    IF numbers[i] > max_val:
      max_val = numbers[i]
  RETURN max_val
```

---

## Google API key — how to create one (do NOT paste the key into the repo)

You must create an API key for the Google Generative AI service (Gemini). These are the high-level steps — UI labels may vary slightly as Google updates the console.

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Select or create a Google Cloud project (top-left project selector).
3. Enable billing for the project (required for Generative AI usage).
4. Enable the Generative AI API or "Generative Models API" for the project:
   - Navigate to `APIs & Services` → `Library` and search for "Generative" or "Generative AI" and enable the appropriate API for your project.
5. Create credentials (API key):
   - `APIs & Services` → `Credentials` → `+ CREATE CREDENTIALS` → `API key`.
   - Copy the created key — treat it like a secret.
6. Optionally restrict the API key (recommended): limit by HTTP referrer, IP, or restrict to the Generative API.

Important: do not commit the API key to your repository. Instead, set it as an environment variable locally and as a repository secret in GitHub Actions (see below).

---

## Configuration / environment variables

The main env vars used by the app are:

- `GOOGLE_API_KEY` — your Google API key (required to call the Generative API)
- `GENAI_MODEL` — optional override of the model id (defaults to a preconfigured Gemini model in the code)
- `ADMIN_TOKEN` — optional admin token used to protect the `POST /clear_history` endpoint

Set them in PowerShell (temporary for the session):

```powershell
$env:GOOGLE_API_KEY = "YOUR_API_KEY_HERE"
$env:GENAI_MODEL = "models/gemini-ultra-1"  # optional
$env:ADMIN_TOKEN = "a-secret-token"        # optional
```

Or on macOS / Linux:

```bash
export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
export GENAI_MODEL="models/gemini-ultra-1"  # optional
export ADMIN_TOKEN="a-secret-token"        # optional
```

Replace `models/gemini-ultra-1` with the model id you want to use (or leave unset to use the default in `flask_server.py`).

---

## Running locally

Start the Flask development server (this project serves `index.html` and provides the API endpoints):

```powershell
# With venv active and env vars set (see above)
python flask_server.py

# By default, server listens on http://127.0.0.1:5000
```

Open `http://127.0.0.1:5000` in your browser to access the UI. Use the textarea to paste pseudocode and click Evaluate. The UI also exposes a History view and a Clear History action (Clear History requires `ADMIN_TOKEN` if set).

API endpoints (examples):

- `POST /evaluate` — JSON { "pseudocode": "..." } → evaluation JSON (from the model)
- `GET /history` — returns saved evaluations (newest-first)
- `POST /clear_history` — clears saved history (requires `ADMIN_TOKEN` header if configured)

Example curl (Linux/macOS):

```bash
curl -X POST http://127.0.0.1:5000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"pseudocode":"FUNCTION foo():\n  RETURN 1"}'
```

Example PowerShell:

```powershell
$body = @{ pseudocode = "FUNCTION foo():\n  RETURN 1" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:5000/evaluate -Method Post -Body $body -ContentType 'application/json'
```

---

## Running tests

Run tests locally with pytest (ensure you have the virtualenv active):

```bash
pip install -r requirements.txt
pytest -q
```

Notes:

- Tests are written to mock external calls where appropriate. If any tests call external APIs, you will need to provide `GOOGLE_API_KEY` or set up mocks.

---

## CI / GitHub Actions

This repository includes a basic GitHub Actions workflow at `.github/workflows/ci.yml` that:

- sets up Python 3.10
- installs `requirements.txt`
- ensures `pytest` is installed
- runs `python -m pytest -q`

If you enable Actions for the repo, add the following repository secrets (Settings → Secrets → Actions):

- `GOOGLE_API_KEY` — your API key (value from Google Cloud)
- `ADMIN_TOKEN` — (optional) the admin token if you want the workflow or other automation to use it

Do NOT store secrets in the repository files.

If you prefer not to run CI on every push, edit the workflow triggers (`on:`) to `pull_request` or `workflow_dispatch` (manual runs only).

---

## Security notes

- Never commit API keys or other secrets to git. Use environment variables and CI secrets.
- Consider restricting the API key in Google Cloud to your project's needs (HTTP referrers, IPs, and API restrictions).
- Rotate keys if you suspect leakage.

---

## Contributing

Fork → branch → implement → tests → PR. Add tests for new features and keep changes focused.

---

## Contact

Repo: https://github.com/Aafi04/RubricAI-PseudoCode-Evaluator

Open an issue for bugs, features, or integration help.

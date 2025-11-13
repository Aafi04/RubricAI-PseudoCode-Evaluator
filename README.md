# Simple Flask Evaluate API

# RubricAI — Pseudocode evaluation (Flask + Gemini)

This small project provides a Flask server and a tiny web UI that evaluates
student pseudocode using an LLM (Google Gemini via the google-generativeai
SDK). It was built as a minimal demo and includes persistence of evaluation
results to `evaluations.jsonl` as well as a simple history viewer.

Features

- Serve a web UI at `/` (single-page app in `index.html`).
- POST `/evaluate` — send pseudocode to the model and return a structured JSON evaluation.
- GET `/history` — read and return all saved evaluations (newest-first).
- POST `/clear_history` — delete the saved history file (admin action).

Requirements

- Python 3.8+ (or newer)
- Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Environment

- Set your Google API key in the environment: `GOOGLE_API_KEY`.
  The server will call the Google Generative AI SDK with this key.
- Optionally set `GENAI_MODEL` to override the default model id (e.g.
  `models/gemini-2.5-flash`). If not set, a default model is used.

Run (development)

```powershell
python flask_server.py
# Then open http://localhost:5000 in a browser
```

Files of interest

- `flask_server.py` — main Flask app (API + static file serving). Contains:
  - `master_prompt` — the prompt template used to evaluate submissions.
  - `/evaluate` — POST endpoint that sends the prompt to the model and
    expects JSON in return.
  - `/history` and `/clear_history` for managing persisted evaluations.
- `index.html` — single-page UI to submit pseudocode and view results/history.
- `evaluations.jsonl` — newline-delimited JSON records of saved evaluations.
- `requirements.txt` — Python dependencies (Flask and google-generativeai).

Persistence and logs

- Evaluations are appended to `evaluations.jsonl` in the project directory.
- App logging is written to `rubricai.log`.

Cleaning cache files

- It's safe to delete Python cache folders such as `__pycache__` and `.pytest_cache` —
  they are regenerated automatically. This repository's tooling may create them when
  running tests or importing modules locally.

Tests

- A small pytest-based test suite is provided in `test_server.py`.

```powershell
python -m pytest -q
```

Preparing for GitHub

- Recommended `.gitignore` entries (these are created in the project):
  - `__pycache__/`
  - `.pytest_cache/`
  - `evaluations.jsonl`
  - `rubricai.log`
  - `.env` (if you store secrets locally)

To initialize a git repo and push to GitHub (example PowerShell):

```powershell
git init
git add .
git commit -m "Initial RubricAI demo"
# create remote repo on GitHub then:
git remote add origin https://github.com/<your-account>/<repo>.git
git branch -M main
git push -u origin main
```

Security and production notes

- Do not store `GOOGLE_API_KEY` in the repo. Use environment variables or a secret
  manager in production.
- This Flask server is for development. Use a WSGI server (gunicorn/uvicorn) or
  containerize for production, and add authentication/authorization for the
  `/clear_history` endpoint.

Admin token for sensitive endpoints

- You can protect the `POST /clear_history` endpoint with a simple token. Set an
  `ADMIN_TOKEN` environment variable locally or in your deployment environment. When
  `ADMIN_TOKEN` is present, the endpoint will require the same token be sent in a
  request header `X-Admin-Token: <token>` or `Authorization: Bearer <token>`.

Example (PowerShell):

```powershell
$headers = @{ 'X-Admin-Token' = $env:ADMIN_TOKEN }
Invoke-RestMethod -Method Post -Uri http://localhost:5000/clear_history -Headers $headers
```

---

---

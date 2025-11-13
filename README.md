# RubricAI PseudoCode Evaluator

Aafi04 / RubricAI-PseudoCode-Evaluator

---

RubricAI PseudoCode Evaluator is a lightweight evaluation toolkit for automatically scoring student-submitted pseudocode (or algorithm descriptions) against instructor rubrics. It is designed to be flexible, interpretable, and easy to integrate into grading pipelines, autograders, or educational tools. The evaluator supports rule-based rubric checks, structure-aware matching, partial-credit allocation, and clear commentable outputs that help instructors and students understand where points were gained or lost.

Key goals:

- Produce consistent, explainable scores for pseudocode submissions.
- Support rubrics expressed as structured JSON/YAML.
- Allow custom matchers and weighting rules.
- Provide both CLI and Python API for batch or interactive usage.

Table of contents

- Project status
- Features
- How it works (high-level)
- Quickstart
- Installation
- Usage
  - CLI examples
  - Python API examples
- Rubric format
- Scoring heuristics & examples
- Configuration & extending matchers
- Running tests
- Integrations & deployment suggestions
- Contributing
- License
- Contact & support
- Roadmap

Project status

- Stable for core rule-based rubric evaluation.
- Actively developed for improved structural matching and richer rubric syntaxes.
- Includes unit tests and example rubrics/submissions (see examples/ directory).

Features

- Structured rubric format (JSON/YAML) with point weights, required/optional items, and tolerant matching rules.
- Multiple matching strategies:
  - Keyword and phrase matching (with synonyms).
  - Structural matching (control flow recognition: loops, conditionals, recursion).
  - Heuristic partial credit for partially-correct steps.
- Detailed evaluation report per student containing:
  - Score breakdown per rubric item
  - Matched evidence from submission
  - Comments & suggestion templates
- CLI for batch scoring and CSV report generation.
- Python API for embedding the evaluator in notebooks, autograders, or web services.
- Extensible matchers: add domain-specific patterns or ML-powered matchers.

How it works (high-level)

1. Load rubric (JSON/YAML) which defines items, points, matchers, and weights.
2. Normalize the student's pseudocode (tokenize, normalize identifiers, reduce whitespace).
3. For each rubric item, apply the configured matchers to the submission and compute:
   - A boolean matched/unmatched indicator
   - A match confidence/score (for partial credit)
   - Evidence snippets showing matched lines
4. Apply weighting/aggregation rules to compute the final numeric score and produce an itemized report.
5. Optional: produce instructor notes and feedback templates derived from rubric entries.

Quickstart (example)

1. Install dependencies
2. Run the evaluator on a sample submission and rubric to see a detailed scoring report.

Installation

Requirements

- Python 3.8+ recommended
- Works on Linux, macOS, Windows (via WSL or natively)

Local installation (pip + virtualenv)

1. Clone the repository:
   git clone https://github.com/Aafi04/RubricAI-PseudoCode-Evaluator.git
   cd RubricAI-PseudoCode-Evaluator

2. Create a virtual environment and activate it:
   python -m venv .venv
   source .venv/bin/activate # Linux / macOS
   .venv\Scripts\activate # Windows (PowerShell / cmd)

3. Install dependencies:
   pip install -r requirements.txt

If there is no requirements.txt in your clone, install commonly used libs:
pip install pyyaml tqdm regex

Usage

CLI (recommended for batch grading)
Basic command (example):
python -m rubricai_evaluator.cli evaluate \
 --rubric examples/rubrics/sample_rubric.json \
 --submissions examples/submissions/ \
 --output reports/report.csv

Parameters:

- --rubric : Path to the rubric file (JSON or YAML).
- --submissions : Path to a single submission file or a directory of submissions. Supports .txt, .md, .py for pseudocode files.
- --output : CSV or JSON report path (if omitted prints to STDOUT).
- --format : Report format (csv|json|html)
- --verbose : Print detailed evaluation to console

Example (single file):
python -m rubricai_evaluator.cli evaluate \
 --rubric examples/rubrics/sample_rubric.json \
 --submissions examples/submissions/student_001.txt \
 --output reports/student_001_report.json \
 --format json \
 --verbose

# Sample Pseudocodes

1. The "Perfect" Submission
   This one should get 10/10. The logic is correct, it handles the main edge case (empty array), and it's very easy to read.

```FUNCTION find_max(numbers):
IF numbers IS EMPTY:
RETURN NULL

    max_val = numbers[0]

    FOR i FROM 1 TO length(numbers) - 1:
        IF numbers[i] > max_val:
            max_val = numbers[i]

    RETURN max_val
```

2. Good Logic, Poor Readability
   This should get a high Logic score (4-5/5) but a low Readability score (1-2/5). The algorithm is correct, but the variable and function names are meaningless.

FUNCTION doit(x):
IF length(x) == 0:
RETURN 0

    v = x[0]
    FOR i FROM 1 TO length(x) - 1:
        IF x[i] > v:
            v = x[i]
    RETURN v

3. Good Readability, Bad Logic
   This is the opposite. It should get a high Readability score (4-5/5) but a low Logic score (1-2/5). The code looks clean, but the algorithm is fundamentally wrong (it skips the last element and starts total at 1).

FUNCTION calculate_sum(array_of_numbers):
total = 1 // BUG: Should be 0

    // BUG: Skips the last element
    FOR i FROM 0 TO length(array_of_numbers) - 2:
        total = total + array_of_numbers[i]

    RETURN total

4. The "Just Plain Wrong" Submission
   This should get a very low score (1-3/10) across the board. The variable names are confusing, and the logic for reversing a string is broken (it just builds the string in the original order).

FUNCTION reverse_it(string_one):
string_two = ""

    FOR i FROM 0 TO length(string_one) - 1:
        string_two = string_two + string_one[i]

    RETURN string_two

Important rubric fields explained

- id: Unique string identifier for the item.
- name: Short title shown in reports.
- description: Guidance for graders / feedback templates.
- max_points: Points available for the item.
- required: (optional) if true, missing this item can trigger a penalty or zeroing.
- matcher: Defines how to detect the item in submission. Supported matcher types:
  - keyword: simple substring or token matching.
  - phrase: detects exact or normalized phrase.
  - structure: attempts to detect algorithmic constructs (loops, recursion, conditionals).
  - regex: use a regular expression for more advanced matching.
- partial_credit: Optional rules to award part of the points when a full match is not found.

Scoring heuristics & examples

- Binary matches: If matcher returns a confident match, award full points for that item.
- Partial matches: Use matcher-specific confidence score (0..1) to multiply max_points.
- Required items: If a required item is missing, the rubric can:
  - Subtract a fixed penalty.
  - Zero the entire submission (configurable).
- Aggregation: By default scores are summed and optionally normalized to the rubric's max_score.

Typical use cases and examples

- Autograders: Integrate evaluator into course grading pipelines to pre-score pseudocode answers and surface likely incorrect areas to human graders.
- Feedback generation: Use the item descriptions and match evidence to generate targeted feedback messages.
- Plagiarism-robust evaluation: Because matches can be structural and phrase-tolerant, the system focuses on correctness patterns instead of exact wording.

Configuration & extending matchers

- Custom matchers: Implement a new matcher by following the matcher interface in rubricai_evaluator/matchers/\*.py. A matcher must implement:
  - match(submission_text, matcher_config) -> MatchResult
- Adding synonyms: Place a synonyms file or JSON mapping inside config/ or pass synonyms directly in rubric matcher config.
- ML-based matchers: If you have a semantic model (e.g., embeddings or classifier), you can create a matcher wrapping your model and reference it via matcher.type="semantic". The repository includes scaffolding and examples in examples/matchers/.

Diagnostics & logs

- Use --verbose in CLI for per-item logs.
- Enable debug logging with RUBRICAI_LOG=debug environment variable.
- The evaluator emits evidence snippets (text fragments with matched indices) in JSON reports to make debugging easy.

Output formats

- JSON: Detailed structure with items, evidence, comments, and scores.
- CSV: Flat report suitable for spreadsheets (one row per submission).
- HTML: Human-readable report with syntax-highlighted pseudocode and inline annotations (optional).

Running tests
If the repository includes a tests/ directory, run tests with:
pytest -q

If you don't have pytest installed:
pip install pytest

Continuous integration

- We recommend setting up GitHub Actions to run tests and linting on push/PR. Example workflows can be added to .github/workflows/.

Integrations & deployment suggestions

- LMS / Autograder: Wrap the CLI or API in a simple HTTP service (FastAPI / Flask) to accept submissions and return JSON results.
- Jupyter Notebooks: Use the Python API directly for interactive grading during office hours or automated feedback notebooks.
- Batch grading: Use the CLI to score a folder of submissions and combine the outputs with student metadata to upload grades to an LMS.

Contributing
Contributions are welcome. Suggested workflow:

1. Fork the repo and create a feature branch.
2. Add unit tests for new behavior or bug fixes.
3. Open a pull request describing the changes and include examples if relevant.

Preferred contribution areas:

- New matcher implementations (structure, semantic).
- Improved normalization and tokenization for pseudocode.
- Additional example rubrics and student submissions.
- UI or integrations (notebook widgets, web UI).
- Performance optimizations for large batch grading.

Please follow repository coding style and include tests where applicable.

License
Include the project's license file (e.g., MIT, Apache-2.0) in LICENSE. If no license is present, treat the repository as proprietary until an explicit license is added. We recommend MIT for educational projects:

- MIT License (recommended): simple and permissive.

Contact & support

- Repo: https://github.com/Aafi04/RubricAI-PseudoCode-Evaluator
- Open an issue for bugs, feature requests, or help.
- If you'd like help integrating into a specific workflow, open an issue with details about your environment and requirements.

Roadmap (high-level)

- v0.1: Stable rule-based evaluator (current).
- v0.2: Structural parser improvements — better control-flow and data-flow matching.
- v0.3: Optional semantic matcher using embeddings for meaning-aware matching.
- v1.0: Web UI and LMS integrations with authentication and bulk-upload features.

Acknowledgements

- Built with inspiration from many autograding projects and course staff tools designed to make feedback faster and fairer.

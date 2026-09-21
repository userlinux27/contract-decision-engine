# Contract Decision Engine

**Contract Decision Engine** is a web application for uploading a PDF contract, checking selected contractual risk factors, and receiving a decision-oriented result. It also publishes downloadable contract templates and a Contract Risk Checker page.

**Demo:** https://contract.workmatic.pro/

> **Disclaimer:** This tool does not provide legal advice.

## What it does

1. Accepts a PDF contract upload (up to 10 MB).
2. Extracts text and document metadata with PyPDF2.
3. Classifies the document from keyword matches and identifies key clause areas.
4. Detects implemented risk factors with regular-expression rules.
5. Weighs the findings and returns a decision, top reasons, and any available suggested wording.
6. Processes uploads asynchronously and exposes task status for frontend polling.

The current decision engine is configured for **service agreements**. Other recognized document categories are classified but are not marked as fully supported by the decision catalogue.

## Key features

- PDF upload, validation, text extraction, page count, language detection, and estimated reading time.
- Keyword-based classification for service agreements, NDAs, employment contracts, tenancy agreements, and unknown documents.
- Rule-based contractual risk detection with contextual text, clause references, confidence values, and selected suggested rewrites.
- Decision calculation that accounts for factor weights and confidence.
- Three built-in demo results: safe, changes recommended, and high risk.
- Asynchronous analysis task creation and status polling.
- Server-rendered contract-template catalogue, individual template pages, and DOCX downloads.
- Event logging endpoints for feedback, copied wording, and template/tool attribution.

## Implemented contract risk factors

The service-agreement catalogue and rule detector implement the following factor pairs:

| Area | Risk factor | Balanced / protective factor |
|---|---|---|
| Liability | Unlimited liability | Liability capped |
| Payment | Unfavorable payment terms | Standard payment terms |
| Intellectual property | IP ownership too broad | IP ownership fair |
| Termination | Unilateral termination | Termination terms balanced |
| Jurisdiction | Jurisdiction unfavorable | Jurisdiction neutral |

Suggested wording is implemented for unlimited liability, unfavorable payment terms, overly broad IP ownership, unilateral termination, and unfavorable jurisdiction.

## Decision outcomes

| Engine value | User-facing outcome |
|---|---|
| `safe_to_sign` | Ready to Sign |
| `sign_after_changes` | Review Recommended |
| `do_not_sign` | High Risk |

The engine aggregates factor weights adjusted by finding confidence. It also checks the configured minimum confidence for a decision and escalates a changes recommendation when a critical finding has no suggested wording.

## Tech stack

- **Backend:** Python, FastAPI, Uvicorn
- **Validation and schemas:** Pydantic
- **PDF processing:** PyPDF2
- **Templating and content rendering:** Jinja2 and Markdown
- **Frontend:** HTML, CSS, and vanilla JavaScript
- **Deployment configuration:** Docker, Docker Compose, Nginx

## High-level architecture

```text
Browser
  -> FastAPI routes and server-rendered pages
  -> upload and task services
  -> PDF parser -> document classifier -> rule detector
  -> service-agreement decision engine -> result polling

Static template content -> Jinja2 template catalogue and detail pages
```

Uploaded files are written to `uploads/` while an in-memory task service tracks processing state and results. Analytics events are logged through the application logging utility.

## Project structure

```text
api/                    FastAPI routers for analysis, tasks, and analytics
content/templates/      Markdown contract templates and page metadata
engine/                 PDF parsing, classification, rules, catalogue, and decisions
fixtures/               Demo decision results
services/               Analysis, document, and task orchestration
static/                 Browser UI, styles, scripts, and downloadable DOCX templates
templates/              Jinja2 pages for the catalogue, details, and tool page
utils/                  Shared logging utility
main.py                 Application setup and page routes
requirements.txt        Python dependencies
```

## Local installation and run

The repository Docker image uses Python 3.11. For a local Python run:

```bash
git clone https://github.com/userlinux27/contract-decision-engine.git
cd contract-decision-engine
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies and start the application:

```bash
pip install -r requirements.txt
python main.py
```

Open http://localhost:8000. The application creates its local `uploads/`, `data/`, and `fixtures/` directories when it starts.

Docker Compose is also provided:

```bash
docker compose up --build
```

This starts the FastAPI application and Nginx; the Nginx service listens on ports 80 and 443 as defined in `docker-compose.yml`.

## API and routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Main contract-upload page |
| GET | `/api/health` | API health response |
| POST | `/api/analyze` | Submit a PDF for asynchronous analysis |
| GET | `/api/tasks/` | List in-memory analysis tasks |
| GET | `/api/tasks/{task_id}` | Get an analysis task's status or result |
| GET | `/analyze/{fixture_type}` | Return a demo fixture: `safe`, `changes`, or `reject` |
| GET | `/demo/{contract_type}` | Legacy demo route for service agreement, NDA, or employment contract fixtures |
| POST | `/feedback` | Log post-result feedback |
| POST | `/analytics/copy` | Log copied suggested wording |
| POST | `/analytics/event` | Log a frontend analytics event |
| POST | `/analytics/template-source` | Log template attribution |
| GET | `/templates` | Contract-template catalogue |
| GET | `/templates/{slug}` | Contract-template detail page |
| GET | `/tools/contract-risk-checker` | Contract Risk Checker page |
| GET | `/robots.txt` | Robots directives |
| GET | `/sitemap.xml` | Generated sitemap |

## Author

**Volodymyr Cherhniavskyi**
GitHub: https://github.com/userlinux27
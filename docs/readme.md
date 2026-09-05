
# Contract Decision Engine

Not an AI contract analyzer. A Decision Engine that answers one question:
**Should I sign this contract?**

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Frontend  │────▶│   API Layer  │────▶│  Services   │────▶│    Engine    │
│ (index.html)│     │  (FastAPI)   │     │  (Orchest.) │     │ (Decision)   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                           │                    │                    │
                           ▼                    ▼                    ▼
                    ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
                    │  Task Queue  │     │  Document   │     │  LLM Service │
                    │  (In-memory) │     │  Service    │     │  (Enrichment)│
                    └──────────────┘     └─────────────┘     └──────────────┘
```

### Key Components

| Layer | Files | Responsibility |
|-------|-------|----------------|
| **API** | `api/analyze.py`, `api/tasks.py` | HTTP endpoints, request/response |
| **Services** | `services/analysis_service.py`, `services/document_service.py`, `services/task_service.py` | Orchestration, document handling, task management |
| **Engine** | `engine/decision_engine.py`, `engine/catalog.py` | **Source of Truth** for decisions |
| **LLM** | `engine/llm_service.py` | Enrichment only (not decision-maker) |
| **Frontend** | `static/index.html`, `static/styles.css`, `static/js/app.js` | Single-page app with Traffic Light UI |

## Quick Start

```bash
pip install -r requirements.txt
python main.py
# Open http://localhost:8000
```

## API Flow

### Real PDF Analysis (Async)
```
POST /api/analyze (multipart/form-data)
    │
    ▼
202 Accepted: { "task_id": "uuid", "status": "processing" }
    │
    ▼
GET /api/tasks/{task_id} (polling every 1s)
    │
    ├──▶ "processing" → continue polling
    ├──▶ "completed" → { "result": {...} }
    └──▶ "failed" → { "error": "..." }
```

### Demo Contracts (Sync)
```
GET /analyze/safe      → { "decision": "safe_to_sign", ... }
GET /analyze/changes   → { "decision": "sign_after_changes", ... }
GET /analyze/reject    → { "decision": "do_not_sign", ... }
```

## Decision Engine — Source of Truth

The **Decision Engine** (`engine/decision_engine.py`) is the single source of truth for all decisions.

### Decision Mapping
| Engine Decision | Traffic Light | Label |
|----------------|---------------|-------|
| `safe_to_sign` | 🟢 GREEN | Ready to Sign |
| `sign_after_changes` | 🟡 YELLOW | Review Recommended |
| `do_not_sign` | 🔴 RED | High Risk |

### Algorithm
1. Receives findings from rule detector (with LLM confidence)
2. Sums weighted scores adjusted by confidence
3. Applies thresholds: safe ≤ 10, changes ≤ 30, else reject
4. Checks critical findings have suggested wording
5. Returns decision + confidence + top 3 reasons

## LLM Role: Enrichment Only

- **LLM does NOT make decisions** — Decision Engine does
- LLM provides: `llm_reason`, `llm_impact`, `suggested_rewrite`
- Current status: **Local stub implementation** (`LLMService.enrich_findings()`)
- Server integration (OpenAI/Ollama): verified separately, not active locally
- Fallback: if LLM fails, analysis continues with rule-based findings only

## Frontend

**Files:** `static/index.html` + `static/styles.css` + `static/js/app.js`

### UI Components
- **Upload Section**: Drag-drop PDF, 3 demo buttons
- **Loading Section**: Spinner with progress messages
- **Result Section**: Traffic Light (main visual) → Decision → Confidence → Analysis Grid
- **Traffic Light**: Large centered bulbs with glow effect
- **Privacy Notice**: "Your contract stays private" on main screen

### Traffic Light Implementation
```css
.traffic-light { gap: 3rem; padding: 2rem; }
.bulb { width: 80px; height: 80px; }
#traffic-light-safe.active .bulb { background: #10b981; box-shadow: 0 0 30px rgba(16,185,129,0.7); }
#traffic-light-changes.active .bulb { background: #f59e0b; box-shadow: 0 0 30px rgba(245,158,11,0.7); }
#traffic-light-reject.active .bulb { background: #ef4444; box-shadow: 0 0 30px rgba(239,68,68,0.7); }
```

## Project Structure

```
contract-decision-engine/
├── main.py                    # FastAPI app, mounts static, includes routers
├── api/
│   ├── analyze.py             # POST /api/analyze, GET /api/health
│   └── tasks.py               # GET /api/tasks/{task_id}, GET /api/tasks/
├── services/
│   ├── analysis_service.py    # Orchestrates full pipeline
│   ├── document_service.py    # PDF validation, saving, parsing
│   └── task_service.py        # In-memory task queue (UUID, status, progress)
├── engine/
│   ├── decision_engine.py     # Source of Truth: BaseDecisionEngine + ServiceAgreementEngine
│   ├── catalog.py             # Decision Catalogue (factors, weights, thresholds)
│   ├── llm_service.py         # LLMService (stub) + OpenAIService (placeholder)
│   ├── pdf_parser.py          # PyMuPDF text extraction
│   ├── classifier.py          # Document classification
│   ├── rule_detector.py       # Rule-based factor detection
│   └── schemas.py             # Pydantic models
├── fixtures/
│   ├── safe.json              # Demo: safe_to_sign
│   ├── changes.json           # Demo: sign_after_changes
│   └── reject.json            # Demo: do_not_sign
├── static/
│   ├── index.html             # HTML structure only
│   ├── styles.css             # Dark theme, Traffic Light styles
│   └── js/app.js              # All frontend logic
└── docs/                      # Architecture, API, Decision Catalogue docs
```

## Documentation

- `docs/02_ARCHITECTURE.md` — System architecture
- `docs/06_API.md` — API specification
- `docs/03_DECISION_CATALOGUE.md` — Decision factors and thresholds
- `docs/05_PROMPTS.md` — LLM prompts
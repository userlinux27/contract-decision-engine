# PRODUCTION_STATE.md

> **Contract Decision Engine — Production Source of Truth**
>
> Этот документ фиксирует не планы и не желаемую архитектуру, а состояние,
> которое подтверждено кодом, production-проверками или проектной документацией.
>
> **Статусы:**
> - ✅ **CONFIRMED** — подтверждено в production / кодом.
> - ⚠️ **LIMITED / PARTIAL** — реализовано, но есть существенное ограничение или подтверждение неполное.
> - ❌ **NOT IMPLEMENTED / NOT CONFIRMED** — не реализовано или production не подтверждён.
> - 📋 **PLANNED** — предусмотрено архитектурой или планом, но production не подтверждён.
>
> **Правило:** если факт не подтверждён, он не должен описываться как production feature.

---

## 1. Current Production State

| Component | Status | Production state |
|---|---|---|
| FastAPI application | ✅ CONFIRMED | Production application is based on FastAPI. |
| PDF upload | ✅ CONFIRMED | `/analyze` accepts uploaded PDF documents. |
| PDF parser | ✅ CONFIRMED | PyMuPDF-based document parsing is implemented. |
| Document classification | ✅ CONFIRMED | Rule-based classification is implemented. |
| Rule detector | ✅ CONFIRMED | Rule-based factor detection is implemented. |
| Decision engine | ✅ CONFIRMED | Rule-based decision engine is implemented. |
| LLM interpreter | ✅ CONFIRMED | LLM enriches detected findings; it does not replace the rule-based decision. |
| LLM provider abstraction | ✅ CONFIRMED | `BaseProvider` interface exists. |
| OpenAI provider | ✅ CONFIRMED | OpenAI provider is implemented. |
| Production LLM model | ✅ CONFIRMED | `gpt-4o-mini` is the documented/default OpenAI model. |
| Gemini provider | 📋 AVAILABLE IN CODE | Provider exists in code, but production use is not confirmed. |
| DeepSeek provider | 📋 AVAILABLE IN CODE | Provider exists in code, but production use is not confirmed. |
| Kimi provider | 📋 AVAILABLE IN CODE | Provider was planned as a provider option; production use is not confirmed. |
| Ollama | ❌ NOT CONFIRMED | No evidence establishes Ollama as the current production LLM provider. |
| Local LLM on production server | ❌ NOT CONFIRMED | Do not describe production as local-only LLM processing. |
| Temporary PDF deletion | ⚠️ LIMITED / PARTIAL | `os.remove(filepath)` is implemented after processing and on parse failure. Historical production inspection also found PDF files in `uploads/`, so retention/cleanup should not be described as globally guaranteed without further verification. |
| Analytics CSV | ⚠️ LIMITED | `data/analytics.csv` exists; current documented use is analytics/metadata, not a permanent contract-document store. |
| External LLM processing | ⚠️ CONFIRMED | With OpenAI active, contract-derived matched text is sent to an external LLM API for interpretation. |
| HTTPS production deployment | ✅ CONFIRMED | Production deployment was established with HTTPS. |
| Database | ⚠️ LIMITED | Application storage exists; exact current production schema should be verified before treating this document as a complete DB inventory. |

---

## 2. Production Architecture

Current application flow:

```text
                    PDF upload
                        │
                        ▼
                 ┌─────────────┐
                 │   FastAPI   │
                 │  /analyze   │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ PDF Parser  │
                 │  PyMuPDF    │
                 └──────┬──────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Language / basic  │
              │ document metadata │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Document          │
              │ Classifier        │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Rule Detector     │
              │ factor detection  │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Decision Engine   │
              │ rule-based        │
              └─────────┬─────────┘
                        │
                  detected findings
                        │
                        ▼
              ┌───────────────────┐
              │ LLM Interpreter   │
              │ enrichment only   │
              └─────────┬─────────┘
                        │
                        ▼
                  API response
                        │
                        ▼
                  analytics/log
```

### Important architectural rule

The LLM is an **interpretation/enrichment layer**.

It is not the authoritative decision-maker.

The rule-based decision engine determines the primary outcome; the LLM adds explanation, impact, suggested rewrite and confidence to detected factors.

---

## 3. LLM Production State

### 3.1 Provider abstraction

The project contains a `BaseProvider` interface. `LLMInterpreter` accepts a provider implementation rather than being hard-coded to one model.

This makes the LLM implementation replaceable without redesigning the interpreter.

### 3.2 OpenAI

Current documented production path:

```text
Provider: OpenAI
Model: gpt-4o-mini
```

The OpenAI implementation sends system/user prompts to the OpenAI API and requests structured JSON output.

### 3.3 What the LLM receives

The interpreter builds a prompt containing, for each detected factor:

```text
Factor
Matched text
Rule explanation
```

Therefore the following statement is **NOT** justified while OpenAI is active:

> "Your contract never leaves our server."

The safer production statement is:

> "Contract files are processed on our server, but relevant detected contract excerpts may be sent to our external AI provider for interpretation."

If the product later switches to a fully local LLM, this section must be updated and independently verified.

---

## 4. Ollama / Local Model Status

### Current state

**❌ NOT CONFIRMED AS PRODUCTION**

The recovered documentation confirms a provider abstraction and multiple provider implementations, but does **not** establish that Ollama was deployed as the production LLM provider.

Therefore:

```text
Ollama production provider:        NOT CONFIRMED
Local LLM production processing:   NOT CONFIRMED
OpenAI production provider:        CONFIRMED / documented
```

### Architectural implication

A local provider can be added without redesigning `LLMInterpreter`, because the interpreter accepts a `BaseProvider`.

Conceptually:

```text
LLMInterpreter
      │
      ▼
 BaseProvider
      │
 ┌────┼─────────┬─────────┐
 ▼    ▼         ▼         ▼
OpenAI Gemini DeepSeek  Local/Ollama
```

This is an architectural capability, not proof that Ollama is currently deployed.

---

## 5. Privacy Reality

### 5.1 PDF storage

The application saves the uploaded PDF temporarily under:

```text
uploads/{task_id}.pdf
```

The code explicitly calls:

```python
os.remove(filepath)
```

after processing and also when PDF parsing fails.

### 5.2 Important limitation

Production inspection previously found PDF files in `uploads/`.

Therefore this document intentionally does **not** claim:

> "All uploaded files are always deleted immediately."

Until a fresh production verification confirms the complete lifecycle, the correct status is:

> Temporary-file deletion is implemented, but retention/cleanup should be re-verified in production.

### 5.3 External processing

When OpenAI is active, the LLM interpreter sends selected contract-derived text to OpenAI.

This is the most important privacy fact for the current Alpha.

---

## 6. Decision Engine

### Confirmed design

The decision engine is rule-based.

The LLM does not directly determine:

```text
Ready to Sign
Review Recommended
High Risk
```

Instead:

```text
Contract
   ↓
Classification
   ↓
Rule detection
   ↓
Decision Engine
   ↓
Primary decision
   ↓
LLM interpretation
   ↓
Explanation / impact / suggested rewrite / confidence
```

### Product principle

**Do not allow the LLM to silently become the decision engine.**

If this changes in the future, it must be a deliberate architecture/version change and documented here.

---

## 7. Current Alpha Capabilities

The recovered project history indicates the following progression:

### v0.1
- application skeleton;
- `POST /analyze`.

### v0.2
- document text extraction.

### v0.3
- document classification;
- rule-based decision engine for Service Agreement.

### v0.4
- Decision Catalogue;
- multiple risk factors;
- rule detector;
- decision outcomes:
  - Ready to Sign;
  - Review Recommended;
  - High Risk.

### v0.5
- LLM integration;
- provider abstraction;
- LLM interpretation of detected factors;
- JSON output;
- fallback when LLM is unavailable.

---

## 8. LLM Fallback Behaviour

The LLM interpreter contains a fallback path.

If LLM interpretation fails, the application keeps the base findings rather than making the entire rule-based analysis dependent on successful LLM execution.

Conceptually:

```text
Rule findings
      │
      ├── LLM available ──► enriched findings
      │
      └── LLM unavailable ─► base findings / fallback
```

This separation is important for reliability and should remain true unless explicitly changed.

---

## 9. Analytics / Logging

A production inspection showed:

```text
data/analytics.csv
```

The application logs processing metadata including items such as:

- task ID;
- upload event;
- file size;
- page count;
- document type;
- decision;
- processing information.

Analytics must not be described as a permanent storage location for full contract contents unless the implementation is explicitly changed and verified.

---

## 10. Security / Privacy Claims Allowed on Landing Page

### Safe claims

The current production state supports statements along these lines:

- "Your contract is processed securely."
- "Uploaded PDFs are processed temporarily."
- "The primary contract decision is rule-based."
- "AI is used to explain detected contract risks."
- "We use an external AI provider for AI interpretation."

### Claims NOT currently justified

Do **not** claim:

- "Your contract never leaves our server."
- "100% local AI."
- "No third-party AI provider processes contract text."
- "All uploaded files are permanently deleted immediately."
- "We never store any contract-derived information."

These claims require additional production verification or architecture changes.

---

## 11. Provider Configuration

Current environment concept:

```text
OPENAI_API_KEY=<SET>
GEMINI_API_KEY=<SET>
DEEPSEEK_API_KEY=<SET>
KIMI_API_KEY=<SET>
LLM_PROVIDER=<SET>
```

Current documented configuration:

```text
LLM_PROVIDER=openai
```

Do not assume that the presence of an API key means that provider is active.

**Active provider must always be determined from `LLM_PROVIDER` and the actual production configuration.**

---

## 12. Architecture Principles

The project documentation establishes several important principles:

### Separation of responsibility

Each module should have one responsibility.

### Replaceable modules

Modules have explicit interfaces so that implementations can be replaced without redesigning the whole application.

### Configuration over magic values

Important parameters should live in configuration rather than being scattered through code.

### LLM separation

The LLM should enrich/interpret rule findings rather than silently replacing the deterministic decision layer.

---

## 13. What Is NOT Yet Production-Confirmed

The following should remain explicitly unconfirmed until checked on the live server:

- exact current git commit/version;
- exact current `LLM_PROVIDER` value;
- exact running model;
- Ollama installation and active service;
- local model actually serving production requests;
- complete PDF deletion lifecycle;
- backups and restore procedure;
- authentication/rate limiting;
- production database schema;
- monitoring/alerting;
- automated privacy verification;
- retention period for analytics/logs;
- deletion of all derived contract data;
- production load/performance limits.

---

## 14. Verification Checklist

Before changing any status from ⚠️/❌/📋 to ✅, verify directly on production.

### LLM

```bash
cd ~/contract-decision-engine

grep -R "LLM_PROVIDER" -n . --exclude-dir=.git --exclude-dir=__pycache__
grep -R "ollama" -n . --exclude-dir=.git --exclude-dir=__pycache__
grep -R "gpt-4o-mini" -n . --exclude-dir=.git --exclude-dir=__pycache__
```

### Running processes

```bash
ps aux | grep -Ei 'uvicorn|fastapi|ollama|contract-decision' | grep -v grep
```

### Ollama

```bash
ollama --version
ollama list
systemctl status ollama --no-pager
```

### Upload retention

```bash
find uploads -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\n' 2>/dev/null | sort
```

### Application logs

Check whether the active LLM provider/model is printed or otherwise observable during an actual `/analyze` request.

### Privacy verification

Upload a controlled test contract containing a unique marker, for example:

```text
PRODUCTION_PRIVACY_TEST_2026_XXXX
```

Then verify:

1. whether the marker reaches the external provider;
2. whether the PDF remains on disk;
3. whether the marker appears in logs;
4. whether the marker appears in analytics;
5. whether the marker appears in database records;
6. whether temporary files are removed.

Do not use a real customer's confidential contract for this test.

---

## 15. Change Log

### 2026-08-27

Created `PRODUCTION_STATE.md` as the production source-of-truth document.

Initial state based on recovered project documentation and production inspection evidence.

Key conclusions:

1. OpenAI / `gpt-4o-mini` is the documented production LLM path.
2. LLM provider abstraction exists.
3. Local Ollama production use is **not confirmed**.
4. The LLM receives detected/matched contract text for interpretation.
5. Temporary PDF deletion is implemented, but complete retention behaviour requires re-verification.
6. Privacy claims must reflect external LLM processing while OpenAI is active.
7. Rule-based decision logic remains the primary decision layer.

---

## 16. Source-of-Truth Rule

When this file conflicts with older documentation:

**Production evidence wins.**

Priority:

```text
1. Live production verification
2. Current production code/configuration
3. Automated tests
4. Current architecture documentation
5. Historical plans / roadmaps
6. Assumptions
```

Never promote a historical plan to "implemented" without verification.

---

## 17. Next Recommended Verification

The next engineering task should **not** be another architecture rewrite.

It should be a short **Production Reality Audit**:

```text
LIVE SERVER
    │
    ├── active LLM provider
    ├── active model
    ├── Ollama status
    ├── PDF lifecycle
    ├── logs
    ├── analytics
    └── database
            │
            ▼
    update PRODUCTION_STATE.md
```

After that audit, this file becomes the baseline for all future development.

# API Specification (Спецификация API)

> Версия: v1.0
> Базовый URL: `http://localhost:8000`
> Версия: v0.1
> Версия: v1.0


### GET /
Главный экран. Возвращает HTML-страницу.

**Ответ:** `text/html`

---

### POST /api/analyze
Загрузка PDF для анализа (асинхронно).
### POST /analyze
Загрузка PDF для анализа.
### POST /api/analyze
Загрузка PDF для анализа (асинхронно).

**Успешный ответ (202 Accepted):**
2026-08-05T14:31:00,abc123,copy_wording,clause=4.2
2026-08-05T14:32:00,abc123,feedback,action=changes|useful=yes|time_to_decision=42
`
      "suggested_rewrite": null
    }
  ]
```

**Ошибки:**
- 404 — fixture не найден
- 500 — файл fixture отсутствует

---

### POST /feedback
Приём обратной связи после отчёта.

**Запрос:**
```json
{
  "visitor_id": "abc123",
  "action": "changes",
  "useful": "yes",
  "time_to_decision": 42
}
```

**Поля:**
- `visitor_id` (string) — ID посетителя из localStorage
- `action` (string | null) — `signed` | `changes` | `walked` | `deciding`
- `useful` (string | null) — `yes` | `no`
- `time_to_decision` (int | null) — секунды от показа результата до ответа

**Ответ (200):**
```json
{"status": "ok"}
```

---

### POST /analytics/copy
Отслеживание копирования suggested wording.

**Запрос:**
```json
{
  "visitor_id": "abc123",
  "clause": "4.2"
}
```

**Ответ (200):**
```json
{"status": "ok"}
```

---

## Decision Mapping (Frontend)

| Engine Decision | Traffic Light | Label |
|----------------|---------------|-------|
| `safe_to_sign` | 🟢 GREEN | Ready to Sign |
| `sign_after_changes` | 🟡 YELLOW | Review Recommended |
| `do_not_sign` | 🔴 RED | High Risk |

---

## AnalysisResult Schema (Result Object)

Возвращается в `result` при `GET /api/tasks/{task_id}` со статусом `completed`:

```json
{
  "classification": {
    "document_type": "service_agreement",
    "display_name": "Service Agreement",
    "confidence": 0.95,
    "supported": true,
    "key_clauses_found": ["payment", "liability", "termination"]
  },
  "pipeline": {
    "text_length": 5000,
    "word_count": 800,
    "pages": 3,
    "language": "en",
    "estimated_reading_time_min": 5,
    "processing_time_sec": 2.3,
    "parser": "pdf_parser_v1.0"
  },
  "decision": "sign_after_changes",
  "decision_details": {
    "decision": "sign_after_changes",
    "confidence": 0.91,
    "top_reasons": [...],
    "all_findings": [...],
    "total_weight": 25
  },
  "decision_labels": {
    "safe_to_sign": "✅ Ready to Sign",
    "sign_after_changes": "🟡 Review Recommended",
    "do_not_sign": "🔴 High Risk"
  }
}
```

---

## Аналитика

Все события пишутся в `data/analytics.csv`:

```csv
timestamp,visitor_id,event,extra
2026-01-15T10:30:00,abc123,upload,file_size_kb=245
2026-01-15T10:31:00,abc123,deciding,time_to_decision=42
2026-01-15T10:31:05,abc123,copy_wording,clause=4.2
2026-01-15T10:32:00,abc123,feedback,action=changes|useful=yes|time_to_decision=42
```

**События:**
- `upload` — загрузка PDF
- `deciding` — пользователь увидел результат
- `copy_wording` — копирование suggested rewrite
- `feedback` — ответ на "Was this useful?" + "What did you do next?"

---

## Frontend Integration

### Real PDF Flow
```javascript
// 1. Upload
const resp = await fetch('/api/analyze', { method: 'POST', body: formData });
const { task_id } = await resp.json();

// 2. Polling
const poll = async () => {
  const r = await fetch(`/api/tasks/${task_id}`);
  const data = await r.json();
  if (data.status === 'completed') return data.result;
  if (data.status === 'failed') throw new Error(data.error);
  await new Promise(r => setTimeout(r, 1000));
  return poll();
};
const result = await poll();
```

### Demo Flow
```javascript
const resp = await fetch('/analyze/safe');
const data = await resp.json();
// Immediately render result
```Файл: docs/06_API.md (полная версия)

# API Specification (Спецификация API)

> Версия: v0.1
> Базовый URL: `http://localhost:8000`

---

## Эндпоинты

### GET /
Главный экран. Возвращает HTML-страницу.

**Ответ:** `text/html`

---

### POST /analyze
Загрузка PDF для анализа.

**Запрос:**
- Content-Type: `multipart/form-data`
- Поле `file`: PDF-файл (макс. 10 МБ)

**Успешный ответ (202):**
json
{
  "task_id": "550e8400-e29b-41  d4-a716-446655440000",
  "status": "processing",
  "message": "Analyzing your contract..."
}

Ошибки:

· 400 — файл не PDF
· 400 — файл больше 10 МБ

---

GET /demo/{contract_type}

Возвращает предзаполненный результат для демо-договора.

Параметры пути:

· contract_type: service-agreement | nda | employment-contract

Ответ (200):

json
{
  "decision": "sign_after_changes",
  "confidence": 0.91,
  "top_reasons": [
    {
      "factor": "Unlimited liability",
      "weight": 30,
      "reason": "Исполнитель несёт ответственность без ограничения суммы."
    }
  ],
  "all_findings": [
    {
      "clause": "4.2",
      "type": "unlimited_liability",
      "severity": "critical",
      "confidence": 0.96,
      "reason": "...",
      "original_text": "...",
      "suggested_rewrite": "..."
    }
  ]
}

Ошибки:

· 404 — тип договора не найден

---

POST /feedback

Приём обратной связи после отчёта.

Запрос:

json
{
  "visitor_id": "abc123",
  "action": "changes",
  "useful": "yes",
  "time_to_decision": 42
}

Поля:

· visitor_id (string) — ID посетителя из localStorage
· action (string | null) — signed | changes | walked | deciding
· useful (string | null) — yes | no
· time_to_decision (int | null) — секунд от показа результата до ответа

Ответ (200):

json
{"status": "ok"}

---

POST /analytics/copy

Отслеживание копирования suggested wording.

Запрос:

json
{
  "visitor_id": "abc123",
  "clause": "4.2"
}

Ответ (200):

json
{"status": "ok"}

---

Аналитика

Все события пишутся в data/analytics.csv в формате:

timestamp,visitor_id,event,extra
2026-08-05T14:30:00,abc123,upload,file_size_kb=245
2026-08-05T14:31:00,abc123,copy_wording,clause=4.2
2026-08-05T14:32:00,abc123,feedback,action=changes|useful=yes|time_to_decision=42
`
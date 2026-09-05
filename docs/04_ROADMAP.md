# Roadmap v1.0

## Phase 0: Foundation (Day -1)
- [x] Vision document
- [x] Decision Journal created
- [x] Decision Catalogue v1.0
- [x] Architecture document
- [x] Project structure initialized

## Phase 1: Demand Validation (Week 1)
- [ ] Day 1: FastAPI skeleton + main screen
- [ ] Day 2: PDF parsing + LLM integration + prompts
- [ ] Day 3: Decision Engine v1.0
- [ ] Day 4: Result screen + feedback collection
- [ ] Day 5: Demo contracts + frontend polish
- [ ] Day 6: Analytics + Time to Decision tracking
- [ ] Day 7: Deploy + first 20 users

Success criteria: A user returns and uploads a second contract unprompted.

## Phase 2: First Paying Users (Month 1)
- Stripe integration
- €20–50/month subscription
- User accounts (minimal)
- Document history (last 5)

## Phase 3: Platform Expansion (Month 3)
- Second document type: NDA
- Refactor prompts and factors for new type
- BaseDecisionEngine reused without modification

## Phase 1: Demand Validation (Неделя 1) — Новый порядок

### День 1: Demo First (Сначала демонстрация)
- [x] Fixtures: safe.json, changes.json, reject.json
- [x] Эндпоинт /analyze/{fixture_type}
- [x] Три демо-кнопки с соответствующими фикстурами
- [x] Полный цикл: лендинг → загрузка → отчёт → обратная связь
- [ ] Показать первому реальному пользователю

Критерий: человек говорит «Да, этим было бы удобно пользоваться»

### День 2: Decision Engine (Движок принятия решений)
- Подключаем реальный engine/decision_engine.py
- Убираем fixtures, заменяем на работу движка
- Движок пока получает данные не от LLM, а из тех же fixtures (ручная эмуляция)

### День 3: PDF Parser (Парсер PDF)
- Реализуем engine/parser.py
- Извлекаем текст из реального PDF
- Пока без LLM — выводим извлечённый текст для проверки

### День 4: LLM Integration (Подключение LLM)
- Интегрируем OpenAI или Ollama
- Используем промпт из prompts/service_agreement.md
- Связываем: PDF → текст → LLM → Decision Engine → отчёт

### День 5: Полный цикл и полировка
- Три демо-договора как реальные PDF в demos/
- Тестирование полного цикла на реальных договорах

### День 6: Аналитика
- Доработка сбора событий
- Скрипт просмотра аналитики

### День 7: Деплой и первые 20 пользователей
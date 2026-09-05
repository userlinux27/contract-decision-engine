markdown
# Vision (Видение)

## What We Build (Что мы строим)

We are NOT building an AI contract analyzer.
We are NOT building a single service.

We are building a Decision Engine Platform — a platform that turns complex documents into clear business decisions.

## Current Product (Текущий продукт)

Contract Decision Engine — первый модуль платформы.
Помогает владельцу малого агентства понять, стоит ли подписывать договор.

## Platform Vision (Видение платформы)


Decision Platform (Платформа принятия решений)
│
├── Contract Decision Engine   ← мы здесь (День 1)
├── Tender Decision Engine     ← Месяц 3+
├── Insurance Decision Engine
├── Vendor Decision Engine
├── HR Decision Engine
└── Policy Decision Engine

Общее ядро: BaseDecisionEngine, Decision Catalogue, принципы explainability (объяснимости).
Разное для каждого модуля: набор факторов, промпты, демо-документы.

## Core Philosophy (Ключевая философия)

> Decision Engine превращает сложный документ в понятное бизнес-решение.

Не «AI анализирует договор», а «вы загрузили документ — получили решение».

## Key Principles (Ключевые принципы)

1. Decision over Analysis (Решение важнее анализа). Одна ясная рекомендация, а не список рисков.
2. Explainability (Объяснимость). Пользователь видит, почему принято именно такое решение (топ-3 причины).
3. Speed (Скорость). Time to Decision < 60 секунд.
4. Honesty (Честность). Confidence Score показывает, когда мы не уверены.
5. Actionability (Применимость). Для каждой проблемы — suggested safer wording (предложенная безопасная формулировка).

## What We Don't Do (Что мы не делаем)

- Не заменяем юристов.
- Не даём юридических консультаций.
- Не храним документы пользователей.
- Не строим функции до проверки основной потребности.

## Success Metric — Week 1 (Метрика успеха — Неделя 1)

Владелец небольшого агентства загружает второй договор без напоминания.

## Long-term Goal (Долгосрочная цель)

Платформа Decision Engine, где меняется только предметная область (договоры, тендеры, страховки, HR-документы), а ядро остаётся неизменным
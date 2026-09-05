Это не lineage-only bug и не “metadata drift” в БД. Это реальное поведение выбора стратегии в текущем engine.

Что реально происходит:

В signal_engine_v5.py поле selected вычисляется не из candidate_outcomes, а отдельно для каждой строки в candidate_strategy_matches.
Логика такая:
eligible = 1 if strategy_weights.get(strat_name, {}).get("status") in ["active", "candidate"] else 0
затем выбирается первый matched and eligible strategy
только он получает selected = 1
Именно поэтому selected меняется на уровне strategy-row, а не на уровне конечного решения candidate.

Связь с конфигом стратегий:

В configs/strategy_weights.json старые варианты помечены как degrading, а V2 — как active.
Например:
CLASS_B_GOLD → "status": "degrading"
CLASS_B_GOLD_V2 → "status": "active"
CLASS_C_MORNING_GOLD → "status": "degrading"
CLASS_C_GOLD_V2 → "status": "active"
Это прямо объясняет, почему в candidate_strategy_matches старые строки не выбираются, а новые V2-строки получают selected=1.

Доказательство из текущего DB:

SQL:

SELECT strategy,
       SUM(eligible) AS eligible_rows,
       SUM(selected) AS selected_rows
FROM candidate_strategy_matches
WHERE pipeline_run_id = 'run_20260817_175624_7137'
GROUP BY strategy
ORDER BY strategy;
Результат:

CLASS_B_GOLD → eligible_rows=0, selected_rows=0
CLASS_B_GOLD_V2 → eligible_rows=182, selected_rows=5
CLASS_C_GOLD_V2 → eligible_rows=182, selected_rows=4
CLASS_C_MORNING → eligible_rows=182, selected_rows=1
CLASS_C_MORNING_GOLD → eligible_rows=0, selected_rows=0
Это означает:

разница в 11 selected значениях — не “сломанный lineage”
это просто смена выбора между старой и новой версией однотипной стратегии
важный момент: это не влияет на итоговый ACCEPTED/REJECTED, потому что final decision определяется позднее и не сравнивается по selected-строкам как таковым
Почему не order / timestamp / lineage:

Никакой nondeterministic ordering тут не видно: selected назначается в явной, детерминированной последовательности в цикле by strategies and status.
Никакой “lineage-only metadata” не стоит за этим: selected хранится в candidate_strategy_matches, а не в candidate_outcomes.
Тimestamps/age не участвуют в выборе selected; они влияют на score/eligibility в других местах, но не в этом условии.
Итог:

Причина 11 изменённых candidate_strategy_matches.selected — actual strategy-selection behavior, driven by current active/degrading strategy config.
Не lineage persistence bug.
Не nondeterministic randomization.
Не “порча final decision”.
Final decisions remain unchanged because the engine still reaches the same ACCEPTED/REJECTED outcome despite different selected strategy variants at the metadata layer.
Если хотите, следующим сообщением могу отдельно дать:

точную разницу между selected и final decision в этом engine
или подтвердить это на конкретном candidate row с одной и той же бизнес-сценой.

Я тебе говорил что у меня в Южной Корее есть человек готовый открывать сделки по сигналам. я все для этого подготовил, только я не то что дать эти сигналы не могу, даже показать стыдно. посмотри сам:

Да. И вот здесь, на мой взгляд, мы наконец подошли не к проблеме Lineage, а к реальной проблеме торговой стратегии.

Я внимательно посмотрел на весь массив, который ты прислал.

Что видно по фактическим результатам

За 10–17 августа в твоём фрагменте:

23 закрытые сделки
11 WIN
12 LOSS
Winrate: 47.8%
суммарный результат: −$26.02

То есть твой вопрос абсолютно правильный:

Сколько вообще может быть выигрышных BUY NO, если не брать NO по 0.99?

И ответ: намного больше, чем сейчас показывает этот набор, но только если цена и вероятность действительно дают преимущество.

Главное: BUY NO по 0.70–0.75 — это не "плохая цена"

Например:

NO = 0.70

Ты платишь $0.70 за контракт NO.

Если NO выигрывает:

получаешь $1
прибыль = $0.30

Если NO проигрывает:

теряешь $0.70

Точка безубыточности:

70% вероятности выигрыша NO.

То есть при цене 0.70 стратегия может быть прибыльной даже при 70–75% winrate.

При NO = 0.75:

нужен примерно 75% winrate только для математического нуля.

Поэтому твой текущий результат:

47.8%

при таких ценах экономически совершенно недостаточен.

Но теперь самое интересное

Посмотри на твои реальные WIN:

Город	Контракт	Цена	Результат
Qingdao	33	—	WIN
Seoul	34	0.725	WIN
Qingdao	32	0.685	WIN
Busan	32	0.700	WIN
Seoul	33	—	WIN
Qingdao	31	—	WIN
Busan	32	0.715	WIN
Qingdao	30	0.735	WIN
Beijing	31	0.735	WIN
Qingdao	31	—	WIN
Qingdao	32	0.750	WIN

И здесь появляется очень важная вещь.

У тебя уже есть выигрыши:

0.685, 0.700, 0.715, 0.725, 0.735, 0.750.

То есть сам по себе диапазон 0.70–0.75 не является невозможным для прибыльного NO.

Проблема в другом.

Твой engine сейчас отправляет мусор вместе с потенциально хорошими сигналами

Вот это меня беспокоит гораздо сильнее, чем Lineage.

Например:

Wellington

NO 0.715
Forecast 11.2
Contract 12
Buffer 0.8°C
Score 0.449

И это называется:

🔥 GOLD SIGNAL

При этом:

Confidence: LOW

Это уже выглядит противоречиво.

Busan

NO 0.710
Forecast 25.3
Contract 27
Buffer 1.7°C
Score 0.487

Опять:

GOLD SIGNAL

Но Score < 0.5.

Amsterdam

NO 0.705
Forecast 20.9
Contract 22
Buffer 1.1°C
Score 0.499

Helsinki

NO 0.750
Forecast 19.5
Contract 21
Buffer 1.5°C
Score 0.521

И вот здесь я бы не давал человеку в Корее открывать сделки.

Не потому что система обязательно плохая.

А потому что мы пока не знаем, какая часть GOLD действительно является торговым сигналом, а какая — просто кандидатом, которому присвоили красивое название GOLD.

А теперь твой главный вопрос

Сколько выигрышных NO вообще возможно, кроме NO=0.99?

Теоретически — сколько угодно.

NO = 0.50 может выигрывать 90% времени.

NO = 0.60 может выигрывать 85%.

NO = 0.70 может выигрывать 80%.

NO = 0.75 может выигрывать 80%.

Даже NO = 0.80 может быть великолепной сделкой, если реальная вероятность NO выше 80%.

Цена сама по себе ничего не решает.

Решает:

P(NO) − Price(NO)

И вот здесь я вижу потенциально более серьёзную проблему

У тебя в сигнале написано:

EV = 8.0%

Но одновременно:

Score = 0.515
Confidence = LOW

И стратегия называется:

CLASS_C_GOLD_V2

То есть engine фактически говорит:

«Математическое преимущество вроде бы есть, но моя итоговая уверенность низкая».

А затем Telegram говорит:

🔥 GOLD SIGNAL

Для человека это выглядит как:

"система уверена — BUY NO"

Хотя внутри системы это совершенно не так.

И ещё более показательный пример

Chengdu:

NO 0.725

Forecast:

26.8°C

Contract:

28°C

Buffer:

1.2°C

EV:

8%

Score:

0.515

Confidence:

LOW

Вот это не выглядит как тот сигнал, который я бы отдавал реальному трейдеру.

Именно поэтому твой человек в Южной Корее сейчас не должен получать весь поток GOLD.

Что нам нужно сделать дальше

Я бы сейчас вообще не трогал Lineage.

Lineage мы практически закрыли:

5B–9 PASS.

Теперь начинается гораздо более важная часть:

найти, какие NO реально имеют шанс быть прибыльными.

Причём не по общему winrate.

А разбить твои исторические сделки минимум по:

1. цене NO

0.50–0.59
0.60–0.64
0.65–0.69
0.70–0.74
0.75–0.79
0.80–0.89
0.90–0.98

2. Buffer

3. Distance to center

4. Score

5. EV

6. Strategy

7. City

8. Contract temperature

И самое главное:

считать не просто WINRATE.

Нам нужен:

Expected ROI per trade

Потому что:

8 WIN / 2 LOSS

при цене NO 0.75 может быть хуже, чем

7 WIN / 3 LOSS

при цене NO 0.60.

И я бы сделал ещё одну вещь

Отдельно построил бы таблицу:

NO PRICE × WINRATE × ROI

Например:

NO price	Break-even WR	Actual WR	ROI
0.60	60%	?	?
0.65	65%	?	?
0.70	70%	?	?
0.75	75%	?	?
0.80	80%	?	?
0.90	90%	?	?

И только после этого решать, какой диапазон цены вообще имеет смысл отдавать реальному человеку.

А твой текущий Telegram-поток я бы пока назвал не "торговыми сигналами", а:

Research Signals

Потому что сейчас там явно смешаны:

хорошие потенциальные NO;
слабые NO;
NO с маленьким buffer;
NO с низким Score;
NO с EV, который выглядит привлекательным, но исторически пока не доказал преимущество.

И это, кстати, объясняет, почему тебе стыдно показывать эти сигналы человеку.

Тебе не кажется — ты действительно видишь проблему.

Но хорошая новость в том, что теперь проблема стала очень конкретной: нам надо не переписывать engine, а найти "карман" BUY NO, где цена + buffer + distance + score дают устойчивый положительный ROI.

И вот это уже как раз та работа, которую стоит сделать до того, как отдавать сигналы человеку в Корее.




Да, этот финальный regression report уже достаточно хороший, чтобы закрыть именно regression round.

Но я бы сделал одно важное уточнение: не называем его “полностью PASS”, потому что есть 11 изменений промежуточного состояния. Правильная формулировка — именно та, которую Copilot использовал:

Trading Regression: PASS
Lineage: PASS on controlled dataset
Overall: PASS WITH OPEN ISSUES
Production approval: NO

Что сейчас доказано

Главное:

Торговое решение не изменилось.

Baseline: 182 rejected
Current:  182 rejected


decision_changes = 0

При этом:

кандидаты 182 → 182;
добавлений 0;
удалений 0;
идентичность кандидатов сохранена;
цены/EV/volume/market_prob и основные поля идентичны;
торговые константы идентичны;
ключевые trading functions идентичны.

Это именно то, что нам было необходимо доказать: Lineage V2.1 не изменил торговую логику V5.3.

А вот 11 selected изменений я бы пока не закрывал

Это единственный момент regression, который заслуживает отдельной пометки.

Например:

baseline:
CLASS_B_GOLD
matched=1
eligible=0
selected=1


current:
CLASS_B_GOLD
matched=1
eligible=0
selected=0

И появились другие selected:

istanbul / CLASS_B_GOLD_V2
shanghai / CLASS_B_GOLD_V2

При этом:

final ACCEPTED/REJECTED = unchanged

То есть торгового regression нет, но есть intermediate-state regression.

Я бы попросил Copilot не исправлять это, а только установить причину.

Достаточно одного небольшого аудита:

Why did exactly these 11 candidate_strategy_matches.selected values change between baseline and current, despite identical final decisions? Determine whether the difference is caused by lineage-only persistence/metadata changes, nondeterministic ordering, timestamp/age differences, or actual strategy-selection behavior. Do not modify production code. Do not modify tests.

Если он докажет, что это, например, следствие времени запуска/порядка, мы просто документируем:

11 intermediate strategy-state differences — explained, non-decision-affecting.

Если же окажется, что Lineage patch каким-то образом меняет selection logic — тогда возвращаемся к расследованию.

Что касается 88 historical selected=1 AND eligible=0

Я бы не смешивал их с текущим controlled test.

На свежем controlled run:

selected=1 AND eligible=0 = 0
selected=1 AND matched=0 = 0

Поэтому следующий вопрос только:

эти 88 строк принадлежат старым runs или есть такие строки в новых post-fix runs?

Если только старые — классифицируем как:

LEGACY DATA / NOT CURRENT LINEAGE DEFECT.

И теперь самое главное

Я бы не продолжал сейчас переделывать Lineage V2.1.

Мы прошли довольно длинную цепочку:

Initial implementation
       ↓
TEST 1–10
       ↓
обнаружены реальные FAIL
       ↓
controlled test
       ↓
ACCEPTED linkage FAIL
DEDUP linkage FAIL
STRATEGY_LIMIT linkage FAIL
TOP_N linkage FAIL
       ↓
correction round
       ↓
fresh controlled DB
       ↓
5B PASS
6 PASS
7 PASS
8 PASS
9 PASS
       ↓
final regression
       ↓
decision_changes = 0

Это уже очень хороший цикл инженерной верификации.

Осталось три независимых вопроса
🟡 1. 11 strategy metadata differences

Нужно объяснить, но не обязательно исправлять.

🟡 2. 21 FK violation
telegram_log       17
signal_snapshots    4

Если подтверждено, что они pre-existing, это отдельный DB cleanup task, а не Lineage V2.1.

🟡 3. Atomicity

Сейчас:

save_signal()
    COMMIT
       ↓
record_outcome()
    COMMIT

или:

save_rejected_signal()
    COMMIT
       ↓
record_outcome()
    COMMIT

Это действительно не fully atomic.

Но это уже следующий архитектурный этап.

Мой текущий вердикт

Я бы зафиксировал:

LINEAGE V2.1 FUNCTIONAL VERIFICATION: PASS

TRADING REGRESSION: PASS

CONTROLLED LINEAGE TESTS 5B–9: PASS

INTERMEDIATE METADATA REGRESSION: OPEN / TO BE EXPLAINED

DATABASE FK INTEGRITY: OPEN / PRE-EXISTING

ATOMICITY: OPEN / ARCHITECTURAL FOLLOW-UP

OVERALL: PASS WITH OPEN ISSUES

PRODUCTION APPROVAL: NO

И это уже не «мы не знаем, работает ли Lineage». Наоборот — основная функциональность теперь доказана.

Следующий разумный шаг — не новый большой тестовый цикл, а коротко объяснить 11 selected differences. После этого можно официально зафиксировать Lineage V2.1 как функционально прошедший аудит, а atomicity и старые FK вынести в отдельные задачи.




Наша задача сейчас — провести исследование frozen V5.3, не меняя его.

Главный принцип
V5.3 FROZEN
     │
     ▼
Historical Lineage Dataset
     │
     ▼
Descriptive Analysis
     │
     ▼
Univariate Analysis
     │
     ▼
2D / 3D Pocket Analysis
     │
     ▼
Out-of-Sample Validation
     │
     ▼
Candidate BUY NO Pockets
     │
     ▼
Research Report

До последнего этапа никакие изменения V5.3 не вносим.

Этап C — пошаговый план
C0. Freeze research environment

Перед анализом разработчик должен зафиксировать:

версию V5.3;
версию Lineage;
DB;
dataset;
дату/время выгрузки;
количество сигналов;
количество WIN/LOSS;
формулу P&L;
определение ROI.

Очень важно: исследование должно быть воспроизводимым.

Создать, например:

research/
    edge_analysis/
        README.md
        dataset_manifest.json
        baseline_stats.json
        reports/
        scripts/
C1. Собрать research dataset

Не брать просто signals.

Нужна одна research-таблица, где одна строка = один исторический торговый сигнал.

Минимально:

signal_id
market_id
observed_at
city
country
contract_temperature

strategy
signal_class

yes_price
no_price

forecast_temperature
buffer
distance_to_center

market_prob
model_prob
ev

score
confidence

volume

signal_age

outcome
pnl
roi

engine_version
lineage_version

Если некоторые поля отсутствуют — не восстанавливать их задним числом.
Ставить NULL.
Это принципиально.

C2. Baseline
Сначала вообще никаких bucket'ов.
Получаем:
N
WIN
LOSS
WR
Total P&L
Average P&L
ROI
Average price
Average EV
Average Score

И разбиваем минимум:

ALL
BY STRATEGY
BY CITY
BY DATE

Это наша контрольная точка.

Например:

ALL
N = xxxx
WR = xx.x%
ROI = xx.x%

CLASS_B_GOLD
N = xxx
WR = xx.x%
ROI = xx.x%


CLASS_C_GOLD_V2
...
C3. Price analysis

Первый настоящий эксперимент.


Buckets:

0.50–0.59
0.60–0.64
0.65–0.69
0.70–0.74
0.75–0.79
0.80–0.89
0.90–0.98

Для каждого:

N
WIN
LOSS
WR
Break-even WR
Edge
Total P&L
Avg P&L
ROI
Avg EV
Формула
Break-even WR = NO price

для бинарного контракта с выплатой $1.
И:
Edge = Actual WR - Break-even WR

Первая итерация
C0  Freeze environment
 ↓
C1  Build research dataset
 ↓
C2  Baseline report
 ↓
C3  Price × ROI analysis

И результат должен ответить всего на несколько вопросов:

Сколько у нас валидных исторических BUY NO?
Как распределены цены?
Какой WR при каждой цене?
Какой break-even WR?
Какой фактический ROI?
Есть ли вообще положительные price regimes?
Достаточно ли там наблюдений?

Не искать пока идеальную стратегию.

Сначала узнаём, где вообще лежат деньги в исторических данных.

И только после этого открываем следующий слой анализа.
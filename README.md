# Event Ingest & Analytics

## Опис роботи

Сервіс збирає події користувачів, забезпечує ідемпотентність, аналітичні запити (DAU, топ-івенти, retention) і підтримує асинхронний інгест через **NATS-чергу**.  
Архітектура побудована на **FastAPI + PostgreSQL + SQLAlchemy (async)**.  
Є CLI-інструмент для імпорту історичних подій і повний Docker-стек для локального запуску.

---

## Основна логіка

### Інгест подій
`POST /events/ingest/` приймає список подій у JSON-форматі.  
Кожна подія має:
- `event_id`
- `occurred_at`
- `user_id`
- `event_type`
- `properties (JSON)`

### Асинхронність через NATS
Події публікуються у чергу **`events.ingest`**, після чого воркер асинхронно обробляє їх і записує в базу даних.  
Якщо подія з тим самим `event_id` уже існує — вона пропускається (ідемпотентність).

### Аналітика / статистика
- `/stats/dau/` — щоденна кількість унікальних користувачів (підтримує фільтри по `event type`);
- `/stats/top_event/` — топ типів подій;
- `/stats/retention/` — когортний ретеншн користувачів.

### Rate Limiting
Реалізований простий ліміт на кількість запитів із однієї IP-адреси.

### CLI-імпорт
Через `typer_app.py` можна завантажити CSV-файл історичних подій у базу даних.

---

## Технологічний стек

| Технологія | Призначення |
|-------------|--------------|
| **FastAPI** | HTTP API |
| **SQLAlchemy (async)** | ORM |
| **PostgreSQL** | Основна база даних |
| **NATS** | Брокер подій |
| **Typer** | CLI-утиліта |
| **Pytest** | Тести |
| **Docker Compose** | Контейнеризація |

---

## Команди для запуску


## 🔧 Встановлення локально (без Docker)

Клонуйте репозиторій:
```bash
git clone https://github.com/PavelSemenikhin/Semenikhin-Task.git
```

Встановіть Poetry, якщо ще не встановлено:
```bash
pip install poetry
```

Встановіть залежності:
```bash
poetry install
```

---


### Docker
```bash
docker compose up --build
```

API буде доступне за адресою:  
[http://localhost:8000/docs](http://localhost:8000/docs)

---

###  CLI-скрипт
```bash
docker compose exec app python typer_app.py import events data/events_sample.csv
```

---

###  Тести
```bash
docker compose exec app pytest -v
```

---

###  Міграції
```bash
docker compose exec app alembic revision --autogenerate
docker compose exec app alembic upgrade head
```

---

###  Логи воркера
```bash
docker logs event_worker
```

---

## Коротко про архітектуру

- **FastAPI-сервіс** приймає запити `/events/ingest` і публікує події у NATS.
- **NATS-воркер** слухає чергу `events.ingest`, обробляє події й записує їх у базу.
- **PostgreSQL** зберігає нормалізовані події з унікальним `event_id`.
- **Статистика** агрегується напряму з бази SQL-запитами через `GROUP BY`, `DISTINCT`, `COUNT`.

---

## Структура проєкту

```
app/
├── api/
│ ├── routes/
│ │ ├── init.py
│ │ ├── events.py
│ │ └── stats.py
│ ├── schemas/
│ │ ├── init.py
│ │ ├── events.py
│ │ └── stats.py
│
├── core/
│ ├── init.py
│ ├── config.py
│ ├── nats_client.py
│ └── rate_limiter.py
│
├── db/
│ ├── init.py
│ ├── base.py
│ └── models.py
│
├── tests/
│ ├── init.py
│ ├── conftest.py
│ ├── test_idemopdency.py
│ ├── test_indexing.py
│ └── test_integration.py
│
├── workers/
│ ├── init.py
│ └── ingest_worker.py
│
├── main.py
│
└── data/
└── events_sample.csv

.env
Dockerfile
.dockerignore
.gitignore
alembic.ini
ADR.md
LEARNED.md 
```

---

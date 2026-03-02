# Наступні кроки по моніторингу

1. **Перевірити локальний стек повністю**
   - Запустити `docker compose up -d --build` і переконатися, що `app`, `worker`, `prometheus`, `loki`, `grafana` (або `grafana/alloy` після заміни) піднялися без помилок (`docker compose ps` + `logs`).
   - Поглянути на `http://localhost:9090`, `http://localhost:3100`, `http://localhost:3000` — мають відповідати Prometheus, Loki, Grafana Alloy.

2. **Вивчити Grafana Alloy**
   - Відкрити Alloy, залогінитися `admin/admin` (дані з `.env`).  
   - Переглянути `Dashboards → Backend → Backend Monitoring` та Explore (Prometheus + Loki).  
   - Зафіксувати, що provisioning дашборду/джерел даних працює після заміни образа.

3. **Приступити до навчальних вправ**
   - Згенерувати кілька HTTP-запитів `curl http://localhost:8000/events`/`/stats`, переконатися, що `/metrics` змінює відлік.
   - В Explore → Loki виконати запит `({app="event_app"}) |= ""`, зберегти як панель у новому дашборді “Backend Logs”.
   - Створити пам’ятку (в цьому або окремому MD) як входити, що дивитися, які запити/фільтри використовувати.

4. **Якщо потрібна Promtail або додатковий дашборд**
   - Додати сервіс `promtail` у `docker-compose` з томами до логів та конфігом `clients.loki` → `http://loki:3100`.
   - Додати нові JSON-документи в `monitoring/grafana/dashboards/` (worker metrics, Loki logs) і переконатися, що Alloy їх імпортує при старті.

5. **document steps для Codec**
   - Перед наступною сесією зафіксувати ці дії (та інструкції по Alloy) у цьому файлі або `MONITORING_LEARNING.md`, щоби наступного разу швидко повторити.

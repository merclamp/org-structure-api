# Org Structure API

REST API для управления организационной структурой: иерархическое дерево подразделений и сотрудники внутри них.

**Стек:** Python 3.11 · FastAPI 0.136 · SQLAlchemy 2.0 (async) · PostgreSQL 16 · Alembic · Docker Compose · pytest

---

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Локальный запуск без Docker](#локальный-запуск-без-docker)
- [Структура проекта](#структура-проекта)
- [Модели данных](#модели-данных)
- [API](#api)
- [Конфигурация](#конфигурация)
- [Миграции](#миграции)
- [Тесты](#тесты)

---

## Быстрый старт

Требования: [Docker](https://docs.docker.com/get-docker/) ≥ 24 и [Docker Compose](https://docs.docker.com/compose/) ≥ 2.

```bash
# 1. Скопировать пример переменных окружения
cp .env.example .env

# 2. Собрать и запустить контейнеры
docker-compose up --build
```

После запуска:

| Адрес | Назначение |
|---|---|
| `http://localhost:8000` | REST API |
| `http://localhost:8000/docs` | Swagger UI (OpenAPI) |
| `http://localhost:8000/health` | Health check |

При старте контейнер `api` автоматически применяет все pending-миграции (`alembic upgrade head`), а затем поднимает сервер через `uvicorn`.

---

## Локальный запуск без Docker

Требования: Python 3.11+ и PostgreSQL 16.

```bash
# 1. Создать и активировать виртуальное окружение
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить переменные окружения
cp .env.example .env
# Указать POSTGRES_HOST=localhost и актуальные учётные данные

# 4. Применить миграции
alembic upgrade head

# 5. Запустить сервер
uvicorn app.main:app --reload
```

---

## Структура проекта

```
org-structure-api/
├── app/
│   ├── core/
│   │   ├── config.py        # Настройки приложения (pydantic-settings)
│   │   └── logging.py       # Конфигурация логирования
│   ├── db/
│   │   ├── base.py          # Declarative base для ORM-моделей
│   │   └── session.py       # Async-движок и фабрика сессий
│   ├── models/              # ORM-модели (SQLAlchemy)
│   └── main.py              # Точка входа: фабрика FastAPI-приложения
├── alembic/                 # Окружение Alembic и версии миграций
├── tests/                   # Тесты (pytest + pytest-asyncio)
├── .env.example             # Пример переменных окружения
├── alembic.ini              # Конфигурация Alembic
├── docker-compose.yml       # Сервисы: api + db (postgres:16-alpine)
├── Dockerfile               # Образ приложения (python:3.11-slim)
├── docker-entrypoint.sh     # Entrypoint: миграции → uvicorn
└── requirements.txt         # Зависимости
```

---

## Модели данных

### Department — подразделение

| Поле | Тип | Описание |
|---|---|---|
| `id` | int | Первичный ключ |
| `name` | str | Название (1–200 символов, уникально среди дочерних одного родителя) |
| `parent_id` | int \| null | FK на `Department`; `null` — корневой узел |
| `created_at` | datetime | Время создания |

### Employee — сотрудник

| Поле | Тип | Описание |
|---|---|---|
| `id` | int | Первичный ключ |
| `department_id` | int | FK на `Department` |
| `full_name` | str | Полное имя (1–200 символов) |
| `position` | str | Должность (1–200 символов) |
| `hired_at` | date \| null | Дата найма (опционально) |
| `created_at` | datetime | Время создания |

**Связи:** `Department` → `Employee` (1:N), `Department` → `Department` (самоссылка через `parent_id`).

---

## API

### Подразделения

#### Создать подразделение

```
POST /departments/
```

**Body:**

```json
{
  "name": "Backend",
  "parent_id": 1
}
```

`parent_id` опционален (`null` — корневой узел). Названия подразделений уникальны в пределах одного родителя.

**Response `201`:** созданное подразделение.

---

#### Получить подразделение

```
GET /departments/{id}
```

**Query-параметры:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `depth` | int | `1` | Глубина вложенных подразделений в ответе (макс. 5) |
| `include_employees` | bool | `true` | Включить список сотрудников |

**Response `200`:**

```json
{
  "id": 1,
  "name": "Engineering",
  "parent_id": null,
  "created_at": "2025-01-01T12:00:00",
  "employees": [
    {
      "id": 1,
      "full_name": "Иван Иванов",
      "position": "Team Lead",
      "hired_at": "2023-06-01",
      "created_at": "2025-01-01T12:00:00"
    }
  ],
  "children": [
    {
      "id": 2,
      "name": "Backend",
      ...
    }
  ]
}
```

---

#### Обновить / переместить подразделение

```
PATCH /departments/{id}
```

**Body** (все поля опциональны):

```json
{
  "name": "Backend Platform",
  "parent_id": 3
}
```

Нельзя сделать подразделение родителем самого себя или переместить его внутрь собственного поддерева — в этих случаях возвращается `409 Conflict`.

**Response `200`:** обновлённое подразделение.

---

#### Удалить подразделение

```
DELETE /departments/{id}
```

**Query-параметры:**

| Параметр | Тип | Описание |
|---|---|---|
| `mode` | `cascade` \| `reassign` | Стратегия удаления |
| `reassign_to_department_id` | int | Обязателен при `mode=reassign` |

- **`cascade`** — рекурсивно удалить подразделение, все дочерние подразделения и всех их сотрудников.
- **`reassign`** — удалить только само подразделение, а его сотрудников перевести в указанное подразделение (`reassign_to_department_id`).

**Response `204 No Content`.**

---

### Сотрудники

#### Создать сотрудника

```
POST /departments/{id}/employees/
```

**Body:**

```json
{
  "full_name": "Мария Петрова",
  "position": "Senior Developer",
  "hired_at": "2024-03-15"
}
```

`hired_at` опционален. Если подразделение не существует — `404 Not Found`.

**Response `201`:** созданный сотрудник.

---

### Коды ответов

| Код | Ситуация |
|---|---|
| `200` | Успех (GET, PATCH) |
| `201` | Ресурс создан (POST) |
| `204` | Удаление выполнено (DELETE) |
| `404` | Подразделение или сотрудник не найдены |
| `409` | Конфликт: цикл в дереве, дублирующееся имя |
| `422` | Ошибка валидации входных данных |

---

## Конфигурация

Все настройки задаются через переменные окружения (см. `.env.example`) и читаются классом `Settings` в `app/core/config.py`.

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DEBUG` | `false` | Режим отладки (SQL-эхо в логах) |
| `LOG_LEVEL` | `INFO` | Уровень логирования (`DEBUG`, `INFO`, `WARNING`, …) |
| `POSTGRES_HOST` | `db` | Хост PostgreSQL (`db` внутри docker-compose, `localhost` локально) |
| `POSTGRES_PORT` | `5432` | Порт PostgreSQL |
| `POSTGRES_USER` | `postgres` | Пользователь БД |
| `POSTGRES_PASSWORD` | `postgres` | Пароль БД |
| `POSTGRES_DB` | `org_structure` | Имя базы данных |

> При запуске через `docker-compose` файл `.env` читается автоматически.

---

## Миграции

Миграции управляются через [Alembic](https://alembic.sqlalchemy.org/).

```bash
# Применить все миграции (выполняется автоматически при старте контейнера)
alembic upgrade head

# Создать новую авто-миграцию
docker-compose exec api alembic revision --autogenerate -m "описание изменений"

# Откатить последнюю миграцию
docker-compose exec api alembic downgrade -1

# Проверить текущую версию схемы
docker-compose exec api alembic current
```

---

## Тесты

```bash
# Запустить все тесты внутри контейнера
docker-compose exec api pytest

# Или локально (при поднятой БД)
pytest
```

Конфигурация pytest находится в `pytest.ini`. Для асинхронных тестов используется `pytest-asyncio`, HTTP-клиент — `httpx`.

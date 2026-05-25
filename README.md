# Org Structure API

REST API для управления организационной структурой: иерархическое дерево подразделений и сотрудники внутри них.

**Стек:** Python 3.11 · FastAPI 0.136 · SQLAlchemy 2.0 (async) · asyncpg · PostgreSQL 16 · Alembic · pytest

---

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Локальный запуск без Docker](#локальный-запуск-без-docker)
- [Структура проекта](#структура-проекта)
- [Архитектура](#архитектура)
- [Модели данных](#модели-данных)
- [API](#api)
- [Бизнес-логика и ограничения](#бизнес-логика-и-ограничения)
- [Конфигурация](#конфигурация)
- [Миграции](#миграции)
- [Тесты](#тесты)

---

## Быстрый старт

Требования: [Docker](https://docs.docker.com/get-docker/) ≥ 24 и [Docker Compose](https://docs.docker.com/compose/) ≥ 2.

```bash
# 1. Скопировать переменные окружения
cp .env.example .env

# 2. Собрать и запустить
docker-compose up --build
```

После запуска:

| Адрес | Назначение |
|---|---|
| `http://localhost:8000` | REST API |
| `http://localhost:8000/docs` | Swagger UI (OpenAPI) |
| `http://localhost:8000/health` | Health check → `{"status": "ok"}` |

При старте `api`-контейнер ждёт готовности PostgreSQL (`pg_isready`), применяет миграции (`alembic upgrade head`) и запускает сервер через `uvicorn`.

---

## Локальный запуск без Docker

Требования: Python 3.11+ и PostgreSQL 16.

```bash
# 1. Создать и активировать виртуальное окружение
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить окружение
cp .env.example .env
# Изменить POSTGRES_HOST=localhost и при необходимости остальные параметры

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
│   │   ├── config.py        # Настройки через pydantic-settings
│   │   ├── exceptions.py    # Иерархия бизнес-исключений
│   │   └── logging.py       # Конфигурация логирования
│   ├── db/
│   │   ├── base.py          # DeclarativeBase + TimestampMixin
│   │   └── session.py       # Async-движок и фабрика сессий
│   ├── models/
│   │   ├── department.py    # ORM-модель Department
│   │   └── employee.py      # ORM-модель Employee
│   ├── schemas/
│   │   ├── department.py    # Pydantic-схемы: Create / Update / Read / Tree
│   │   └── employee.py      # Pydantic-схемы: Create / Read
│   ├── repositories/
│   │   ├── base.py          # BaseRepository (обёртка над AsyncSession)
│   │   ├── department.py    # DepartmentRepository
│   │   └── employee.py      # EmployeeRepository
│   ├── services/
│   │   ├── department.py    # DepartmentService — бизнес-логика
│   │   └── employee.py      # EmployeeService — бизнес-логика
│   ├── routers/
│   │   └── departments.py   # FastAPI-роутер /departments
│   └── main.py              # Фабрика FastAPI-приложения, обработчики ошибок
├── alembic/                 # Окружение Alembic и версии миграций
├── tests/
│   ├── conftest.py          # Фикстуры: TestClient, БД, очистка между тестами
│   └── test_api.py          # Интеграционные тесты
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── docker-entrypoint.sh
└── requirements.txt
```

---

## Архитектура

Проект построен по слоистой архитектуре:

```
Router  →  Service  →  Repository  →  SQLAlchemy (async)  →  PostgreSQL
```

- **Router** (`app/routers/`) — FastAPI-эндпоинты, валидация входных данных через Pydantic-схемы.
- **Service** (`app/services/`) — бизнес-логика: проверки уникальности, обнаружение циклов, оркестрация транзакций.
- **Repository** (`app/repositories/`) — инкапсуляция SQL-запросов через SQLAlchemy 2.0 (async select / update / delete).
- **Model** (`app/models/`) — ORM-модели с декларативным маппингом и `Mapped`-аннотациями.

Зависимости (DB-сессия, репозитории, сервисы) пробрасываются через FastAPI `Depends`.

---

## Модели данных

### Department — подразделение

| Поле | Тип | Описание |
|---|---|---|
| `id` | int | Первичный ключ |
| `name` | str | Название (1–200 символов) |
| `parent_id` | int \| null | FK на `Department`; `null` — корневой узел |
| `created_at` | datetime (TZ) | Время создания (server default `now()`) |

Уникальность: `(parent_id, name)` в пределах одного родителя. Для корневых узлов (`parent_id IS NULL`) тоже применяется (`postgresql_nulls_not_distinct=True`).

Каскад: при удалении подразделения все дочерние и их сотрудники удаляются на уровне БД (`ON DELETE CASCADE`) и ORM (`cascade="all, delete-orphan"`).

### Employee — сотрудник

| Поле | Тип | Описание |
|---|---|---|
| `id` | int | Первичный ключ |
| `department_id` | int | FK на `Department` (ON DELETE CASCADE) |
| `full_name` | str | Полное имя (1–200 символов) |
| `position` | str | Должность (1–200 символов) |
| `hired_at` | date \| null | Дата найма (опционально) |
| `created_at` | datetime (TZ) | Время создания |

---

## API

### `POST /departments/` — создать подразделение

**Body:**
```json
{
  "name": "Backend",
  "parent_id": 1
}
```
`parent_id` опционален (`null` — корневое подразделение). Пробелы по краям `name` обрезаются автоматически.

**Response `201`:** объект подразделения (`DepartmentRead`).

**Ошибки:** `409` — дублирующееся имя в пределах того же родителя.

---

### `GET /departments/{id}` — получить подразделение (дерево + сотрудники)

**Query-параметры:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `depth` | int | `1` | Глубина вложенных подразделений (1–5) |
| `include_employees` | bool | `true` | Включить список сотрудников |

**Response `200`:**
```json
{
  "department": {
    "id": 1,
    "name": "Engineering",
    "parent_id": null,
    "created_at": "2026-05-24T19:00:00+00:00"
  },
  "employees": [
    {
      "id": 1,
      "department_id": 1,
      "full_name": "Иван Иванов",
      "position": "Team Lead",
      "hired_at": "2023-06-01",
      "created_at": "2026-05-24T19:01:00+00:00"
    }
  ],
  "children": [
    {
      "department": { "id": 2, "name": "Backend", ... },
      "employees": [],
      "children": []
    }
  ]
}
```

Сотрудники отсортированы по `created_at`. Дочерние подразделения рекурсивно включаются до уровня `depth`.

**Ошибки:** `404` — подразделение не найдено; `400` — `depth` вне диапазона 1–5.

---

### `PATCH /departments/{id}` — обновить / переместить подразделение

**Body** (все поля опциональны):
```json
{
  "name": "Platform",
  "parent_id": 3
}
```

Чтобы сделать подразделение корневым, передайте `"parent_id": null`. Чтобы переименовать без смены родителя — передайте только `name`.

**Response `200`:** обновлённый объект (`DepartmentRead`).

**Ошибки:** `404` — подразделение не найдено; `409` — цикл в дереве или дублирующееся имя.

---

### `DELETE /departments/{id}` — удалить подразделение

**Query-параметры:**

| Параметр | Тип | Описание |
|---|---|---|
| `mode` | `cascade` \| `reassign` | Стратегия удаления |
| `reassign_to_department_id` | int | Обязателен при `mode=reassign` |

- **`cascade`** — рекурсивно удалить подразделение и все дочерние вместе со всеми их сотрудниками (через `ON DELETE CASCADE`).
- **`reassign`** — перевести сотрудников удаляемого подразделения в указанное (`reassign_to_department_id`), затем удалить само подразделение. Дочерние подразделения при этом **не** удаляются.

**Response `204 No Content`.**

**Ошибки:** `404` — подразделение или целевое подразделение не найдены; `400` — `mode=reassign` без `reassign_to_department_id`.

---

### `POST /departments/{id}/employees` — создать сотрудника

**Body:**
```json
{
  "full_name": "Мария Петрова",
  "position": "Senior Developer",
  "hired_at": "2024-03-15"
}
```
`hired_at` опционален. Пробелы в `full_name` и `position` обрезаются.

**Response `201`:** созданный сотрудник (`EmployeeRead`).

**Ошибки:** `404` — подразделение не существует; `422` — невалидное тело запроса.

---

### Коды ответов

| Код | Ситуация |
|---|---|
| `200` | Успех (GET, PATCH) |
| `201` | Ресурс создан (POST) |
| `204` | Удаление выполнено (DELETE) |
| `400` | Ошибка бизнес-валидации (пустое имя, недопустимый `depth`) |
| `404` | Подразделение или сотрудник не найдены |
| `409` | Конфликт: цикл в дереве или дублирующееся имя |
| `422` | Ошибка валидации Pydantic (неверный тип / формат данных) |

---

## Бизнес-логика и ограничения

- **Уникальность имён:** два подразделения с одинаковым именем под одним родителем запрещены (включая два корневых с одинаковым именем). Реализовано на уровне БД (`UniqueConstraint` с `postgresql_nulls_not_distinct=True`) и дублирующей проверкой в сервисе.
- **Обрезка пробелов:** поля `name`, `full_name`, `position` автоматически триммируются (`str_strip_whitespace=True` в Pydantic-схемах).
- **Обнаружение циклов:** при перемещении подразделения проверяется через рекурсивный CTE — нельзя сделать узел потомком самого себя или своего поддерева. Возвращает `409 Conflict`.
- **Глубина дерева:** параметр `depth` ограничен диапазоном 1–5 (`DepartmentService.MAX_DEPTH`).
- **Каскадное удаление** реализовано на двух уровнях: `ON DELETE CASCADE` в схеме БД и `cascade="all, delete-orphan"` в ORM-отношениях.

---

## Конфигурация

Настройки читаются классом `Settings` (`app/core/config.py`) из переменных окружения и файла `.env`.

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DEBUG` | `false` | SQL-эхо в логах |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `POSTGRES_HOST` | `db` | Хост PostgreSQL (`db` в docker-compose, `localhost` локально) |
| `POSTGRES_PORT` | `5432` | Порт PostgreSQL |
| `POSTGRES_USER` | `postgres` | Пользователь БД |
| `POSTGRES_PASSWORD` | `postgres` | Пароль БД |
| `POSTGRES_DB` | `org_structure` | Имя базы данных |

При запуске через `docker-compose` файл `.env` читается автоматически.

---

## Миграции

Миграции управляются через [Alembic](https://alembic.sqlalchemy.org/). При старте контейнера выполняется автоматически.

```bash
# Применить все миграции (автоматически при старте контейнера)
alembic upgrade head

# Создать новую авто-миграцию
docker-compose exec api alembic revision --autogenerate -m "описание"

# Откатить последнюю миграцию
docker-compose exec api alembic downgrade -1

# Проверить текущую версию
docker-compose exec api alembic current
```

---

## Тесты

Тесты — интеграционные, работают через `TestClient` (синхронный) против реальной PostgreSQL. Сессия БД поднимается один раз, между тестами таблицы очищаются.

```bash
# Запустить тесты внутри контейнера (при поднятом docker-compose)
docker-compose exec api pytest -v

# Или локально (при запущенной БД)
pytest -v
```

Конфигурация pytest — в `pytest.ini`. В тестах используется `psycopg2-binary` (синхронный драйвер) и `httpx` через `starlette.testclient`.

Покрытие тестами: health check, создание подразделений, проверка уникальности имён, валидация сотрудников, построение дерева с заданной глубиной, обнаружение циклов, удаление в режиме `reassign` и `cascade`.

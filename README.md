# Org Structure API

REST API для управления организационной структурой: дерево подразделений
и сотрудники внутри них.

Стек: **FastAPI**, **SQLAlchemy 2.0 (async)**, **PostgreSQL**, **Alembic**,
**Docker Compose**.

> Статус: проект в разработке. На текущем шаге готов каркас приложения,
> конфигурация, подключение к БД и инфраструктура (Docker, Alembic).

## Требования

- Docker и Docker Compose

(Для локального запуска без Docker — Python 3.12+ и PostgreSQL.)

## Быстрый старт

```bash
# 1. Скопировать пример переменных окружения
cp .env.example .env

# 2. Поднять БД и приложение
docker-compose up --build
```

После запуска:

- API — http://localhost:8000
- Swagger UI (OpenAPI) — http://localhost:8000/docs
- Health check — http://localhost:8000/health

## Структура проекта

```
org-structure-api/
├── app/
│   ├── core/            # конфигурация, логирование
│   │   ├── config.py
│   │   └── logging.py
│   ├── db/              # движок БД, сессии, declarative base
│   │   ├── base.py
│   │   └── session.py
│   ├── models/          # ORM-модели
│   └── main.py          # фабрика FastAPI-приложения
├── alembic/             # окружение и версии миграций
├── tests/               # тесты (pytest)
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Конфигурация

Все настройки задаются через переменные окружения (см. `.env.example`)
и читаются классом `Settings` (`app/core/config.py`).

| Переменная          | По умолчанию    | Описание                       |
|---------------------|-----------------|--------------------------------|
| `DEBUG`             | `false`         | Режим отладки (SQL-эхо)        |
| `LOG_LEVEL`         | `INFO`          | Уровень логирования            |
| `POSTGRES_HOST`     | `db`            | Хост PostgreSQL                |
| `POSTGRES_PORT`     | `5432`          | Порт PostgreSQL                |
| `POSTGRES_USER`     | `postgres`      | Пользователь БД                |
| `POSTGRES_PASSWORD` | `postgres`      | Пароль БД                      |
| `POSTGRES_DB`       | `org_structure` | Имя базы данных                |

## Миграции

При старте контейнера `api` автоматически выполняется `alembic upgrade head`.

Создать новую миграцию:

```bash
docker-compose exec api alembic revision --autogenerate -m "описание"
```

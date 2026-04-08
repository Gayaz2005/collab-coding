# Collab Coding

**Collab Coding** — это платформа для совместного онлайн-кодинга в реальном времени, которая позволяет нескольким пользователям одновременно редактировать код и безопасно выполнять его в изолированной среде.

## Ключевые возможности

- **Real-time синхронизация**: Обновление в реальном времени кода у всех участников комнаты с сохранением позиции курсора через WebSocket
- **Безопасное выполнение кода**: Изолированная среда выполнения на основе nsjail в Docker с ограничением ресурсов
- **Хранение данных**: PostgreSQL для метаданных, Redis для активных данных, MinIO для архивации с версионированием
- **Docker-контейнеризация**: Полная инфраструктура из 5 сервисов с healthcheck'ами

## Технологии

- **Backend**: Python 3.11, FastAPI, WebSocket, SQLAlchemy 2.0, Pydantic
- **Базы данных**: PostgreSQL (метаданные), Redis (кэш, активные комнаты)
- **Хранилище**: MinIO (S3-совместимое, версионирование)
- **Безопасность**: nsjail (изоляция кода в Docker-контейнере)
- **Инфраструктура**: Docker, Docker Compose

## Хранение данных

- PostgreSQL: метаданные комнат (id, название, язык, даты)
- Redis: активные комнаты, участники, текущий код (TTL 1 час)
- MinIO: архив кода с версионированием (сохраняется при выходе последнего участника)

## Быстрый старт

### Требования

- Docker и Docker Compose
- Python 3.11
- Poetry

### Инфраструктура

Запуск всех сервисов:

```bash
docker-compose up -d
```

Сервисы будут доступны по портам:
- PostgreSQL: 5432
- Redis: 6379
- MinIO API: 9000, Console: 9001
- pgAdmin: 8080

### Приложение

Установка зависимостей:

```bash
poetry install
```

Запуск сервера:

```bash
uvicorn src.collab_coding.server:app --reload
```

Приложение будет доступно по адресу: `http://localhost:8000`

Swagger UI документация: `http://localhost:8000/docs`

### Сборка образа для изоляции

```bash
docker build -f sandbox/nsjail.Dockerfile -t nsjail sandbox/
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/rooms` | Создание комнаты |
| GET | `/rooms` | Список активных комнат |
| GET | `/rooms/{id}` | Получение комнаты по ID |
| DELETE | `/rooms/{id}` | Удаление комнаты |
| PUT | `/rooms/{id}/code` | Обновление кода |
| GET | `/rooms/{id}/code` | Получение кода |
| POST | `/rooms/{id}/run` | Выполнение кода |
| WS | `/ws/{id}` | WebSocket соединение |
| GET | `/health` | Health check |

## Структура проекта

```
collab-coding/
├── src/
│   └── collab_coding/
│       ├── server.py          # FastAPI приложение
│       ├── settings.py        # Конфигурация
│       ├── models.py          # Pydantic модели
│       ├── models_db.py       # SQLAlchemy модели
│       ├── database.py        # Подключение к БД
│       ├── storage.py         # CRUD операции
│       ├── redis_client.py    # Redis клиент
│       ├── minio_client.py    # MinIO клиент
│       ├── websocket.py       # WebSocket менеджер
│       ├── executor.py        # Выполнение кода
│       └── static/            # Фронтенд файлы
├── sandbox/
│   ├── nsjail.Dockerfile
│   └── nsjail.cfg
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── README.md
```

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

Основные переменные:

```ini
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=collab

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=collab-files
```

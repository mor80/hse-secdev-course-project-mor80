# Wishlist - HSE SecDev 2025

[![CI](https://github.com/mor80/hse-secdev-course-project-mor80/actions/workflows/ci.yml/badge.svg)](https://github.com/mor80/hse-secdev-course-project-mor80/actions/workflows/ci.yml)

Full-stack Wishlist приложение с безопасным API и современным React фронтендом.

## Особенности

### Backend (FastAPI)

- **Async/Await** - полная поддержка асинхронности (FastAPI + asyncpg + async SQLAlchemy)
- **PostgreSQL** - production-ready БД с миграциями (Alembic)
- **Authentication** - JWT tokens с безопасным хешированием паролей (bcrypt)
- **Authorization** - role-based access control (user/admin)
- **Structured Errors** - единый формат ошибок с кодами и деталями
- __Request Logging__ - каждый запрос логируется с уникальным request_id
- **Comprehensive Tests** - async тесты с полным покрытием

### Frontend (React)

- **Modern Stack** - React 18 + TypeScript + Vite
- **Beautiful UI** - Tailwind CSS с responsive design
- **State Management** - React Query для эффективного data fetching
- **Form Handling** - React Hook Form с валидацией
- **Type-Safe** - полное покрытие TypeScript типами

## Быстрый старт

### Вариант 1: Запуск через Docker (рекомендуется)

```bash
# Собрать и запустить все сервисы
docker compose up -d --build

# В отдельном терминале создать admin пользователя
docker compose exec app python create_admin.py
```

Доступ к сервисам:

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **Swagger**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (admin@admin.com / admin123)

### Вариант 2: Локальная разработка

#### 1. Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

#### 2. Настройка окружения

```bash
# Создать .env файл
chmod +x setup_env.sh
./setup_env.sh

# Или создать вручную
cat > .env << 'EOF'
APP_NAME=Wishlist API
ENV=local
DEBUG=False
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql+asyncpg://wishlist_user:wishlist_pass@localhost:5432/wishlist_db
POSTGRES_DB=wishlist_db
POSTGRES_USER=wishlist_user
POSTGRES_PASSWORD=wishlist_pass
CORS_ORIGINS=
EOF
```

#### 3. Запуск PostgreSQL

```bash
# Используя Docker
docker compose up -d db

# Или установите PostgreSQL локально и создайте БД
createdb wishlist_db
```

#### 4. Применить миграции

```bash
alembic upgrade head
```

#### 5. Создать admin пользователя

```bash
python create_admin.py
```

#### 6. Запустить backend сервер

```bash
uvicorn app.main:app --reload
```

API будет доступен на `http://localhost:8000`

#### 7. Запустить frontend (в отдельном терминале)

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

Frontend доступен на `http://localhost:3000`
Документация: `http://localhost:8000/docs`

## Makefile команды

Для удобства можно использовать Makefile:

```bash
make help          # Показать все команды
make setup         # Первичная настройка проекта
make install       # Установить зависимости
make env           # Создать .env файл
make dev           # Запустить dev сервер
make test          # Запустить тесты
make lint          # Проверить код
make format        # Отформатировать код
make docker-up     # Запустить в Docker
make docker-down   # Остановить Docker
make create-admin  # Создать admin пользователя
```

## Тесты

```bash
# Локально
make test
# или
pytest -v
pytest --cov=app tests/

# В Docker
make docker-test
# или
docker compose -f docker-compose.test.yaml up --build
```

## Ритуал перед PR

```bash
make format
make lint
make test
pre-commit run --all-files
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - регистрация нового пользователя
- `POST /api/v1/auth/login` - логин (получение JWT токена)
- `GET /api/v1/auth/me` - информация о текущем пользователе

### Admin (требуется роль admin)

- `GET /api/v1/admin/users` - получить список всех пользователей

### Wishes (требуется аутентификация)

- `POST /api/v1/wishes/` - создать wish
- `GET /api/v1/wishes/` - получить список wishes (с пагинацией и фильтрацией)
- `GET /api/v1/wishes/{id}` - получить конкретный wish
- `PATCH /api/v1/wishes/{id}` - обновить wish
- `DELETE /api/v1/wishes/{id}` - удалить wish

### Query Parameters

- `limit` - лимит записей (1-100, по умолчанию 10)
- `offset` - смещение для пагинации (по умолчанию 0)
- `price_filter` - фильтр по максимальной цене

### Health Check

- `GET /health` - проверка работоспособности
- `GET /` - информация об API

## Роли

### User (по умолчанию)

- Может создавать/читать/обновлять/удалять только свои wishes
- Получает только свои wishes в списке

### Admin

- Может просматривать все wishes всех пользователей
- Может обновлять/удалять любые wishes
- Полный доступ ко всем ресурсам

## Формат ошибок

Все ошибки возвращаются в едином формате:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "details": {}
}
```

---

## Требования Безопасности

| Категория          | Требование                                                                | Как реализовано |
|--------------------|---------------------------------------------------------------------------|-----------------|
| Аутентификация     | Минимальная длина пароля — 6 символов.                                    | В схеме регистрации проверка через `pydantic.Field(min_length=6)`. |
| Сессии             | Время жизни access-токена не более 15 минут, refresh-токена — до 30 минут; поддерживается завершение сессии. | Конфиги: `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_MINUTES=30`; при logout токены аннулируются. |
| Ошибки/ответы      | Сообщения об ошибках единообразные; код возврата 401 или 403 без уточнений. | Все исключения маппятся на `HTTPException` с единым JSON-ответом. |
| Секреты            | Ключи и пароли не хранятся в коде, только в переменных окружения.          | Используются `.env` и GitHub Secrets, pre-commit следит за отсутствием ключей. |
| Логи и аудит       | Фиксируются все HTTP-запросы и действия с сущностями (создание, удаление, экспорт). | Uvicorn пишет access-логи, дополнительно пишем audit-события CRUD. |
| Приватность/данные | В БД остаётся только необходимая информация (title, link, price, notes, category, owner_id). | Модели минимальны, чувствительные данные не собираются, удалённые записи стираются окончательно. |


См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
### Коды ошибок

- `VALIDATION_ERROR` (422) - ошибка валидации данных
- `AUTHENTICATION_ERROR` (401) - ошибка аутентификации
- `AUTHORIZATION_ERROR` (403) - недостаточно прав
- `NOT_FOUND` (404) - ресурс не найден
- `DUPLICATE_ERROR` (409) - дубликат ресурса
- `BAD_REQUEST` (400) - некорректный запрос
- `INTERNAL_ERROR` (500) - внутренняя ошибка сервера

## Структура проекта

```rb
app/
  adapters/
    repositories/       # Data access layer
    database.py        # Database connection
  api/
    v1/                # API version 1 endpoints
    dependencies.py    # Auth dependencies
    middleware.py      # Request logging
  domain/
    entities.py        # SQLAlchemy models
    models.py          # Pydantic schemas
    exceptions.py      # Custom exceptions
  services/
    auth_service.py    # Authentication logic
  config.py            # Configuration
  main.py              # FastAPI app
tests/
  conftest.py          # Test fixtures
  test_*.py            # Test files
migrations/            # Alembic migrations
```

## Security

Проект следует best practices безопасности:

- Пароли хешируются с использованием bcrypt
- JWT токены с настраиваемым временем жизни
- Owner-only access control для resources
- SQL injection защита через SQLAlchemy ORM
- Валидация всех входных данных через Pydantic
- CORS настройки
- Request logging с request_id для трейсинга

См. также: `SECURITY.md`

## CI/CD

В репозитории настроен GitHub Actions workflow для автоматического тестирования и проверки кода.

## License

HSE SecDev 2025 Course Project

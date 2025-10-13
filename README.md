# Wishlist — сервис желаемых вещей

Учебный проект курса **HSE SecDev 2025**.
Задача — спроектировать и реализовать веб-сервис с безопасной архитектурой, валидацией данных, тестами и CI/CD.

---

## Цели проекта
- Освоить базовые практики **безопасной разработки** (валидация, owner-only доступ, секреты вне кода).
- Настроить **гигиену репозитория** (pre-commit, линтеры, CI).
- Реализовать минимальный **MVP сервиса**:
  - хранение «желаний» пользователя (CRUD),
  - аутентификация и разграничение прав,
  - фильтры, сортировки, экспорт,
  - корректная обработка ошибок.

---

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
uvicorn app.main:app --reload
```

---

## Ритуал перед PR
```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

---

## Тесты
```bash
pytest -q
```

---

## CI
В репозитории настроен workflow **CI** (GitHub Actions) — required check для `main`.
Badge добавится автоматически после загрузки шаблона в GitHub.

---

## Контейнеры
```bash
docker build -t secdev-app .
docker run --rm -p 8000:8000 secdev-app
# или
docker compose up --build
```

---

## Эндпойнты
- `GET /health` → `{"status": "ok"}`
- `POST /wishes?name=...` — создать сущность
- `GET /wishes/{id}` — получить по id
- `GET /wishes` — список с фильтрами
- `PATCH /wishes/{id}` — обновить
- `DELETE /wishes/{id}` — удалить
- `GET /wishes/export.csv` — экспорт в CSV

---

## Формат ошибок
Все ошибки — JSON-обёртка:
```json
{
  "error": {"code": "not_found", "message": "item not found"}
}
```

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.

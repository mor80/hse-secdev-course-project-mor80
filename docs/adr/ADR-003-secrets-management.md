# ADR-003: Secrets Management

**Дата**: 2025-01-22
**Статус**: Accepted
**Автор**: Development Team

## Context

Текущее управление секретами имеет проблемы:
- Секреты в переменных окружения без ротации
- Отсутствие валидации силы секретов
- Нет разделения секретов по средам
- Отсутствие аудита доступа к секретам
- Потенциальная утечка в логах

**Текущие секреты**:
- `SECRET_KEY` для JWT подписи
- `DATABASE_URL` с паролем БД
- `PGADMIN_DEFAULT_PASSWORD`

**Угрозы**:
- Слабые секреты (brute force)
- Отсутствие ротации (long-term exposure)
- Утечка в логах/исключениях
- Hardcoded секреты в коде

## Decision

Внедрить централизованное управление секретами с автоматической ротацией и валидацией.

**Архитектура секретов**:

1. **Secret Strength Validation**:
   - Минимум 32 символа для SECRET_KEY
   - Сложность паролей БД
   - Валидация при старте приложения

2. **Rotation Strategy**:
   - Автоматическая ротация SECRET_KEY (ежемесячно)
   - Graceful transition для JWT токенов
   - Уведомления о ротации

3. **Environment Separation**:
   - Разные секреты для dev/staging/prod
   - Валидация соответствия среды
   - Запрет prod секретов в dev

4. **Logging Protection**:
   - Маскирование секретов в логах
   - Sanitization исключений
   - Аудит доступа к секретам

**Параметры**:
```python
SECRET_KEY_MIN_LENGTH = 32
ROTATION_INTERVAL_DAYS = 30
MASKED_SECRET = "***REDACTED***"
```

## Consequences

**Плюсы**:
- ✅ Автоматическая ротация секретов
- ✅ Валидация силы секретов
- ✅ Защита от утечек в логах
- ✅ Разделение по средам

**Минусы**:
- ⚠️ Сложность ротации без downtime
- ⚠️ Дополнительная валидация при старте
- ⚠️ Необходимость обновления deployment

**Компромиссы**:
- Graceful ротация (без прерывания сервиса)
- Валидация только критичных секретов
- Постепенное внедрение (не все сразу)

## Implementation

1. Создать `app/services/secrets_service.py`
2. Добавить валидацию силы секретов в `app/config.py`
3. Реализовать маскирование в логах
4. Добавить rotation endpoint для админов
5. Создать middleware для sanitization

## Links

- **NFR-05** (Security): Ротация секретов и защита от утечек
- **NFR-06** (Audit): Логирование доступа к секретам
- **F19** (Threat Model): SECRET_KEY access
- **R4, R5** (Risk Register): Secret exposure и weak secrets
- **Tests**: `tests/test_secrets.py::test_secret_validation`
- **Closure Criteria**: Все секреты проходят валидацию, ротация работает, утечки в логах заблокированы

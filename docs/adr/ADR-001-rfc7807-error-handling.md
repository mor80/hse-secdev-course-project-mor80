# ADR-001: RFC 7807 Error Handling

**Дата**: 2025-01-22
**Статус**: Accepted
**Автор**: Development Team

## Context

В текущей реализации API ошибки возвращаются в различных форматах:
- FastAPI автоматические ошибки валидации (422)
- Кастомные исключения без стандартизации
- Отсутствие correlation_id для трейсинга
- Утечка внутренних деталей в production

**Проблемы**:
- Клиенты не могут единообразно обрабатывать ошибки
- Сложность отладки в production
- Отсутствие трейсинга запросов
- Потенциальная утечка чувствительной информации

## Decision

Внедрить RFC 7807 Problem Details for HTTP APIs для стандартизации всех ошибок API.

**Стандартный формат ошибки**:
```json
{
  "type": "https://api.wishlist.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Password must be at least 8 characters long",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "instance": "/api/v1/auth/register"
}
```

**Параметры**:
- Все ошибки возвращают correlation_id (UUID4)
- Production режим маскирует детали ошибок
- Типы ошибок следуют URI схеме
- Статус коды соответствуют HTTP стандартам

## Consequences

**Плюсы**:
- ✅ Стандартизированный формат ошибок
- ✅ Улучшенная отладка с correlation_id
- ✅ Безопасность в production (маскирование)
- ✅ Лучший UX для клиентов

**Минусы**:
- ⚠️ Дополнительная сложность в коде
- ⚠️ Увеличение размера ответов
- ⚠️ Необходимость обновления клиентов

**Компромиссы**:
- Добавлен middleware для автоматической обработки
- Сохранена обратная совместимость для существующих клиентов
- Логирование correlation_id для мониторинга

## Implementation

1. Создать `app/api/error_handler.py` с RFC 7807 форматированием
2. Добавить middleware для автоматической обработки исключений
3. Обновить все endpoints для использования стандартного формата
4. Добавить маскирование в production режиме

## Links

- **NFR-03** (Error Handling): Стандартизированные ошибки с correlation_id
- **NFR-05** (Security): Маскирование чувствительной информации
- **F11, F12** (Threat Model): JWT validation errors
- **R2** (Risk Register): Information disclosure через ошибки
- **Tests**: `tests/test_errors.py::test_rfc7807_contract`
- **Closure Criteria**: Все API endpoints возвращают RFC 7807 формат, тесты покрывают негативные сценарии

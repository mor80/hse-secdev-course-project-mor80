# ADR-002: Input Validation & File Upload Security

**Дата**: 2025-01-22
**Статус**: Accepted
**Автор**: Development Team

## Context

Текущая система не поддерживает загрузку файлов, но планируется добавление функциональности для:
- Аватаров пользователей
- Изображений желаний
- Документов/скриншотов

**Угрозы без защиты**:
- Path traversal атаки (`../../../etc/passwd`)
- Загрузка вредоносных файлов
- DoS через большие файлы
- MIME type spoofing
- Symlink атаки

**Требования безопасности**:
- Валидация magic bytes (не только MIME)
- Ограничения размера файлов
- Канонизация путей
- UUID имена файлов
- Запрет symlinks

## Decision

Реализовать безопасную систему загрузки файлов с многоуровневой защитой.

**Архитектура безопасности**:

1. **Magic Bytes Validation**:
   - Проверка сигнатур файлов (PNG, JPEG)
   - Игнорирование MIME type от клиента
   - Поддержка только безопасных типов

2. **Path Security**:
   - UUID имена файлов (предотвращение угадывания)
   - Канонизация путей (предотвращение traversal)
   - Запрет symlinks в родительских директориях
   - Chroot-подобная изоляция

3. **Size & Rate Limits**:
   - Максимум 5MB на файл
   - Rate limiting на загрузки
   - Таймауты обработки

**Параметры**:
```python
MAX_FILE_SIZE = 5_000_000  # 5MB
ALLOWED_TYPES = {"image/png", "image/jpeg"}
UPLOAD_DIR = "/app/uploads"  # Изолированная директория
```

## Consequences

**Плюсы**:
- ✅ Защита от path traversal
- ✅ Предотвращение загрузки вредоносных файлов
- ✅ DoS защита через лимиты
- ✅ UUID имена предотвращают угадывание

**Минусы**:
- ⚠️ Дополнительная сложность валидации
- ⚠️ Overhead на проверку magic bytes
- ⚠️ Ограничения на типы файлов

**Компромиссы**:
- Только изображения для MVP (безопасность > функциональность)
- UUID имена (безопасность > читаемость)
- Строгие лимиты (безопасность > удобство)

## Implementation

1. Создать `app/services/file_service.py` с безопасной загрузкой
2. Добавить magic bytes detection
3. Реализовать path canonicalization
4. Добавить rate limiting для uploads
5. Создать endpoint `/api/v1/upload/avatar`

## Links

- **NFR-01** (Input Validation): Строгая валидация всех входных данных
- **NFR-02** (File Upload Security): Безопасная загрузка файлов
- **F3, F4** (Threat Model): User upload flows
- **R1, R3** (Risk Register): Path traversal и malicious uploads
- **Tests**: `tests/test_file_upload.py::test_security_validation`
- **Closure Criteria**: Все файлы проходят magic bytes проверку, path traversal заблокирован, тесты покрывают негативные сценарии

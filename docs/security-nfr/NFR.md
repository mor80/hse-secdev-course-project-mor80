# Security Non-Functional Requirements (NFR)

## Проект: Wishlist API

### Цель документа
Определение измеримых требований безопасности и производительности для Wishlist API, обеспечивающих защиту пользовательских данных, доступность сервиса и соответствие лучшим практикам безопасности.

---

## Таблица NFR

| ID     | Название                          | Описание                                                                 | Метрика/Порог                              | Проверка (чем/где)                    | Компонент      | Приоритет |
|--------|-----------------------------------|--------------------------------------------------------------------------|-------------------------------------------|---------------------------------------|----------------|-----------|
| NFR-01 | Хранение паролей                  | Использование bcrypt для хеширования паролей с ограничением 72 символа   | bcrypt rounds ≥ 12, max 72 chars          | Unit-тесты + code review              | auth_service   | Critical  |
| NFR-02 | Структурированные ошибки          | Все API errors в формате RFC 7807 без утечки PII/stack traces           | 100% endpoints с structured errors        | Contract tests + E2E                  | api middleware | High      |
| NFR-03 | Производительность /login         | Время ответа p95 для логина при нормальной нагрузке                     | p95 ≤ 500ms @ 50 RPS                      | Load testing (k6/locust)              | auth endpoint  | High      |
| NFR-04 | Производительность /wishes        | Время ответа p95 для CRUD операций с wishes                              | p95 ≤ 300ms @ 100 RPS                     | Load testing + monitoring             | wishes API     | High      |
| NFR-05 | Уязвимости зависимостей           | Максимальное время исправления критичных уязвимостей                     | High/Critical ≤ 7 дней                    | CI: safety/pip-audit/dependabot       | dependencies   | Critical  |
| NFR-06 | JWT токены                        | Срок жизни и алгоритм подписи JWT токенов                                | TTL = 30 min, алг = HS256, min 256 bit    | Config validation + integration tests | auth_service   | High      |
| NFR-07 | Rate Limiting                     | Ограничение запросов для защиты от brute-force и DoS                    | /login: 5 req/min, /api: 100 req/min      | E2E tests + monitoring                | middleware     | High      |
| NFR-08 | SQL Injection защита              | Использование параметризованных запросов через ORM                       | 100% queries через SQLAlchemy ORM         | Code review + SAST                    | repositories   | Critical  |
| NFR-09 | CORS политика                     | Строгая настройка CORS для production                                    | Только whitelisted origins                | Config tests + security scan          | main.py        | High      |
| NFR-10 | Request ID трассировка            | Все запросы логируются с уникальным request_id                           | 100% requests with X-Request-ID           | Integration tests + logs audit        | middleware     | Medium    |
| NFR-11 | HTTPS только                      | Все соединения через TLS 1.2+                                            | TLS 1.2+, HSTS enabled                    | SSL Labs scan + deployment check      | infrastructure | Critical  |
| NFR-12 | Ротация секретов                  | Регулярная ротация SECRET_KEY и database credentials                    | Ротация каждые 90 дней                   | Vault/KMS policy + runbook            | config         | Medium    |

---

## Детальное описание приоритетных NFR

### NFR-01: Хранение паролей (Critical)
**Обоснование**: Утечка паролей — наиболее критичная уязвимость, ведущая к компрометации учетных записей.

**Технические требования**:
- Использование bcrypt с cost factor ≥ 12
- Ограничение длины пароля до 72 символов (ограничение bcrypt)
- Запрет на хранение паролей в plaintext
- Валидация минимальной длины: 8 символов

**Реализация**: `app/services/auth_service.py`
```python
def get_password_hash(password: str) -> str:
    password_bytes = password[:72].encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')
```

---

### NFR-02: Структурированные ошибки (High)
**Обоснование**: Утечка stack traces и внутренней информации помогает атакующим в разведке системы.

**Технические требования**:
- Формат ответа: `{code, message, details}`
- Маскирование PII в логах и ошибках
- Correlation ID (request_id) в каждом ответе
- HTTP статусы соответствуют RFC 7231

**Примеры кодов**: `VALIDATION_ERROR`, `AUTHENTICATION_ERROR`, `AUTHORIZATION_ERROR`, `NOT_FOUND`, `INTERNAL_ERROR`

---

### NFR-03: Производительность /login (High)
**Обоснование**: Медленный логин ухудшает UX и может быть вектором DoS атак.

**Технические требования**:
- p95 ≤ 500ms при 50 RPS
- p99 ≤ 1s при 50 RPS
- Без деградации при 100 RPS в течение 5 минут
- Async обработка запросов

**Мониторинг**: Prometheus + Grafana с алертами на превышение порогов

---

### NFR-05: Уязвимости зависимостей (Critical)
**Обоснование**: Уязвимые зависимости — частая причина компрометации приложений.

**Технические требования**:
- SBOM генерируется при каждом билде
- CI проверка на High/Critical CVE (fail on detection)
- SLA на исправление: Critical ≤ 3 дня, High ≤ 7 дней
- Automated PR для security updates (Dependabot)

**Инструменты**: `pip-audit`, `safety`, GitHub Dependabot

---

### NFR-07: Rate Limiting (High)
**Обоснование**: Защита от brute-force атак на /login и DoS на API.

**Технические требования**:
- `/api/v1/auth/login`: 5 попыток в минуту с IP
- `/api/v1/auth/register`: 3 попытки в 5 минут с IP
- `/api/v1/**`: 100 запросов в минуту на пользователя
- 429 Too Many Requests при превышении

**Реализация**: SlowAPI/FastAPI middleware с Redis backend

---

### NFR-08: SQL Injection защита (Critical)
**Обоснование**: SQL Injection входит в OWASP Top 10 и ведет к полной компрометации данных.

**Технические требования**:
- 100% queries через SQLAlchemy ORM
- Запрет на raw SQL без review
- Prepared statements для всех динамических запросов
- SAST проверка в CI

**Валидация**: Semgrep/Bandit rules + code review checklist

---

## Связь с безопасностью

### STRIDE анализ покрытия
- **Spoofing**: NFR-01, NFR-06 (хеширование паролей, JWT)
- **Tampering**: NFR-08 (SQL Injection защита)
- **Repudiation**: NFR-10 (request ID трассировка)
- **Information Disclosure**: NFR-02, NFR-11 (structured errors, HTTPS)
- **Denial of Service**: NFR-03, NFR-04, NFR-07 (performance, rate limiting)
- **Elevation of Privilege**: NFR-06, NFR-09 (JWT validation, CORS)

### Compliance
- **GDPR**: NFR-02 (маскирование PII), NFR-12 (безопасное хранение секретов)
- **OWASP Top 10 2021**:
  - A02:2021 - Cryptographic Failures → NFR-01, NFR-11
  - A03:2021 - Injection → NFR-08
  - A07:2021 - Identification and Authentication Failures → NFR-01, NFR-06, NFR-07

---

## Мониторинг и алертинг

### Метрики для отслеживания
1. Response times (p50, p95, p99) для всех endpoints
2. Error rates (4xx, 5xx) по типам
3. Authentication failures rate
4. Rate limiting triggers
5. CVE count по severity

### Алерты
- **Critical**: p95 > порога на 30%, CVE Critical detected, error rate > 5%
- **High**: p95 > порога на 15%, rate limiting triggers > 100/min
- **Medium**: JWT expiration warnings, secret rotation due date

---

## Roadmap внедрения

### Phase 1 (P03): Документация и проектирование
- ✅ Определение NFR
- ✅ BDD сценарии
- ✅ Трассировка на backlog

### Phase 2 (P04-P05): Реализация критичных NFR
- [ ] NFR-01: Улучшение bcrypt (rounds=12)
- [ ] NFR-07: Rate limiting middleware
- [ ] NFR-05: Automated dependency scanning в CI

### Phase 3 (P06-P07): Мониторинг и тестирование
- [ ] Load testing инфраструктура
- [ ] Prometheus + Grafana дашборды
- [ ] Alerting rules

### Phase 4 (P08+): Оптимизация и hardening
- [ ] Secret management (Vault)
- [ ] Advanced threat detection
- [ ] Incident response playbooks

---

**Владелец документа**: Security Team
**Последнее обновление**: 2025-10-13
**Версия**: 1.0

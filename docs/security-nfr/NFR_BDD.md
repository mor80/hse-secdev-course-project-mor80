# NFR BDD Scenarios (Gherkin)

## Цель документа
Определение приемочных сценариев для проверки соответствия Non-Functional Requirements в стиле Behavior-Driven Development.

---

## Feature 1: Хранение паролей (NFR-01)

### Scenario 1.1: Безопасное хеширование пароля при регистрации
```gherkin
Feature: Безопасное хранение паролей
  Как система
  Я хочу хешировать пароли с использованием bcrypt
  Чтобы защитить учетные данные пользователей от утечек

  Scenario: Успешное хеширование пароля при регистрации
    Given новый пользователь с email "user@example.com"
    And паролем длиной 12 символов
    When отправляется POST /api/v1/auth/register
    Then пароль хешируется с использованием bcrypt
    And bcrypt cost factor >= 12
    And в БД хранится только hash, не plaintext
    And hash начинается с "$2b$" (bcrypt prefix)

  Scenario: Отклонение слишком длинного пароля
    Given новый пользователь с email "user@example.com"
    And паролем длиной 80 символов
    When отправляется POST /api/v1/auth/register
    Then пароль автоматически обрезается до 72 символов
    And хеширование выполняется успешно
    And пользователь создается без ошибок
```

---

## Feature 2: Структурированные ошибки (NFR-02)

### Scenario 2.1: Формат ошибок соответствует стандарту
```gherkin
Feature: Структурированные ошибки API
  Как разработчик клиента
  Я хочу получать ошибки в едином формате
  Чтобы единообразно обрабатывать их на фронтенде

  Scenario: Ошибка валидации возвращает структурированный ответ
    Given неавторизованный пользователь
    When отправляется POST /api/v1/auth/register с невалидным email
    Then HTTP статус = 422 Unprocessable Entity
    And response содержит поле "code" = "VALIDATION_ERROR"
    And response содержит поле "message" (human-readable)
    And response содержит поле "details" с описанием ошибок
    And response НЕ содержит stack trace
    And response НЕ содержит внутренние пути файлов

  Scenario: Внутренняя ошибка маскируется
    Given авторизованный пользователь
    And в системе произошла необработанная ошибка
    When отправляется GET /api/v1/wishes/123
    Then HTTP статус = 500 Internal Server Error
    And response содержит "code" = "INTERNAL_ERROR"
    And response содержит generic "message"
    And response НЕ содержит stack trace
    And ошибка залогирована с request_id
```

---

## Feature 3: Производительность /login (NFR-03)

### Scenario 3.1: Время ответа при нормальной нагрузке
```gherkin
Feature: Производительность аутентификации
  Как пользователь
  Я хочу быстро авторизоваться
  Чтобы получить доступ к своим данным без задержек

  Background:
    Given сервис развернут на staging окружении
    And база данных содержит 1000 активных пользователей

  Scenario: p95 времени ответа /login при 50 RPS
    Given выполняется нагрузочный тест
    And RPS = 50 запросов в секунду
    And длительность теста = 5 минут
    When запрашивается POST /api/v1/auth/login с валидными credentials
    Then p95 времени ответа <= 500 ms
    And p99 времени ответа <= 1000 ms
    And error rate < 0.1%

  Scenario: Деградация производительности при повышенной нагрузке
    Given выполняется нагрузочный тест
    And RPS постепенно увеличивается от 50 до 150
    When достигается 100 RPS
    Then p95 времени ответа <= 800 ms
    And сервис НЕ возвращает 5xx ошибки
    When достигается 150 RPS
    Then сервис отвечает rate limiting (429) для excess запросов
    And p95 для успешных запросов <= 1000 ms
```

---

## Feature 4: Производительность /wishes CRUD (NFR-04)

### Scenario 4.1: Быстрый доступ к списку wishes
```gherkin
Feature: Производительность операций с wishes
  Как пользователь
  Я хочу быстро получать свой список желаний
  Чтобы эффективно работать с приложением

  Background:
    Given в системе 500 пользователей
    And у каждого пользователя в среднем 20 wishes

  Scenario: p95 для GET /wishes с пагинацией
    Given выполняется нагрузочный тест
    And RPS = 100 запросов в секунду
    And запросы распределены между пользователями
    When запрашивается GET /api/v1/wishes?limit=10&offset=0
    Then p95 времени ответа <= 300 ms
    And p99 времени ответа <= 500 ms
    And каждый запрос возвращает только wishes владельца

  Scenario: Производительность создания wish
    Given авторизованный пользователь
    And выполняется серия POST запросов
    When создается новый wish через POST /api/v1/wishes
    Then p95 времени ответа <= 250 ms
    And wish сохраняется в БД корректно
    And owner_id устанавливается из JWT токена
```

---

## Feature 5: Rate Limiting (NFR-07)

### Scenario 5.1: Защита от brute-force на /login
```gherkin
Feature: Rate limiting для защиты от атак
  Как система
  Я хочу ограничивать частоту запросов
  Чтобы предотвратить brute-force и DoS атаки

  Scenario: Блокировка после превышения лимита логина
    Given неавторизованный клиент с IP 192.168.1.100
    When отправляется 5 POST /api/v1/auth/login запросов за 60 секунд
    Then все 5 запросов обрабатываются нормально
    When отправляется 6-й POST /api/v1/auth/login
    Then HTTP статус = 429 Too Many Requests
    And response содержит "code" = "RATE_LIMIT_EXCEEDED"
    And response содержит header "Retry-After" с временем в секундах
    And запрос логируется как potential brute-force attempt

  Scenario: Rate limit сбрасывается после временного окна
    Given клиент был заблокирован rate limiter
    When проходит 60 секунд
    And отправляется новый POST /api/v1/auth/login
    Then запрос обрабатывается успешно
    And rate limit counter сброшен
```

---

## Feature 6: SQL Injection защита (NFR-08)

### Scenario 6.1: Безопасная обработка пользовательского ввода
```gherkin
Feature: Защита от SQL Injection
  Как система
  Я хочу безопасно обрабатывать пользовательский ввод
  Чтобы предотвратить SQL Injection атаки

  Scenario: Попытка SQL Injection в поиске wishes
    Given авторизованный пользователь
    And malicious payload: "1' OR '1'='1"
    When отправляется GET /api/v1/wishes?price_filter=1' OR '1'='1
    Then запрос обрабатывается через SQLAlchemy ORM
    And SQL injection НЕ выполняется
    And возвращается либо пустой результат, либо validation error
    And попытка логируется в security log

  Scenario: Безопасное создание wish с специальными символами
    Given авторизованный пользователь
    And title содержит: "Book: 'Python & SQL'"
    When отправляется POST /api/v1/wishes с этим title
    Then wish создается успешно
    And title сохраняется в БД корректно
    And специальные символы экранированы автоматически
    And при чтении wish title возвращается без изменений
```

---

## Негативные сценарии

### Negative Scenario 1: Отказоустойчивость при недоступности БД
```gherkin
Feature: Graceful degradation при сбоях
  Как система
  Я хочу корректно обрабатывать сбои зависимостей
  Чтобы не утекать чувствительную информацию об инфраструктуре

  Scenario: База данных недоступна
    Given PostgreSQL не отвечает на запросы
    When отправляется любой API запрос, требующий БД
    Then HTTP статус = 503 Service Unavailable
    And response содержит "code" = "SERVICE_UNAVAILABLE"
    And response НЕ содержит database connection string
    And response НЕ содержит внутренние ошибки PostgreSQL
    And алерт отправляется в мониторинг
    And request_id логируется для troubleshooting
```

### Negative Scenario 2: Невалидный JWT токен
```gherkin
Feature: Защита от подделки JWT
  Как система
  Я хочу отклонять невалидные JWT токены
  Чтобы предотвратить несанкционированный доступ

  Scenario: Expired JWT токен
    Given пользователь был авторизован 35 минут назад
    And JWT TTL = 30 минут
    When отправляется GET /api/v1/wishes с expired токеном
    Then HTTP статус = 401 Unauthorized
    And response содержит "code" = "TOKEN_EXPIRED"
    And пользователь должен re-authenticate

  Scenario: Подделанный JWT signature
    Given атакующий модифицировал payload JWT токена
    And signature не соответствует SECRET_KEY
    When отправляется запрос с подделанным токеном
    Then HTTP статус = 401 Unauthorized
    And response содержит "code" = "INVALID_TOKEN"
    And попытка логируется как security incident
    And НЕ предоставляется информация о причине отклонения
```

### Negative Scenario 3: Граничные случаи валидации
```gherkin
Feature: Строгая валидация входных данных
  Как система
  Я хочу отклонять граничные невалидные случаи
  Чтобы поддерживать целостность данных

  Scenario: Wish с экстремально длинным title
    Given авторизованный пользователь
    When отправляется POST /api/v1/wishes с title длиной 201 символ
    Then HTTP статус = 422 Unprocessable Entity
    And response содержит validation error для поля "title"
    And wish НЕ создается в БД

  Scenario: Отрицательная price_estimate
    Given авторизованный пользователь
    When отправляется POST /api/v1/wishes с price_estimate = -100
    Then HTTP статус = 422 Unprocessable Entity
    And response содержит validation error: "price_estimate must be >= 0"
    And wish НЕ создается в БД
```

---

## Критерии приемки (Definition of Done)

Для каждого NFR сценарий считается пройденным, если:

1. ✅ **Автоматизация**: Тест автоматизирован (pytest/k6/postman)
2. ✅ **CI Integration**: Выполняется в CI pipeline
3. ✅ **Мониторинг**: Метрики собираются в production
4. ✅ **Документация**: Процедура проверки задокументирована
5. ✅ **Алертинг**: Настроены алерты на нарушение порогов

---

## Инструменты для реализации тестов

### Unit & Integration тесты
- **pytest**: `tests/test_nfr_auth.py`, `tests/test_nfr_performance.py`
- **pytest-benchmark**: для performance тестов
- **httpx**: для API тестов

### Load тесты
- **k6**: для сценариев NFR-03, NFR-04
- **locust**: альтернатива для complex scenarios

### Security тесты
- **bandit/semgrep**: SAST для NFR-08
- **safety/pip-audit**: dependency scanning для NFR-05

### Мониторинг
- **Prometheus**: сбор метрик
- **Grafana**: дашборды для NFR
- **AlertManager**: алертинг

---

**Владелец документа**: QA & Security Team
**Последнее обновление**: 2025-10-13
**Версия**: 1.0

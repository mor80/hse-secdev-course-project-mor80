# P10 — Отчёты сканирования

В эту директорию CI складывает результаты задания P10:

- `semgrep.sarif` — отчёт Semgrep (профиль `p/ci` + правила из `security/semgrep/rules.yml`).
- `gitleaks.json` — отчёт Gitleaks с конфигом `security/.gitleaks.toml`.

Файлы перезаписываются при каждом успешном запуске workflow `.github/workflows/ci-sast-secrets.yml`.

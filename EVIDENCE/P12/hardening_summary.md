## P12 Hardening Summary

- Dockerfile:
  - Base image pinned (no `latest`).
  - Runtime runs as non-root user.
- IaC:
  - `iac/docker-compose.yml` uses `read_only`, drops capabilities, and enforces `no-new-privileges`.
- Container security scans (Hadolint/Checkov/Trivy) are executed in CI with reports stored under `EVIDENCE/P12/`.

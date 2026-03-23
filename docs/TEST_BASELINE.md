# Test Baseline (Release Gate)

Last updated: 2026-03-23

## Core release gate (required)

1. Backend: `.\.venv\Scripts\python.exe -m pytest backend/tests`
2. Frontend unit tests: `cd frontend && npm.cmd test`

These two suites are the default release gate and are expected to pass stably in CI and local dev.

## Isolated suite (not required by default gate)

1. Frontend E2E (Playwright): `cd frontend && npm.cmd run test:e2e`
2. Food knowledge RAG validation: `.\.venv\Scripts\python.exe scripts/validate_food_kb_rag.py`

Notes:
- The critical-flow E2E case depends on live AI response.
- The spec is now conditionally skipped when `DASHSCOPE_API_KEY` is not set.
- This suite is treated as an integration validation layer, not a hard default gate.
- RAG validation checks dataset health, retrieval coverage, and citation output integrity.

## One-command gate execution

Use:

```powershell
.\scripts\run_release_gate.ps1
```

Behavior:
- Always runs required backend + frontend unit tests.
- Runs Playwright only when `DASHSCOPE_API_KEY` is present in environment.

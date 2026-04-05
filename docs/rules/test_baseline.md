# 测试基线

- Status: Active
- Owner: Engineering
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为默认发布门禁与测试层级主文档
- Related Docs: `docs/TEST_BASELINE.md`

## 默认发布门禁

1. Backend tests: `.\.venv\Scripts\python.exe -m pytest backend/tests`
2. Retrieval quality gate: `.\.venv\Scripts\python.exe scripts/validate_food_kb_rag.py`
3. Frontend unit tests: `cd frontend && npm.cmd test`

## 条件性集成验证

1. Frontend E2E (Playwright): `cd frontend && npm.cmd run test:e2e`

## 规则

1. Backend tests、检索质量验证、前端单测是默认门禁。
2. Playwright 不是默认强制门禁。
3. 是否执行 E2E 取决于 AI key 环境。

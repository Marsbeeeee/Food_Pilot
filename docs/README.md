# FoodPilot Docs Map

## Purpose

This directory should evolve from a single large spec dump into a layered documentation system.

The goal is:

1. Make each type of information have one stable home.
2. Reduce repeated definitions across documents.
3. Make retrieval fast for PM, design, frontend, backend, and testing work.

---

## Source Of Truth Rules

1. One topic should have one primary document.
2. Other documents may reference that topic, but should not redefine it.
3. Stable information goes to long-lived docs; iteration-specific information goes to delivery docs.
4. Product goals, system collaboration, module specs, rules, and delivery tasks should be separated.

---

## Proposed Structure

```text
docs/
  README.md
  glossary.md

  product/
    product_overview.md
    user_journeys.md
    roadmap.md

  system/
    system_overview.md
    core_objects.md
    frontend_backend_contracts.md
    state_machine.md
    data_lifecycle.md

  modules/
    auth.md
    workspace_chat.md
    estimate_api.md
    food_log.md
    profile.md
    insights.md
    product_understanding.md
    decision_engine.md
    image_assets_and_review.md
    food_kb_and_retrieval.md

  rules/
    decision_card_contract.md
    container_data_model.md
    confidence_policy.md
    image_governance.md
    test_baseline.md

  delivery/
    roadmap_current.md
    task_01_decision_card.md
    task_02_decision_mode.md
    task_03_product_understanding.md
    task_04_brand_estimation.md
    task_05_personalized_decision.md
    task_06_decision_workspace.md
    task_07_ocr_entry.md
    task_08_confidence_and_templates.md
    task_09_compare_save_review.md
    task_10_evaluation_and_ops.md

  decisions/
    ADR-001-workspace-as-main-entry.md
    ADR-002-save-vs-analysis-separation.md
    ADR-003-low-confidence-clarification.md

  archives/
    PRODUCT_SPEC_legacy.md
```

---

## What Goes Where

### `product/`

Use for long-lived product intent.

- product positioning
- target users
- main use cases
- end-to-end journey
- product boundaries
- roadmap themes

### `system/`

Use for how the product works as one system.

- module collaboration
- cross-module flows
- upstream/downstream dependencies
- state transitions
- object flow from input to storage to analysis
- frontend and backend interaction model

### `modules/`

Use for module-local behavior and ownership.

- responsibilities
- non-goals
- local APIs and dependencies
- module-specific rules
- local acceptance criteria

### `rules/`

Use for cross-module shared rules.

- data contracts
- object semantics
- save and analysis rules
- confidence policy
- governance policies
- test baseline

### `delivery/`

Use for implementation planning and phased delivery.

- current phase scope
- task breakdown
- dependencies
- rollout order
- acceptance checklist

### `decisions/`

Use for recording why a key choice was made.

- chosen approach
- alternatives considered
- impact
- follow-up implications

### `archives/`

Use for deprecated large docs that should remain readable but no longer act as the main source of truth.

---

## Retrieval Guide

When looking for information, use this routing rule:

- "What is the product trying to achieve?" -> `product/`
- "How do modules cooperate?" -> `system/`
- "How does one module behave?" -> `modules/`
- "What is the canonical contract or rule?" -> `rules/`
- "What are we building this phase?" -> `delivery/`
- "Why was this tradeoff chosen?" -> `decisions/`

---

## Recommended Metadata Template

Each major doc should start with:

```md
# Title

- Status:
- Owner:
- Last Updated:
- Source Of Truth:
- Depends On:
- Related Docs:
```

This keeps ownership and retrieval explicit.

---

## Recommended Writing Template

For most specs, prefer this section order:

1. Goal
2. Scope
3. Non-goals
4. Responsibilities
5. Inputs / Outputs
6. Core flow
7. States and exceptions
8. Data / API contract
9. Acceptance criteria
10. Related docs

---

## Current Docs Mapping

Current files should gradually move into this structure:

- `PRODUCT_SPEC.md` -> split across `product/`, `system/`, `modules/`, `delivery/`
- `TASK2_DECISION_MODE_SPEC.md` -> `delivery/task_02_decision_mode.md` and later merge stable parts into `modules/workspace_chat.md`
- `CONTAINER_DATA_MODEL_SPEC.md` -> `rules/container_data_model.md`
- `FOOD_LOG_IMAGE_GOVERNANCE.md` -> `rules/image_governance.md`
- `TEST_BASELINE.md` -> `rules/test_baseline.md`
- `food_kb_task2/*` -> keep as supporting delivery artifacts under `delivery/` or `archives/` unless promoted into stable rules

---

## Suggested Migration Order

1. Add glossary and this navigation file.
2. Split `PRODUCT_SPEC.md` into stable layers before adding new tasks.
3. Move cross-module rules into `rules/`.
4. Move module-specific behavior into `modules/`.
5. Keep `delivery/` for phase work only.
6. Retain the old large spec as a legacy reference during transition.

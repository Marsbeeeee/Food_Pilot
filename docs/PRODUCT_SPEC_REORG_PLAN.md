# PRODUCT_SPEC Reorganization Plan

- Status: Draft
- Owner: Product
- Last Updated: 2026-04-05
- Source Of Truth: This file is the migration plan, not the final long-term source of truth.
- Related Docs: `docs/README.md`, `docs/PRODUCT_SPEC.md`

## Goal

Split the current `PRODUCT_SPEC.md` by information type so that stable product knowledge, system collaboration rules, module specs, and delivery tasks stop living in one document.

---

## New Target Docs

### Product Layer

- `docs/product/product_overview.md`
- `docs/product/user_journeys.md`
- `docs/product/roadmap.md`

### System Layer

- `docs/system/system_overview.md`
- `docs/system/core_objects.md`
- `docs/system/frontend_backend_contracts.md`
- `docs/system/state_machine.md`
- `docs/system/data_lifecycle.md`

### Module Layer

- `docs/modules/auth.md`
- `docs/modules/workspace_chat.md`
- `docs/modules/estimate_api.md`
- `docs/modules/food_log.md`
- `docs/modules/profile.md`
- `docs/modules/insights.md`
- `docs/modules/product_understanding.md`
- `docs/modules/decision_engine.md`
- `docs/modules/image_assets_and_review.md`
- `docs/modules/food_kb_and_retrieval.md`

### Rules Layer

- `docs/rules/decision_card_contract.md`
- `docs/rules/container_data_model.md`
- `docs/rules/confidence_policy.md`
- `docs/rules/image_governance.md`
- `docs/rules/test_baseline.md`

### Delivery Layer

- `docs/delivery/roadmap_current.md`
- `docs/delivery/task_01_decision_card.md`
- `docs/delivery/task_02_decision_mode.md`
- `docs/delivery/task_03_product_understanding.md`
- `docs/delivery/task_04_brand_estimation.md`
- `docs/delivery/task_05_personalized_decision.md`
- `docs/delivery/task_06_decision_workspace.md`
- `docs/delivery/task_07_ocr_entry.md`
- `docs/delivery/task_08_confidence_and_templates.md`
- `docs/delivery/task_09_compare_save_review.md`
- `docs/delivery/task_10_evaluation_and_ops.md`

---

## Split Principles

1. Stable definitions move out first.
2. Cross-module semantics get their own docs instead of staying buried under one feature chapter.
3. Module behavior stays with the module, even if it currently appears in the large product spec.
4. Tasks keep only delivery intent, dependencies, and acceptance criteria.
5. Repeated wording should become links, not duplicated paragraphs.

---

## Section Mapping From Current PRODUCT_SPEC

### A. Move to `docs/product/product_overview.md`

Use for stable product intent and boundaries.

- `产品方向总述`
- `一、产品定位`
- `二、核心产品目标`
- `三、目标用户与使用场景`
- `四、产品形态与入口设计`
- `六、关键差异化方向`
- `九、当前阶段的产品边界`
- `十、建议写入 Spec 的一句话版本`
- `17. 当前版本对外描述建议`
- `19. 结论` 中保留产品级结论，工程现状另拆

### B. Move to `docs/product/user_journeys.md`

Use for stable journey framing.

- `12. 当前信息架构` 中的主链路描述
- `20.1 升级主链路`
- 来自场景章节的用户旅程片段，重写为统一 journey 文档

### C. Move to `docs/product/roadmap.md`

Use for product stage planning, not detailed implementation tasks.

- `八、阶段性实施路径`
- `18. 下一阶段行动计划` 的产品级摘要
- `20.3 任务优先级分层`
- `22. 建议执行顺序`
- `23. P0 阶段定义`

---

### D. Move to `docs/system/system_overview.md`

Use for how the system works as one product.

- `五、核心能力框架`
- `七、系统数据与能力沉淀方向`
- `12. 当前信息架构` 的系统视图重写
- `13. 当前版本模块状态`
- `20.2 本轮规划的设计原则`

This doc should explicitly add material that is currently missing:

- module collaboration map
- end-to-end flow by stage
- capability-layer vs entry-layer separation
- upstream/downstream ownership

### E. Move to `docs/system/core_objects.md`

This is mostly missing today and should be newly created.

It should define:

- `raw_input`
- `normalized_input`
- `product_structure`
- `decision_card`
- `save_target`
- `food_log_entry`
- `analysis_item`
- `favorite_item`

### F. Move to `docs/system/frontend_backend_contracts.md`

This also needs significant new writing.

It should centralize:

- workspace request models
- chat response contract
- estimate response contract
- decision card UI-driving fields
- save action contract
- analysis basket contract

### G. Move to `docs/system/state_machine.md`

This should be newly created from scattered behavior.

It should define:

- input idle / submitting / parsing
- clarification required
- low confidence but continuable
- success
- saveable but not analysis-eligible
- analysis-eligible
- save success / failure
- deleted source fallback states

### H. Move to `docs/system/data_lifecycle.md`

This should collect lifecycle rules now spread across multiple sections.

It should define:

- chat result lifecycle
- save lifecycle
- container assignment lifecycle
- analysis eligibility lifecycle
- edit / soft delete / restore impact
- session deletion impact on saved objects

---

### I. Move to `docs/modules/auth.md`

- `4.1 Auth`

### J. Move to `docs/modules/workspace_chat.md`

- `4.2 Chat / Assistant`
- `4.2.1 会话能力`
- `4.2.2 消息类型契约`
- `4.2.3 意图分流`
- `4.2.4 Assistant 输出边界`
- `4.2.5 推荐安全约束`
- `4.2.6 Chat 估算卡片层级强约束`

This doc should later absorb stable pieces from `TASK2_DECISION_MODE_SPEC.md`.

### K. Move to `docs/modules/estimate_api.md`

- `4.3 独立 Estimate API（系统能力层）`

### L. Move to `docs/modules/food_log.md`

- `4.4 Food Log`
- especially save, edit, retrieval, lifecycle sections

### M. Move to `docs/modules/profile.md`

- `4.5 Profile`

### N. Move to `docs/modules/insights.md`

- `4.6 Insights`

### O. Move to `docs/modules/food_kb_and_retrieval.md`

- `13. 当前版本模块状态` 中知识库相关状态
- `18. 下一阶段行动计划` 中任务 1、任务 2

### P. Move to `docs/modules/image_assets_and_review.md`

- `4.4.7 图片与元数据`
- `4.4.8 标准菜品图片自动补齐（当前实现）`
- `13. 当前版本模块状态` 中图片资产 / Admin 审核说明

### Q. Create `docs/modules/product_understanding.md`

This is currently implied in tasks, but not yet documented as a stable module.

Primary source material today:

- `Task 3：实现商品理解层与分层商品目录 V1`
- related constraints in chat clarification and save/container logic

### R. Create `docs/modules/decision_engine.md`

This is also currently implied, not centralized.

Primary source material today:

- `Task 1：统一点单决策卡片输出契约`
- `Task 4：实现品牌感知估算层 V1`
- `Task 5：实现个体化决策层与建议层 V1`

---

### S. Move to `docs/rules/decision_card_contract.md`

This should be extracted from:

- `Task 1：统一“点单决策卡片”输出契约`
- parts of `4.2.4 Assistant 输出边界`
- parts of `4.2.6 Chat 估算卡片层级强约束`
- parts of `4.3 独立 Estimate API` return contract

### T. Move to `docs/rules/container_data_model.md`

Primary source:

- `docs/CONTAINER_DATA_MODEL_SPEC.md`
- `PRODUCT_SPEC.md` sections:
  - `4.4.1A 容器模型（下一阶段补充）`
  - save / analysis eligibility language
  - task sections referring to `container_type`, `save_container_key`, `analysis_eligible`

### U. Create `docs/rules/confidence_policy.md`

Primary source material:

- clarification rules under chat
- task 3 low-confidence parsing behavior
- task 4 fallback logic
- task 8 confidence mechanism

### V. Move to `docs/rules/image_governance.md`

- `docs/FOOD_LOG_IMAGE_GOVERNANCE.md`

### W. Move to `docs/rules/test_baseline.md`

- `docs/TEST_BASELINE.md`
- `15.4 测试基线`

---

### X. Move to `docs/delivery/roadmap_current.md`

Use this for the current execution phase only.

- `18. 下一阶段行动计划`
- condensed version of `20` to `23`

### Y. Move Task Sections Into Separate Delivery Docs

- `Task 1` -> `docs/delivery/task_01_decision_card.md`
- `Task 2` -> `docs/delivery/task_02_decision_mode.md`
- `Task 3` -> `docs/delivery/task_03_product_understanding.md`
- `Task 4` -> `docs/delivery/task_04_brand_estimation.md`
- `Task 5` -> `docs/delivery/task_05_personalized_decision.md`
- `Task 6` -> `docs/delivery/task_06_decision_workspace.md`
- `Task 7` -> `docs/delivery/task_07_ocr_entry.md`
- `Task 8` -> `docs/delivery/task_08_confidence_and_templates.md`
- `Task 9` -> `docs/delivery/task_09_compare_save_review.md`
- `Task 10` -> `docs/delivery/task_10_evaluation_and_ops.md`

Each task doc should keep only:

- goal
- scope
- dependencies
- implementation notes for this phase
- acceptance criteria

Stable definitions should link to `system/`, `modules/`, or `rules/`.

---

## Recommended Migration Sequence

1. Keep current `PRODUCT_SPEC.md` unchanged as transition source.
2. Create `docs/README.md` and this plan first.
3. Extract cross-module rules into `rules/`.
4. Extract module specs into `modules/`.
5. Write missing `system/` docs for collaboration, objects, state, and lifecycle.
6. Move tasks into `delivery/`.
7. Reduce `PRODUCT_SPEC.md` into a short hub doc or archive it under `archives/`.

---

## What Should Stay Out Of PRODUCT_SPEC Going Forward

After migration, the top-level product spec should no longer directly carry:

- detailed route lists for every module
- full save / restore / delete operational rules
- repeated contract field definitions
- detailed delivery tasks for every phase
- test execution commands
- governance details for specialized subsystems

Instead, it should act as an executive map pointing to the correct lower-level docs.

---

## Expected Outcome

After the split:

- PM can find strategy, roadmap, and journeys without scanning engineering detail.
- frontend and backend can find contracts and state logic without reading all tasks.
- rules like `analysis_eligible` and `container_type` get one canonical home.
- delivery planning stops polluting stable product/system docs.
- future retrieval becomes a classification problem instead of a memory problem.

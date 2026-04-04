# Task2 Scope (2026-04-04)

## Fixed Input
- Seed dataset: `backend/data/chinese_food_kb_seed.json`
- Baseline source version: `2026-03-30` (75 entries)
- Task2 release version: `2026-04-04`

## Expansion Classes (Top 高频 + 易误判)
- 组合菜（盖饭表达）
: 番茄炒蛋盖饭、青椒肉丝盖饭、鱼香肉丝盖饭、麻婆豆腐盖饭
- 套餐（主食+配餐+饮料）
: 汉堡薯条可乐套餐、炸鸡汉堡套餐、牛肉面卤蛋套餐、鸡腿饭可乐套餐
- 早餐组合
: 油条豆浆组合、包子豆浆早餐、煎饼果子豆浆早餐、茶叶蛋白粥早餐
- 饮品表达（品牌口语）
: 燕麦拿铁、零度可乐、无糖乌龙茶、蜂蜜柠檬茶、茉莉奶绿

## Governance Scope
- 强制字段门禁: `food_id / aliases / portion_hints / nutrition_per_100g / source_ids / updated_at`
- 固定评估集扩展: 新增 task2 场景 case
- 检索质量基线更新: legacy vs enhanced 指标回归

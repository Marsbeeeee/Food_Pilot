import assert from 'node:assert/strict';
import test from 'node:test';

import { buildFoodLogHierarchy } from './foodLogHierarchy.ts';

test('buildFoodLogHierarchy groups entries by category then brand group', () => {
  const hierarchy = buildFoodLogHierarchy([
    {
      id: '1',
      name: '生椰拿铁',
      description: '瑞幸咖啡',
      calories: '280',
      savedAt: '2026-04-14 10:00:00',
      mealOccurredAt: '2026-04-14 10:00:00',
      category: { id: 'coffee_tea', name: '咖啡奶茶', sortOrder: 10 },
      brandGroup: { id: 'brand:luckin', name: '瑞幸', type: 'brand', sortOrder: 10 },
      breakdown: [],
    },
    {
      id: '2',
      name: '厚乳拿铁',
      description: '瑞幸咖啡',
      calories: '310',
      savedAt: '2026-04-14 11:00:00',
      mealOccurredAt: '2026-04-14 11:00:00',
      category: { id: 'coffee_tea', name: '咖啡奶茶', sortOrder: 10 },
      brandGroup: { id: 'brand:luckin', name: '瑞幸', type: 'brand', sortOrder: 10 },
      breakdown: [],
    },
    {
      id: '3',
      name: '黄焖鸡米饭',
      description: '无品牌',
      calories: '520',
      savedAt: '2026-04-14 12:00:00',
      mealOccurredAt: '2026-04-14 12:00:00',
      category: { id: 'snack_meal', name: '小吃简餐', sortOrder: 60 },
      brandGroup: { id: 'no_brand', name: '无品牌', type: 'no_brand', sortOrder: 920 },
      breakdown: [],
    },
  ]);

  assert.equal(hierarchy.length, 2);
  assert.equal(hierarchy[0].name, '咖啡奶茶');
  assert.equal(hierarchy[0].itemCount, 2);
  assert.equal(hierarchy[0].brands.length, 1);
  assert.equal(hierarchy[0].brands[0].name, '瑞幸');
  assert.equal(hierarchy[0].brands[0].itemCount, 2);
  assert.deepEqual(hierarchy[0].brands[0].entries.map((entry) => entry.id), ['1', '2']);
  assert.equal(hierarchy[1].name, '小吃简餐');
  assert.equal(hierarchy[1].brands[0].name, '无品牌');
});

test('buildFoodLogHierarchy falls back to safe unknown buckets when hierarchy fields are missing', () => {
  const hierarchy = buildFoodLogHierarchy([
    {
      id: '1',
      name: 'Mystery Meal',
      description: 'legacy record',
      calories: '420',
      savedAt: '2026-04-14 09:00:00',
      mealOccurredAt: '2026-04-14 09:00:00',
      breakdown: [],
    },
  ]);

  assert.equal(hierarchy.length, 1);
  assert.equal(hierarchy[0].id, 'dining');
  assert.equal(hierarchy[0].brands.length, 1);
  assert.equal(hierarchy[0].brands[0].id, 'unknown_source');
  assert.equal(hierarchy[0].brands[0].entries[0].name, 'Mystery Meal');
});

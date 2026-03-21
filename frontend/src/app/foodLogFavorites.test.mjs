import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildFoodLogCollectionStats,
  buildFoodLogEditPayload,
  filterFoodLogEntries,
  sortFoodLogEntries,
} from './foodLogFavorites.js';

test('sortFoodLogEntries supports updated_desc with updatedAt fallback', () => {
  const bySavedAt = sortFoodLogEntries([
    {
      id: '1',
      savedAt: '2026-03-12 08:00:00',
      updatedAt: '2026-03-16 08:00:00',
    },
    {
      id: '2',
      savedAt: '2026-03-14 09:30:00',
      updatedAt: '2026-03-15 11:00:00',
    },
    {
      id: '3',
      savedAt: 'invalid',
    },
  ]);
  const byUpdatedAt = sortFoodLogEntries([
    {
      id: '1',
      savedAt: '2026-03-12 08:00:00',
      updatedAt: '2026-03-16 08:00:00',
    },
    {
      id: '2',
      savedAt: '2026-03-14 09:30:00',
      updatedAt: '2026-03-15 11:00:00',
    },
    {
      id: '3',
      savedAt: 'invalid',
    },
  ], 'updated_desc');

  assert.deepEqual(
    bySavedAt.map((entry) => entry.id),
    ['2', '1', '3'],
  );
  assert.deepEqual(
    byUpdatedAt.map((entry) => entry.id),
    ['1', '2', '3'],
  );
});

test('sortFoodLogEntries supports calorie ascending and descending order', () => {
  const entries = [
    { id: '1', calories: '420 kcal', savedAt: '2026-03-10 08:00:00' },
    { id: '2', calories: '180 kcal', savedAt: '2026-03-11 08:00:00' },
    { id: '3', calories: '', savedAt: '2026-03-12 08:00:00' },
    { id: '4', calories: '640 kcal', savedAt: '2026-03-13 08:00:00' },
  ];

  const desc = sortFoodLogEntries(entries, 'calories_desc');
  const asc = sortFoodLogEntries(entries, 'calories_asc');

  assert.deepEqual(desc.map((entry) => entry.id), ['4', '1', '2', '3']);
  assert.deepEqual(asc.map((entry) => entry.id), ['2', '1', '4', '3']);
});

test('buildFoodLogEditPayload trims fields and normalizes kcal values', () => {
  const payload = buildFoodLogEditPayload({
    name: '  Chicken   Salad  ',
    description: '  Protein forward   lunch ',
    calories: '260',
    ingredients: [
      {
        name: ' Chicken ',
        portion: ' 150g ',
        energy: '220',
      },
      {
        name: ' Avocado ',
        portion: ' 50g ',
        energy: '40 kcal',
      },
    ],
  });

  assert.deepEqual(payload, {
    resultTitle: 'Chicken Salad',
    resultDescription: 'Protein forward lunch',
    totalCalories: '260 kcal',
    ingredients: [
      {
        name: 'Chicken',
        portion: '150g',
        energy: '220 kcal',
      },
      {
        name: 'Avocado',
        portion: '50g',
        energy: '40 kcal',
      },
    ],
  });
});

test('buildFoodLogEditPayload requires at least one ingredient', () => {
  assert.throws(
    () => buildFoodLogEditPayload({
      name: 'Chicken Salad',
      description: 'Protein forward lunch',
      calories: '260 kcal',
      ingredients: [],
    }),
    /Add at least one ingredient before saving\./,
  );
});

test('buildFoodLogCollectionStats counts recent updates and chat-linked entries', () => {
  const stats = buildFoodLogCollectionStats(
    [
      {
        id: '1',
        savedAt: '2026-03-14 10:00:00',
        sessionId: '42',
      },
      {
        id: '2',
        savedAt: '2026-03-08 09:00:00',
      },
      {
        id: '3',
        savedAt: '2026-03-01 09:00:00',
        sessionId: '99',
      },
    ],
    new Date('2026-03-14T12:00:00'),
  );

  assert.deepEqual(stats, {
    updatedThisWeek: 2,
    chatLinked: 2,
  });
});

test('filterFoodLogEntries supports calorie preset ranges', () => {
  const entries = [
    { id: '1', name: 'A', description: '', calories: '180 kcal', savedAt: '2026-03-10 08:00:00', mealOccurredAt: '2026-03-10 08:00:00' },
    { id: '2', name: 'B', description: '', calories: '350 kcal', savedAt: '2026-03-11 08:00:00', mealOccurredAt: '2026-03-11 08:00:00' },
    { id: '3', name: 'C', description: '', calories: '820 kcal', savedAt: '2026-03-12 08:00:00', mealOccurredAt: '2026-03-12 08:00:00' },
  ];

  const under200 = filterFoodLogEntries(entries, { caloriePreset: 'under_200', sort: 'created_asc' });
  const range200500 = filterFoodLogEntries(entries, { caloriePreset: '200_500', sort: 'created_asc' });
  const above800 = filterFoodLogEntries(entries, { caloriePreset: '800_plus', sort: 'created_asc' });

  assert.deepEqual(under200.map((entry) => entry.id), ['1']);
  assert.deepEqual(range200500.map((entry) => entry.id), ['2']);
  assert.deepEqual(above800.map((entry) => entry.id), ['3']);
});

test('filterFoodLogEntries custom calorie range overrides preset', () => {
  const entries = [
    { id: '1', name: 'A', description: '', calories: '180 kcal', savedAt: '2026-03-10 08:00:00', mealOccurredAt: '2026-03-10 08:00:00' },
    { id: '2', name: 'B', description: '', calories: '350 kcal', savedAt: '2026-03-11 08:00:00', mealOccurredAt: '2026-03-11 08:00:00' },
    { id: '3', name: 'C', description: '', calories: '820 kcal', savedAt: '2026-03-12 08:00:00', mealOccurredAt: '2026-03-12 08:00:00' },
  ];

  const customOnly = filterFoodLogEntries(entries, {
    caloriePreset: '800_plus',
    minCalories: '200',
    maxCalories: '500',
    sort: 'created_asc',
  });

  assert.deepEqual(customOnly.map((entry) => entry.id), ['2']);
});

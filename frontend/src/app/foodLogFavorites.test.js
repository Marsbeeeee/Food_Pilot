import assert from 'node:assert/strict';
import test from 'node:test';

import { filterFoodLogEntries, sortFoodLogEntries } from './foodLogFavorites.js';

const SAMPLE_ENTRIES = [
  {
    id: '1',
    name: 'Chicken Salad',
    description: 'Lunch bowl with greens',
    savedAt: '2026-03-13 12:00:00',
    updatedAt: '2026-03-18 09:00:00',
    mealOccurredAt: '2026-03-13 12:00:00',
    sourceType: 'chat_message',
    image: '',
    breakdown: [{ name: 'Avocado', portion: '50g', energy: '80 kcal' }],
  },
  {
    id: '2',
    name: 'Salmon Bowl',
    description: 'Dinner bowl',
    savedAt: '2026-03-14 18:30:00',
    updatedAt: '2026-03-16 10:15:00',
    mealOccurredAt: '2026-03-14 18:30:00',
    sourceType: 'chat_message',
    image: 'https://img.example/salmon.jpg',
    breakdown: [{ name: 'Salmon', portion: '180g', energy: '320 kcal' }],
  },
  {
    id: '3',
    name: 'Oatmeal Bowl',
    description: 'Breakfast oats',
    savedAt: '2026-03-15 08:00:00',
    mealOccurredAt: '2026-03-15 08:00:00',
    sourceType: 'estimate_api',
    image: undefined,
    breakdown: [{ name: 'Oats', portion: '1 bowl', energy: '320 kcal' }],
  },
];

test('sortFoodLogEntries supports created_desc, created_asc, and updated_desc', () => {
  const desc = sortFoodLogEntries(SAMPLE_ENTRIES, 'created_desc');
  const asc = sortFoodLogEntries(SAMPLE_ENTRIES, 'created_asc');
  const updated = sortFoodLogEntries(SAMPLE_ENTRIES, 'updated_desc');

  assert.deepEqual(desc.map((item) => item.id), ['3', '2', '1']);
  assert.deepEqual(asc.map((item) => item.id), ['1', '2', '3']);
  assert.deepEqual(updated.map((item) => item.id), ['1', '2', '3']);
});

test('sortFoodLogEntries supports calories_desc and calories_asc', () => {
  const entries = [
    { id: '1', calories: '420 kcal', savedAt: '2026-03-10 08:00:00' },
    { id: '2', calories: '180 kcal', savedAt: '2026-03-11 08:00:00' },
    { id: '3', calories: '', savedAt: '2026-03-12 08:00:00' },
    { id: '4', calories: '640 kcal', savedAt: '2026-03-13 08:00:00' },
  ];

  const desc = sortFoodLogEntries(entries, 'calories_desc');
  const asc = sortFoodLogEntries(entries, 'calories_asc');

  assert.deepEqual(desc.map((item) => item.id), ['4', '1', '2', '3']);
  assert.deepEqual(asc.map((item) => item.id), ['2', '1', '4', '3']);
});

test('filterFoodLogEntries supports stable combined filters', () => {
  const result = filterFoodLogEntries(SAMPLE_ENTRIES, {
    query: 'salmon',
    sourceType: 'chat_message',
    hasImage: 'with_image',
    dateFrom: '2026-03-14',
    dateTo: '2026-03-14',
    sort: 'created_desc',
  });

  assert.deepEqual(result.map((item) => item.id), ['2']);
});

test('filterFoodLogEntries query supports ingredient names and image toggle', () => {
  const byIngredient = filterFoodLogEntries(SAMPLE_ENTRIES, {
    query: 'avocado',
  });
  const withoutImage = filterFoodLogEntries(SAMPLE_ENTRIES, {
    hasImage: 'without_image',
    sort: 'created_asc',
  });

  assert.deepEqual(byIngredient.map((item) => item.id), ['1']);
  assert.deepEqual(withoutImage.map((item) => item.id), ['1', '3']);
});

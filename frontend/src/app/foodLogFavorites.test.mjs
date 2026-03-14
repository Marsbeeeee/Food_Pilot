import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildFoodLogCollectionStats,
  buildFoodLogEditPayload,
  sortFoodLogEntries,
} from './foodLogFavorites.js';

test('sortFoodLogEntries orders favorites by most recent savedAt', () => {
  const ordered = sortFoodLogEntries([
    {
      id: '1',
      savedAt: '2026-03-12 08:00:00',
    },
    {
      id: '2',
      savedAt: '2026-03-14 09:30:00',
    },
    {
      id: '3',
      savedAt: 'invalid',
    },
  ]);

  assert.deepEqual(
    ordered.map((entry) => entry.id),
    ['2', '1', '3'],
  );
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

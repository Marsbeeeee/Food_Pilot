import assert from 'node:assert/strict';
import test from 'node:test';

import {
  autoSaveAnalysisBasket,
  getDailyAnalysisStorageKey,
  loadSavedAnalysisSelections,
  restoreAllAnalysisItems,
  restoreAnalysisItemsFromSyncedBasket,
  serializeAnalysisBasketForSync,
} from './insightsBasketState.ts';

test('autoSaveAnalysisBasket and restoreAllAnalysisItems keep basket snapshots recoverable', () => {
  const cleanup = installMockWindow();
  try {
    const baseEntry = buildEntry('101', 'Oatmeal');
    const orphanSnapshot = buildEntry('202', 'Eggs');

    autoSaveAnalysisBasket('user-1', [
      {
        ...baseEntry,
        basketId: 'basket-a',
        analysisDate: '2026-03-20',
      },
      {
        ...orphanSnapshot,
        basketId: 'basket-b',
        analysisDate: '2026-03-21',
      },
    ]);

    const restored = restoreAllAnalysisItems('user-1', [
      { ...baseEntry, name: 'Oatmeal (Updated)' },
    ]);

    assert.equal(restored.length, 2);
    assert.equal(restored[0].analysisDate, '2026-03-20');
    assert.equal(restored[0].name, 'Oatmeal (Updated)');
    assert.equal(restored[1].analysisDate, '2026-03-21');
    assert.equal(restored[1].id, '202');
    assert.equal(restored[1].name, 'Eggs');
    assert.ok(restored[0].basketId);
    assert.ok(restored[1].basketId);
  } finally {
    cleanup();
  }
});

test('loadSavedAnalysisSelections tolerates malformed localStorage payload', () => {
  const cleanup = installMockWindow({
    [getDailyAnalysisStorageKey('user-2')]: '{bad-json',
  });
  try {
    assert.deepEqual(loadSavedAnalysisSelections('user-2'), {});
  } finally {
    cleanup();
  }
});

test('serializeAnalysisBasketForSync and restoreAnalysisItemsFromSyncedBasket preserve IDs and dates', () => {
  const baseEntry = buildEntry('101', 'Oatmeal');
  const serialized = serializeAnalysisBasketForSync([
    {
      ...baseEntry,
      basketId: 'basket-a',
      analysisDate: '2026-03-20',
    },
  ]);

  assert.deepEqual(serialized, [
    {
      basketId: 'basket-a',
      analysisDate: '2026-03-20',
      snapshot: baseEntry,
    },
  ]);

  const restored = restoreAnalysisItemsFromSyncedBasket(serialized, [
    { ...baseEntry, calories: '350' },
  ]);

  assert.equal(restored.length, 1);
  assert.equal(restored[0].basketId, 'basket-a');
  assert.equal(restored[0].analysisDate, '2026-03-20');
  assert.equal(restored[0].calories, '350');
});

test('analysis basket helpers ignore ineligible or deleted snapshots', () => {
  const cleanup = installMockWindow();
  try {
    const eligibleEntry = buildEntry('101', 'Oatmeal');
    const ineligibleEntry = buildEntry('202', 'Needs Clarification', {
      decisionCard: {
        analysisEligible: false,
      },
    });
    const deletedEntry = buildEntry('303', 'Deleted Item', {
      status: 'deleted',
    });

    autoSaveAnalysisBasket('user-3', [
      {
        ...eligibleEntry,
        basketId: 'basket-a',
        analysisDate: '2026-03-20',
      },
      {
        ...ineligibleEntry,
        basketId: 'basket-b',
        analysisDate: '2026-03-20',
      },
      {
        ...deletedEntry,
        basketId: 'basket-c',
        analysisDate: '2026-03-20',
      },
    ]);

    const restored = restoreAllAnalysisItems('user-3', [eligibleEntry, ineligibleEntry, deletedEntry]);
    assert.equal(restored.length, 1);
    assert.equal(restored[0].id, '101');

    const serialized = serializeAnalysisBasketForSync([
      {
        ...eligibleEntry,
        basketId: 'basket-a',
        analysisDate: '2026-03-20',
      },
      {
        ...ineligibleEntry,
        basketId: 'basket-b',
        analysisDate: '2026-03-20',
      },
    ]);
    assert.equal(serialized.length, 1);
    assert.equal(serialized[0].snapshot.id, '101');

    const restoredFromSync = restoreAnalysisItemsFromSyncedBasket([
      {
        basketId: 'basket-a',
        analysisDate: '2026-03-20',
        snapshot: eligibleEntry,
      },
      {
        basketId: 'basket-b',
        analysisDate: '2026-03-20',
        snapshot: ineligibleEntry,
      },
    ], [eligibleEntry, ineligibleEntry]);
    assert.equal(restoredFromSync.length, 1);
    assert.equal(restoredFromSync[0].id, '101');
  } finally {
    cleanup();
  }
});

function installMockWindow(initial = {}) {
  const previousWindow = globalThis.window;
  const storage = new Map(Object.entries(initial));

  globalThis.window = {
    localStorage: {
      getItem(key) {
        return storage.has(key) ? storage.get(key) : null;
      },
      setItem(key, value) {
        storage.set(key, String(value));
      },
      removeItem(key) {
        storage.delete(key);
      },
      clear() {
        storage.clear();
      },
    },
  };

  return () => {
    if (typeof previousWindow === 'undefined') {
      delete globalThis.window;
    } else {
      globalThis.window = previousWindow;
    }
  };
}

function buildEntry(id, name, overrides = {}) {
  return {
    id,
    name,
    description: `${name} description`,
    calories: '320',
    date: 'Mar 20',
    time: '08:00 AM',
    savedAt: '2026-03-20 08:00:00',
    mealOccurredAt: '2026-03-20 08:00:00',
    status: 'active',
    sourceType: 'manual',
    isManual: true,
    breakdown: [
      {
        name,
        portion: '1 bowl',
        energy: '320 kcal',
      },
    ],
    ...overrides,
  };
}

import type { FoodLogEntry, InsightsBasketItem } from '../types/types';

export interface AnalysisSelectionItem extends FoodLogEntry {
  basketId: string;
  analysisDate: string;
}

/** Format: date -> array of {id, snapshot}. Snapshot allows items to persist after unsave from Food Log. */
export type SavedAnalysisSelections = Record<string, Array<{ id: string; snapshot: FoodLogEntry }>>;

const DAILY_ANALYSIS_STORAGE_PREFIX = 'foodpilot:dailyAnalysis:';

export function createAnalysisBasketItemId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function getDailyAnalysisStorageKey(userId: string): string {
  return `${DAILY_ANALYSIS_STORAGE_PREFIX}${userId}`;
}

export function loadSavedAnalysisSelections(userId: string): SavedAnalysisSelections {
  if (typeof window === 'undefined') {
    return {};
  }
  try {
    const raw = window.localStorage.getItem(getDailyAnalysisStorageKey(userId));
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== 'object') {
      return {};
    }
    const obj = parsed as Record<string, unknown>;
    const result: SavedAnalysisSelections = {};
    for (const [date, val] of Object.entries(obj)) {
      if (!Array.isArray(val)) continue;
      const items: Array<{ id: string; snapshot: FoodLogEntry }> = [];
      for (const it of val) {
        if (it && typeof it === 'object' && 'id' in it && 'snapshot' in it) {
          const snapshot = (it as { snapshot: unknown }).snapshot;
          if (snapshot && typeof snapshot === 'object') {
            items.push({
              id: String((it as { id: unknown }).id),
              snapshot: snapshot as FoodLogEntry,
            });
          }
        } else if (typeof it === 'string') {
          items.push({ id: it, snapshot: null as unknown as FoodLogEntry });
        }
      }
      result[date] = items;
    }
    return result;
  } catch {
    return {};
  }
}

export function persistSavedAnalysisSelections(
  userId: string,
  value: SavedAnalysisSelections,
): void {
  if (typeof window === 'undefined') {
    return;
  }
  try {
    window.localStorage.setItem(
      getDailyAnalysisStorageKey(userId),
      JSON.stringify(value),
    );
  } catch {
    // Swallow storage errors to avoid breaking the UI.
  }
}

export function autoSaveAnalysisBasket(
  userId: string,
  basket: AnalysisSelectionItem[],
): void {
  const byDate: SavedAnalysisSelections = {};
  for (const item of basket) {
    if (!byDate[item.analysisDate]) {
      byDate[item.analysisDate] = [];
    }
    const { basketId, analysisDate, ...snapshot } = item;
    byDate[item.analysisDate].push({
      id: item.id,
      snapshot: snapshot as FoodLogEntry,
    });
  }
  persistSavedAnalysisSelections(userId, byDate);
}

export function restoreAllAnalysisItems(
  userId: string,
  allEntries: FoodLogEntry[],
): AnalysisSelectionItem[] {
  const saved = loadSavedAnalysisSelections(userId);
  const entriesById = new Map(allEntries.map((entry) => [entry.id, entry]));
  const result: AnalysisSelectionItem[] = [];

  for (const [date, items] of Object.entries(saved)) {
    for (const { id, snapshot } of items) {
      const entry = entriesById.get(id) ?? (
        snapshot && Object.keys(snapshot).length > 0
          ? snapshot
          : null
      );
      if (!entry) continue;
      result.push({
        ...entry,
        basketId: createAnalysisBasketItemId(),
        analysisDate: date,
      });
    }
  }

  return result;
}

export function serializeAnalysisBasketForSync(
  basket: AnalysisSelectionItem[],
): InsightsBasketItem[] {
  return basket.map((item) => {
    const { basketId, analysisDate, ...snapshot } = item;
    return {
      basketId,
      analysisDate,
      snapshot: snapshot as FoodLogEntry,
    };
  });
}

export function restoreAnalysisItemsFromSyncedBasket(
  items: InsightsBasketItem[],
  allEntries: FoodLogEntry[],
): AnalysisSelectionItem[] {
  const entriesById = new Map(allEntries.map((entry) => [entry.id, entry]));
  const result: AnalysisSelectionItem[] = [];

  for (const item of items) {
    const entry = entriesById.get(item.snapshot.id) ?? item.snapshot;
    if (!entry) continue;
    result.push({
      ...entry,
      basketId: item.basketId || createAnalysisBasketItemId(),
      analysisDate: item.analysisDate,
    });
  }

  return result;
}

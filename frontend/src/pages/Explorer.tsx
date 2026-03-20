import React, { useEffect, useState } from 'react';

import {
  buildFoodLogCollectionStats,
  buildFoodLogEditPayload,
  formatSavedMoment,
  sortFoodLogEntries,
} from '../app/foodLogFavorites';
import {
  AnalysisSelectionItem,
  autoSaveAnalysisBasket,
  createAnalysisBasketItemId,
  restoreAllAnalysisItems,
  restoreAnalysisItemsFromSyncedBasket,
  serializeAnalysisBasketForSync,
} from '../app/insightsBasketState';
import {
  buildInsightsCacheKey,
  normalizeSelectedLogIds,
} from '../app/insightsCacheKey';
import {
  buildInsightsCacheFromHistoryItems,
  getNormalizedRangeKeyFromCacheKey,
  resolveHistoryInsightsState,
} from '../app/insightsHistoryState';
import {
  getInsightsAIPanelDescription,
  getInsightsAnalyzeButtonText,
  getInsightsIdleHint,
  getInsightsLoadingHint,
  getInsightsScopeDescription,
  shouldForceReanalyze,
} from '../app/insightsUiState';
import { buildWeeklyTrendSummary } from '../app/insightsWeekTrends';
import type { WeeklyTrendMetric } from '../app/insightsWeekTrends';
import {
  analyzeInsights,
  fetchInsightsBasket,
  fetchInsightsHistory,
  InsightsApiError,
  syncInsightsBasket,
} from '../api/insights';
import { ConfirmDialog } from '../components/ConfirmDialog';
import {
  FoodLogEntry,
  FoodLogPatchInput,
  IngredientResult,
  InsightsAnalyzeData,
} from '../types/types';

interface ExplorerProps {
  logEntries: FoodLogEntry[];
  onNavigateToSession: (sessionId: string) => void;
  onDeleteFoodLog: (entryId: string) => Promise<void>;
  onRestoreFoodLog: (entryId: string) => Promise<void>;
  onUpdateFoodLog: (entryId: string, payload: FoodLogPatchInput) => Promise<void>;
  defaultToAnalysisView?: boolean;
  analysisDate: string;
  onAnalysisDateChange?: (date: string) => void;
  onNavigateToInsights?: () => void;
  currentUserId?: string | number;
  profileKcalTarget?: string | number;
  insightsCache?: Record<string, { status: 'success'; data: InsightsAnalyzeData }>;
  onInsightsCacheUpdate?: React.Dispatch<React.SetStateAction<Record<string, { status: 'success'; data: InsightsAnalyzeData }>>>;
  insightsHistoryLoaded?: boolean;
}

interface FoodLogEditDraft {
  name: string;
  description: string;
  calories: string;
  ingredients: IngredientResult[];
  originalIngredients: IngredientResult[];
}

function getSelectedLogIdsForAnalysis(
  analyzeItems: AnalysisSelectionItem[],
  logEntryIds: Set<string>,
): number[] {
  return normalizeSelectedLogIds(
    analyzeItems
      .filter((item) => logEntryIds.has(item.id))
      .map((item) => Number(item.id)),
  );
}

export const Explorer: React.FC<ExplorerProps> = ({
  logEntries,
  onNavigateToSession,
  onDeleteFoodLog,
  onRestoreFoodLog,
  onUpdateFoodLog,
  defaultToAnalysisView = false,
  analysisDate,
  onAnalysisDateChange,
  onNavigateToInsights,
  currentUserId,
  profileKcalTarget,
  insightsCache: insightsCacheProp,
  onInsightsCacheUpdate: onInsightsCacheUpdateProp,
  insightsHistoryLoaded: insightsHistoryLoadedProp,
}) => {
  const orderedEntries = sortFoodLogEntries(logEntries);
  const [selectedEntry, setSelectedEntry] = useState<FoodLogEntry | null>(null);
  const [isMobileDetailOpen, setIsMobileDetailOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [deletingEntryId, setDeletingEntryId] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [undoableDeletedEntry, setUndoableDeletedEntry] = useState<FoodLogEntry | null>(null);
  const [restoringEntryId, setRestoringEntryId] = useState<string | null>(null);
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [editDraft, setEditDraft] = useState<FoodLogEditDraft | null>(null);

  const [analysisBasket, setAnalysisBasket] = useState<AnalysisSelectionItem[]>([]);
  const [showAnalysisView, setShowAnalysisView] = useState(defaultToAnalysisView);
  const analysisBasketRef = React.useRef<AnalysisSelectionItem[]>([]);
  const basketHydratedRef = React.useRef(false);
  const basketSyncReadyRef = React.useRef(false);
  const basketSyncQueueRef = React.useRef<Promise<void>>(Promise.resolve());

  const [localInsightsCache, setLocalInsightsCache] = useState<Record<string, { status: 'success'; data: InsightsAnalyzeData }>>({});
  const [localInsightsHistoryLoaded, setLocalInsightsHistoryLoaded] = useState(false);

  const insightsCache = insightsCacheProp ?? localInsightsCache;
  const onInsightsCacheUpdate = onInsightsCacheUpdateProp ?? setLocalInsightsCache;
  const insightsHistoryLoaded = insightsHistoryLoadedProp ?? localInsightsHistoryLoaded;

  useEffect(() => {
    setShowAnalysisView(Boolean(defaultToAnalysisView));
  }, [defaultToAnalysisView]);

  useEffect(() => {
    analysisBasketRef.current = analysisBasket;
  }, [analysisBasket]);

  useEffect(() => {
    if (basketHydratedRef.current) return;
    basketHydratedRef.current = true;

    const userKey = currentUserId != null ? String(currentUserId).trim() : '';
    if (!userKey || typeof window === 'undefined') return;

    const localRestored = restoreAllAnalysisItems(userKey, logEntries);
    if (localRestored.length > 0) {
      setAnalysisBasket(localRestored);
    }

    let cancelled = false;
    void fetchInsightsBasket()
      .then((res) => {
        if (cancelled) return;

        const syncedRestored = restoreAnalysisItemsFromSyncedBasket(res.items, logEntries);
        if (syncedRestored.length > 0) {
          setAnalysisBasket(syncedRestored);
          return;
        }

        const currentLocalBasket = (
          analysisBasketRef.current.length > 0
            ? analysisBasketRef.current
            : localRestored
        );
        if (currentLocalBasket.length === 0) return;
        const payload = serializeAnalysisBasketForSync(currentLocalBasket);
        basketSyncQueueRef.current = basketSyncQueueRef.current
          .catch(() => undefined)
          .then(async () => {
            await syncInsightsBasket(payload);
          })
          .catch(() => undefined);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!cancelled) {
          basketSyncReadyRef.current = true;
        }
      });

    return () => {
      cancelled = true;
    };
  }, [logEntries, currentUserId]);

  useEffect(() => {
    if (!basketHydratedRef.current) return;
    const userKey = currentUserId != null ? String(currentUserId).trim() : '';
    if (!userKey || typeof window === 'undefined') return;

    autoSaveAnalysisBasket(userKey, analysisBasket);
    if (!basketSyncReadyRef.current) return;

    const payload = serializeAnalysisBasketForSync(analysisBasket);
    basketSyncQueueRef.current = basketSyncQueueRef.current
      .catch(() => undefined)
      .then(async () => {
        await syncInsightsBasket(payload);
      })
      .catch(() => undefined);
  }, [analysisBasket, currentUserId]);

  useEffect(() => {
    if (onInsightsCacheUpdateProp != null) return;
    const userKey = currentUserId != null ? String(currentUserId).trim() : '';
    if (!userKey) {
      setLocalInsightsCache({});
      setLocalInsightsHistoryLoaded(true);
      return;
    }
    let cancelled = false;
    setLocalInsightsHistoryLoaded(false);
    void fetchInsightsHistory()
      .then((res) => {
        if (cancelled) return;
        setLocalInsightsCache(buildInsightsCacheFromHistoryItems(res.items));
      })
      .catch(() => {
        if (cancelled) return;
        setLocalInsightsCache({});
      })
      .finally(() => {
        if (!cancelled) {
          setLocalInsightsHistoryLoaded(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [currentUserId, onInsightsCacheUpdateProp]);

  const collectionStats = buildFoodLogCollectionStats(orderedEntries);

  useEffect(() => {
    if (orderedEntries.length === 0) {
      setSelectedEntry(null);
      setIsMobileDetailOpen(false);
      setIsEditing(false);
      setIsDeleteDialogOpen(false);
      setEditDraft(null);
      return;
    }

    setSelectedEntry((current) => {
      if (!current) {
        return null;
      }

      return orderedEntries.find((entry) => entry.id === current.id) ?? null;
    });
  }, [logEntries]);

  const handleDeleteSelectedEntry = async () => {
    if (!selectedEntry || deletingEntryId) {
      return;
    }

    setDeletingEntryId(selectedEntry.id);
    try {
      await onDeleteFoodLog(selectedEntry.id);
      setUndoableDeletedEntry(selectedEntry);
      setIsDeleteDialogOpen(false);
      setIsMobileDetailOpen(false);
      setIsEditing(false);
      setEditDraft(null);
      // Do NOT remove from analysis basket: items in food analysis persist even after unsave.
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : 'Unable to remove this saved entry right now.';
      window.alert(message);
    } finally {
      setDeletingEntryId((current) => (current === selectedEntry.id ? null : current));
    }
  };

  const handleUndoDelete = async () => {
    if (!undoableDeletedEntry || restoringEntryId) {
      return;
    }

    setRestoringEntryId(undoableDeletedEntry.id);
    try {
      await onRestoreFoodLog(undoableDeletedEntry.id);
      setUndoableDeletedEntry(null);
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : 'Unable to restore this saved entry right now.';
      window.alert(message);
    } finally {
      setRestoringEntryId(null);
    }
  };

  const handleOpenEditModal = () => {
    if (!selectedEntry) {
      return;
    }

    setEditDraft(buildEditDraft(selectedEntry));
    setIsEditing(true);
  };

  const handleCloseEditModal = () => {
    if (isSavingEdit) {
      return;
    }

    setIsEditing(false);
    setEditDraft(null);
  };

  const handleIngredientGramsChange = (
    ingredientIndex: number,
    newGramsInput: string,
  ) => {
    setEditDraft((current) => {
      if (!current) {
        return current;
      }

      const original = current.originalIngredients[ingredientIndex];
      if (!original) {
        return current;
      }

      const originalGrams = extractGramsFromPortion(original.portion);
      const newGrams = Number.parseFloat(newGramsInput);
      const ratio = (originalGrams > 0 && Number.isFinite(newGrams) && newGrams >= 0)
        ? newGrams / originalGrams
        : 0;

      const unit = getPortionUnit(original.portion);

      const updatedIngredient: IngredientResult = {
        ...original,
        portion: newGramsInput ? `${newGramsInput} ${unit}` : '',
        energy: ratio > 0 ? `${Math.round(extractCaloriesValue(original.energy) * ratio)} kcal` : '0 kcal',
        protein: original.protein ? `${formatNumber(extractNutritionValue(original.protein) * ratio)} g` : undefined,
        carbs: original.carbs ? `${formatNumber(extractNutritionValue(original.carbs) * ratio)} g` : undefined,
        fat: original.fat ? `${formatNumber(extractNutritionValue(original.fat) * ratio)} g` : undefined,
      };

      return {
        ...current,
        ingredients: current.ingredients.map((ingredient, currentIndex) => (
          currentIndex === ingredientIndex ? updatedIngredient : ingredient
        )),
      };
    });
  };

  const handleSaveEdit = async () => {
    if (!selectedEntry || !editDraft || isSavingEdit) {
      return;
    }

    const nextDraft = {
      ...editDraft,
      calories: getDraftTotalCalories(editDraft),
    };

    setIsSavingEdit(true);
    try {
      await onUpdateFoodLog(selectedEntry.id, buildFoodLogEditPayload(nextDraft));
      setIsEditing(false);
      setEditDraft(null);
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : 'Unable to update this saved entry right now.';
      window.alert(message);
    } finally {
      setIsSavingEdit(false);
    }
  };

  const handleSelectEntry = (entry: FoodLogEntry) => {
    setSelectedEntry(entry);
    setIsEditing(false);
    setIsDeleteDialogOpen(false);
    setEditDraft(null);

    if (typeof window !== 'undefined' && window.matchMedia('(max-width: 1023px)').matches) {
      setIsMobileDetailOpen(true);
    }
  };

  const handleAddToAnalysis = (entry: FoodLogEntry) => {
    setAnalysisBasket((current) => ([
      ...current,
      {
        ...entry,
        basketId: createAnalysisBasketItemId(),
        analysisDate,
      },
    ]));
  };

  const handleRemoveFromAnalysis = (basketId: string) => {
    setAnalysisBasket((current) => current.filter((item) => item.basketId !== basketId));
  };

  const currentDayAnalysisItems = analysisBasket.filter(
    (item) => item.analysisDate === analysisDate,
  );

  if (showAnalysisView) {
    return (
      <AnalysisView
        items={analysisBasket}
        logEntries={logEntries}
        onBack={() => setShowAnalysisView(false)}
        onRemove={handleRemoveFromAnalysis}
        analysisDate={analysisDate}
        onAnalysisDateChange={onAnalysisDateChange}
        currentUserId={currentUserId}
        profileKcalTarget={profileKcalTarget}
        insightsCache={insightsCache}
        onInsightsCacheUpdate={onInsightsCacheUpdate}
        insightsHistoryLoaded={insightsHistoryLoaded}
      />
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden bg-[#FFFDF5] lg:flex-row">
      <main className="custom-scrollbar flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-6 py-6 md:px-8 md:py-8 lg:px-10 lg:py-10 xl:px-12">
        <div className="mx-auto w-full max-w-4xl pb-10">
          <div className="mb-8 flex flex-col gap-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#FF8A65]/70">
              Food Log
            </span>
            <h1 className="font-serif-brand text-4xl font-bold text-[#4A453E] md:text-5xl">
              Saved Entries
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-[#4A453E]/60 md:text-base">
              Food Log keeps the meal analyses you choose to save. It is a list of saved entries
              you can revisit and refine over time, not a full eating diary. Entries are organized
              around when they were last saved or edited.
            </p>
          </div>

          <div className="mb-12 grid grid-cols-1 gap-4 md:grid-cols-3">
            <SummaryCard
              label="Saved Entries"
              value={String(orderedEntries.length)}
              unit="items"
              accent
            />
            <SummaryCard
              label="Updated This Week"
              value={String(collectionStats.updatedThisWeek)}
              unit="items"
            />
            <SummaryCard
              label="Chat-Linked"
              value={String(collectionStats.chatLinked)}
              unit="items"
            />
          </div>

          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                Saved Entries
              </h2>
              {orderedEntries.length > 0 && (
                <span className="text-[11px] font-semibold text-[#4A453E]/35">
                  Sorted by latest save or edit
                </span>
              )}
            </div>

              {orderedEntries.length > 0 ? (
              orderedEntries.map((entry) => {
                const isActive = selectedEntry?.id === entry.id;
                const savedMoment = formatSavedMoment(entry.savedAt);

                return (
                  <div
                    key={entry.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => handleSelectEntry(entry)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        handleSelectEntry(entry);
                      }
                    }}
                    className={`group flex w-full flex-col rounded-[28px] border p-5 text-left transition-all md:flex-row md:items-center cursor-pointer ${
                      isActive
                        ? 'translate-x-1 border-[#4A453E]/10 bg-white shadow-md'
                        : 'border-transparent bg-white/40 hover:border-[#4A453E]/05 hover:bg-white hover:shadow-sm'
                    }`}
                  >
                    <div className="mb-4 size-full h-40 overflow-hidden rounded-[22px] border border-[#4A453E]/05 md:mb-0 md:size-14 md:shrink-0">
                      <FoodLogImage
                        src={entry.image}
                        alt={entry.name}
                        compact
                        className="h-full w-full object-cover grayscale-[20%] transition-all group-hover:grayscale-0"
                      />
                    </div>

                    <div className="min-w-0 flex-1 md:px-6">
                      <span className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-[#4A453E]/30">
                        Updated {savedMoment.date} / {savedMoment.time}
                      </span>
                      <h4 className="truncate text-lg font-bold text-[#4A453E]">{entry.name}</h4>
                      <p className="mt-1 truncate text-xs text-[#4A453E]/50">{entry.description}</p>
                    </div>

                    <div className="mt-4 flex items-center justify-between gap-3 md:mt-0 md:gap-4">
                      <div className="flex flex-col items-start md:items-end">
                        <div className="flex items-baseline gap-1">
                          <span className="font-serif-brand text-2xl font-bold text-[#4A453E]">
                            {formatCalories(entry.calories)}
                          </span>
                          <span className="text-[10px] font-bold uppercase text-[#4A453E]/30">
                            kcal
                          </span>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          handleAddToAnalysis(entry);
                        }}
                        className="flex size-10 items-center justify-center rounded-full bg-[#FFF2EC] text-[#FF8A65] transition-all hover:scale-[1.03] hover:bg-[#FF8A65] hover:text-white"
                        title="Add to today analysis"
                      >
                        <span className="material-symbols-outlined text-[20px]">add</span>
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="rounded-[32px] border border-dashed border-[#4A453E]/10 bg-white/40 py-20 text-center">
                <div className="mb-4 inline-flex size-16 items-center justify-center rounded-full bg-white">
                  <span className="material-symbols-outlined text-4xl text-[#4A453E]/20">
                    history_toggle_off
                  </span>
                </div>
                <p className="text-base font-bold text-[#4A453E]/45">Nothing in Food Log yet.</p>
                <p className="mt-2 text-sm text-[#4A453E]/35">
                  Save an analysis first. Food Log keeps only the results you choose to keep.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      {selectedEntry && (
        <>
          <aside className="hidden min-h-0 bg-white shadow-[-10px_0_30px_rgba(0,0,0,0.02)] lg:flex lg:w-[400px] lg:shrink-0 lg:border-l lg:border-[#4A453E]/05 xl:w-[450px]">
            <SelectedEntryPanel
              entry={selectedEntry}
              isEditing={isEditing}
              editDraft={editDraft}
              isSavingEdit={isSavingEdit}
              isDeleting={deletingEntryId === selectedEntry.id}
              onClose={() => {
                setSelectedEntry(null);
                setIsEditing(false);
                setIsDeleteDialogOpen(false);
                setEditDraft(null);
              }}
              onEdit={handleOpenEditModal}
              onCancelEdit={handleCloseEditModal}
              onSaveEdit={() => void handleSaveEdit()}
              onIngredientGramsChange={handleIngredientGramsChange}
              onDelete={() => setIsDeleteDialogOpen(true)}
              onOpenChat={() => selectedEntry.sessionId && onNavigateToSession(selectedEntry.sessionId)}
              onAddToAnalysis={() => handleAddToAnalysis(selectedEntry)}
            />
          </aside>

          {isMobileDetailOpen && (
            <div
              className="fixed inset-0 z-[90] bg-[#4A453E]/18 px-4 pb-4 pt-20 lg:hidden"
              onClick={() => setIsMobileDetailOpen(false)}
            >
              <div
                className="mx-auto flex h-full w-full max-w-3xl overflow-hidden rounded-[32px] border border-[#4A453E]/8 bg-white shadow-[0_32px_90px_rgba(74,69,62,0.18)]"
                onClick={(event) => event.stopPropagation()}
              >
                <SelectedEntryPanel
                  entry={selectedEntry}
                  isEditing={isEditing}
                  editDraft={editDraft}
                  isSavingEdit={isSavingEdit}
                  isDeleting={deletingEntryId === selectedEntry.id}
                  onClose={() => {
                    setIsMobileDetailOpen(false);
                    setIsEditing(false);
                    setIsDeleteDialogOpen(false);
                    setEditDraft(null);
                  }}
                  onEdit={handleOpenEditModal}
                  onCancelEdit={handleCloseEditModal}
                  onSaveEdit={() => void handleSaveEdit()}
                  onIngredientGramsChange={handleIngredientGramsChange}
                  onDelete={() => setIsDeleteDialogOpen(true)}
                  onOpenChat={() => selectedEntry.sessionId && onNavigateToSession(selectedEntry.sessionId)}
                  onAddToAnalysis={() => handleAddToAnalysis(selectedEntry)}
                />
              </div>
            </div>
          )}
        </>
      )}

      {currentDayAnalysisItems.length > 0 && !selectedEntry && (
        <button
          type="button"
          onClick={() => {
            onNavigateToInsights?.();
            setShowAnalysisView(true);
          }}
          className="fixed bottom-6 right-6 z-[120] flex h-12 w-12 items-center justify-center rounded-full bg-[#FF8A65] text-white shadow-[0_14px_40px_rgba(255,138,101,0.35)] transition-all hover:scale-[1.03] hover:bg-[#FF7A50]"
          title="Open today analysis"
        >
          <div className="relative flex items-center justify-center">
            <span className="material-symbols-outlined text-[22px] leading-none">pie_chart</span>
            <span className="absolute -right-4 -top-3 flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-[#FF8A65] bg-white px-1 text-[9px] font-bold text-[#FF8A65]">
              {currentDayAnalysisItems.length}
            </span>
          </div>
        </button>
      )}

      {undoableDeletedEntry && (
        <div className="pointer-events-none fixed bottom-6 left-1/2 z-[110] w-full max-w-xl -translate-x-1/2 px-6">
          <div className="pointer-events-auto flex items-center justify-between gap-4 rounded-[24px] border border-[#4A453E]/10 bg-white px-5 py-4 shadow-[0_20px_60px_rgba(74,69,62,0.15)]">
            <div className="min-w-0">
              <p className="text-sm font-bold text-[#4A453E]">
                Removed from Food Log
              </p>
              <p className="mt-1 text-xs leading-5 text-[#4A453E]/55">
                {undoableDeletedEntry.name} was soft-deleted. Chat links and audit metadata are still recoverable.
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <button
                type="button"
                onClick={() => setUndoableDeletedEntry(null)}
                disabled={Boolean(restoringEntryId)}
                className="rounded-full border border-[#4A453E]/10 px-3 py-2 text-xs font-bold text-[#4A453E]/55 transition-colors hover:bg-[#F7F3E9] disabled:cursor-not-allowed disabled:opacity-70"
              >
                Dismiss
              </button>
              <button
                type="button"
                onClick={() => void handleUndoDelete()}
                disabled={Boolean(restoringEntryId)}
                className={`rounded-full px-3 py-2 text-xs font-bold text-white transition-colors ${
                  restoringEntryId
                    ? 'cursor-wait bg-[#4A453E]/25'
                    : 'bg-[#FF8A65] hover:bg-[#FF8A65]/90'
                }`}
              >
                {restoringEntryId ? 'Restoring...' : 'Undo Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(selectedEntry) && isDeleteDialogOpen}
        title="Remove Entry?"
        description={(
          <>
            <span className="font-bold text-[#4A453E]">
              {selectedEntry?.name ?? 'This saved entry'}
            </span>{' '}
            will disappear from Food Log, but you can save it again from a new analysis later.
          </>
        )}
        confirmLabel={deletingEntryId ? 'Removing...' : 'Remove Entry'}
        icon="delete"
        isConfirming={Boolean(deletingEntryId)}
        onClose={() => {
          if (!deletingEntryId) {
            setIsDeleteDialogOpen(false);
          }
        }}
        onConfirm={() => void handleDeleteSelectedEntry()}
      />
    </div>
  );
};

type AnalysisState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: InsightsAnalyzeData }
  | { status: 'error'; message: string; retryable: boolean };

interface AnalysisViewProps {
  items: AnalysisSelectionItem[];
  logEntries: FoodLogEntry[];
  onBack: () => void;
  onRemove: (basketId: string) => void;
  analysisDate: string;
  onAnalysisDateChange?: (date: string) => void;
  currentUserId?: string | number;
  profileKcalTarget?: string | number;
  insightsCache: Record<string, { status: 'success'; data: InsightsAnalyzeData }>;
  onInsightsCacheUpdate: React.Dispatch<React.SetStateAction<Record<string, { status: 'success'; data: InsightsAnalyzeData }>>>;
  insightsHistoryLoaded: boolean;
}

type AnalysisMode = 'day' | 'week';
const IDLE_ANALYSIS_STATE: AnalysisState = { status: 'idle' };

const AnalysisView: React.FC<AnalysisViewProps> = ({
  items,
  logEntries,
  onBack,
  onRemove,
  analysisDate,
  onAnalysisDateChange,
  currentUserId,
  profileKcalTarget,
  insightsCache,
  onInsightsCacheUpdate,
  insightsHistoryLoaded,
}) => {
  const logEntryIds = React.useMemo(() => new Set(logEntries.map((e) => e.id)), [logEntries]);
  const [currentDate, setCurrentDate] = useState(analysisDate);
  const [mode, setMode] = useState<AnalysisMode>('day');
  const [weekMetric, setWeekMetric] = useState<WeeklyTrendMetric>('calories');
  const [hoveredWeekPointDate, setHoveredWeekPointDate] = useState<string | null>(null);
  const [runtimeAnalysisState, setRuntimeAnalysisState] = useState<AnalysisState>(IDLE_ANALYSIS_STATE);
  const abortControllerRef = React.useRef<AbortController | null>(null);
  const previousCacheKeyRef = React.useRef<string>('');

  useEffect(() => {
    setCurrentDate(analysisDate);
  }, [analysisDate]);

  const { start: weekStart, end: weekEnd } = getWeekRange(currentDate);
  const dateRange = mode === 'day' 
    ? { start: currentDate, end: currentDate }
    : { start: weekStart, end: weekEnd };

  const filteredItems = items.filter((item) => {
    if (mode === 'day') {
      return item.analysisDate === currentDate;
    } else {
      return item.analysisDate >= weekStart && item.analysisDate <= weekEnd;
    }
  });
  const currentSelectedLogIds = React.useMemo(
    () => getSelectedLogIdsForAnalysis(filteredItems, logEntryIds),
    [filteredItems, logEntryIds],
  );

  const hasOrphanedItems = filteredItems.some((item) => !logEntryIds.has(item.id));

  const clientTotalCalories = filteredItems.reduce(
    (sum, item) => sum + extractCaloriesValue(item.calories),
    0,
  );
  const clientTotalProtein = filteredItems.reduce(
    (sum, item) => sum + extractNutritionValue(item.protein),
    0,
  );
  const clientTotalCarbs = filteredItems.reduce(
    (sum, item) => sum + extractNutritionValue(item.carbs),
    0,
  );
  const clientTotalFat = filteredItems.reduce(
    (sum, item) => sum + extractNutritionValue(item.fat),
    0,
  );
  const currentCacheKey = buildInsightsCacheKey(
    mode,
    dateRange.start,
    dateRange.end,
    currentSelectedLogIds,
  );
  const historyMatchedState = insightsHistoryLoaded
    ? resolveHistoryInsightsState(insightsCache, currentCacheKey)
    : null;
  const analysisState: AnalysisState = runtimeAnalysisState.status === 'idle'
    ? (historyMatchedState ?? IDLE_ANALYSIS_STATE)
    : runtimeAnalysisState;

  const agg = analysisState.status === 'success' ? analysisState.data.aggregation : null;
  const useClientTotals = hasOrphanedItems || !agg;
  const totalCalories = useClientTotals ? clientTotalCalories : agg!.totalCalories;
  const totalProtein = useClientTotals ? clientTotalProtein : agg!.totalProtein;
  const totalCarbs = useClientTotals ? clientTotalCarbs : agg!.totalCarbs;
  const totalFat = useClientTotals ? clientTotalFat : agg!.totalFat;

  const dailyTargetCalories = Math.max(extractCaloriesValue(profileKcalTarget ?? 0), 0);
  const targetCalories = mode === 'week' ? dailyTargetCalories * 7 : dailyTargetCalories;
  const intake = totalCalories;
  const progressRatio = targetCalories > 0 ? Math.min(intake / targetCalories, 1) : 0;
  const remainingCalories = Math.max(targetCalories - intake, 0);
  const exceededCalories = Math.max(intake - targetCalories, 0);
  const isExceeded = intake > targetCalories;
  const weeklyTrend = React.useMemo(
    () => (mode === 'week'
      ? buildWeeklyTrendSummary({
        weekStart,
        weekEnd,
        items: filteredItems,
      })
      : null),
    [mode, weekStart, weekEnd, filteredItems],
  );
  const modeScopeDescription = getInsightsScopeDescription(mode);
  const modeAIPanelDescription = getInsightsAIPanelDescription(mode);
  const modeIdleHint = getInsightsIdleHint(mode, filteredItems.length > 0);
  const modeLoadingHint = getInsightsLoadingHint(mode);
  const selectedWeekSeries = weeklyTrend ? weeklyTrend.seriesByMetric[weekMetric] : null;
  const weekChartModel = React.useMemo(() => {
    if (!selectedWeekSeries || selectedWeekSeries.points.length === 0) {
      return null;
    }
    const width = 640;
    const height = 240;
    const leftPad = 40;
    const rightPad = 20;
    const topPad = 18;
    const bottomPad = 40;
    const innerWidth = width - leftPad - rightPad;
    const innerHeight = height - topPad - bottomPad;
    const values = selectedWeekSeries.points.map((point) => point.value);
    const maxValue = Math.max(...values, selectedWeekSeries.average, 1);
    const toX = (index: number) => {
      if (selectedWeekSeries.points.length === 1) {
        return leftPad + innerWidth / 2;
      }
      return leftPad + (innerWidth * index) / (selectedWeekSeries.points.length - 1);
    };
    const toY = (value: number) => topPad + innerHeight - (value / maxValue) * innerHeight;
    const path = selectedWeekSeries.points
      .map((point, index) => `${index === 0 ? 'M' : 'L'} ${toX(index)} ${toY(point.value)}`)
      .join(' ');
    return {
      width,
      height,
      leftPad,
      rightPad,
      topPad,
      bottomPad,
      innerHeight,
      toX,
      toY,
      path,
      averageY: toY(selectedWeekSeries.average),
      maxValue,
    };
  }, [selectedWeekSeries]);

  useEffect(() => {
    setHoveredWeekPointDate(null);
  }, [mode, weekMetric, currentDate]);

  const handleAnalyze = async (
    force = false,
    analyzeMode = mode,
    analyzeStart = dateRange.start,
    analyzeEnd = dateRange.end,
    analyzeItems = filteredItems,
  ) => {
    if (analyzeItems.length === 0) {
      setRuntimeAnalysisState(IDLE_ANALYSIS_STATE);
      return;
    }

    const selectedLogIds = getSelectedLogIdsForAnalysis(analyzeItems, logEntryIds);
    const cacheKey = buildInsightsCacheKey(
      analyzeMode,
      analyzeStart,
      analyzeEnd,
      selectedLogIds,
    );
    if (!force && insightsCache[cacheKey]) {
      setRuntimeAnalysisState(insightsCache[cacheKey]);
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const loadingTimeout = setTimeout(() => {
      if (!abortController.signal.aborted) {
        setRuntimeAnalysisState((prev) => ({
          ...prev,
          status: 'loading'
        }));
      }
    }, 300);

    try {
      const response = await analyzeInsights({
        mode: analyzeMode,
        selectedLogIds: selectedLogIds.length > 0 ? selectedLogIds : undefined,
        dateRange: { start: analyzeStart, end: analyzeEnd },
        cacheKey,
      }, abortController.signal);

      clearTimeout(loadingTimeout);

      if (abortController.signal.aborted) return;

      if (response.data) {
        const newState = { status: 'success' as const, data: response.data };
        onInsightsCacheUpdate((prev) => {
          const rangeKey = getNormalizedRangeKeyFromCacheKey(cacheKey);
          if (!rangeKey) {
            return { ...prev, [cacheKey]: newState };
          }
          return {
            ...prev,
            [cacheKey]: newState,
            [rangeKey]: newState,
          };
        });
        setRuntimeAnalysisState(newState);
      } else {
        setRuntimeAnalysisState({
          status: 'error',
          message: '分析服务返回了空数据，请稍后重试。',
          retryable: true,
        });
      }
    } catch (error) {
      clearTimeout(loadingTimeout);

      if (abortController.signal.aborted) return;

      if (error instanceof InsightsApiError) {
        // #region agent log
        fetch('http://127.0.0.1:7693/ingest/2b8ec8af-3a30-41dc-a691-2ee12f18fa1a',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'9096da'},body:JSON.stringify({sessionId:'9096da',location:'Explorer.tsx:handleAnalyze',message:'Insights API error',data:{msg:error.message,status:error.status,retryable:error.retryable},timestamp:Date.now()})}).catch(()=>{});
        // #endregion
        setRuntimeAnalysisState({
          status: 'error',
          message: error.message,
          retryable: error.retryable,
        });
      } else {
        setRuntimeAnalysisState({
          status: 'error',
          message: error instanceof Error ? error.message : '暂时无法生成分析，请稍后重试。',
          retryable: true,
        });
      }
    }
  };

  useEffect(() => {
    if (previousCacheKeyRef.current === '') {
      previousCacheKeyRef.current = currentCacheKey;
      return;
    }
    if (previousCacheKeyRef.current === currentCacheKey) {
      return;
    }
    previousCacheKeyRef.current = currentCacheKey;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setRuntimeAnalysisState(IDLE_ANALYSIS_STATE);
  }, [currentCacheKey]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return (
    <div className="flex h-full min-h-0 flex-1 overflow-hidden bg-[#FFFDF5]">
      <main className="flex min-h-0 flex-1 overflow-hidden">
        <section className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-6 py-6 md:px-8 md:py-8">
          <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="flex-1">
                  <h1 className="font-serif-brand text-3xl font-bold text-[#4A453E] md:text-4xl">
                    Insights
                  </h1>
                  <p className="mt-3 max-w-2xl text-sm leading-7 text-[#4A453E]/60 md:text-base">
                    {modeAIPanelDescription}
                  </p>
                </div>
              </div>

              <div className="flex flex-col gap-4 md:flex-row md:items-center">
                <div className="inline-flex items-center gap-1 rounded-full border border-[#4A453E]/10 bg-[#FFFDF9] p-1 shadow-sm">
                  <button
                    type="button"
                    onClick={() => setMode('day')}
                    className={`rounded-full px-4 py-1.5 text-sm font-bold transition-all ${
                      mode === 'day' ? 'bg-[#4A453E] text-white shadow-md' : 'text-[#4A453E]/60 hover:bg-[#4A453E]/5'
                    }`}
                  >
                    日分析
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode('week')}
                    className={`rounded-full px-4 py-1.5 text-sm font-bold transition-all ${
                      mode === 'week' ? 'bg-[#4A453E] text-white shadow-md' : 'text-[#4A453E]/60 hover:bg-[#4A453E]/5'
                    }`}
                  >
                    周分析
                  </button>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="date"
                    value={currentDate}
                    onChange={(event) => {
                      const nextDate = event.target.value;
                      if (nextDate) {
                        setCurrentDate(nextDate);
                        onAnalysisDateChange?.(nextDate);
                      }
                    }}
                    className="rounded-full border border-[#FF8A65]/25 bg-[#FFF7F2] px-3 py-2 text-[11px] font-bold text-[#FF8A65] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15"
                  />
                  {mode === 'week' && (
                    <span className="text-xs font-bold text-[#4A453E]/60">
                      {weekStart} 至 {weekEnd}
                    </span>
                  )}
                </div>
              </div>
              <p className="text-xs font-semibold text-[#4A453E]/55">
                {modeScopeDescription}
              </p>
            </div>

            {filteredItems.length === 0 ? (
              <div className="mt-8 flex flex-col items-center justify-center rounded-[32px] border border-dashed border-[#4A453E]/10 bg-white/40 py-20 text-center">
                <div className="mb-4 inline-flex size-16 items-center justify-center rounded-full bg-white">
                  <span className="material-symbols-outlined text-4xl text-[#4A453E]/20">
                    restaurant_menu
                  </span>
                </div>
                <h3 className="text-lg font-bold text-[#4A453E]">暂无可分析的饮食记录</h3>
                <p className="mt-2 max-w-sm text-sm text-[#4A453E]/50">
                  在当前时间段内没有找到饮食记录，先去 Assistant 记录你的第一餐吧！
                </p>
                <button
                  type="button"
                  onClick={onBack}
                  className="mt-6 rounded-full bg-[#FF8A65] px-6 py-2.5 text-sm font-bold text-white shadow-md transition-all hover:bg-[#FF8A65]/90"
                >
                  返回 Food Log
                </button>
              </div>
            ) : (
              <div className={`transition-opacity duration-300 ${analysisState.status === 'loading' ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <div className="rounded-[28px] border border-[#4A453E]/08 bg-white p-6 shadow-sm">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                        总热量
                      </p>
                    </div>
                    <div className="flex flex-col items-center justify-center pt-2">
                      <div className="relative flex h-48 w-48 items-center justify-center rounded-full bg-[#FFF7F2]">
                        <svg
                          className="h-40 w-40 -rotate-90"
                          viewBox="0 0 140 140"
                        >
                          {(() => {
                            const radius = 60;
                            const circumference = 2 * Math.PI * radius;
                            const baseOffset = isExceeded ? 0 : circumference * (1 - progressRatio);
                            const overRatio = isExceeded ? Math.min((intake - targetCalories) / targetCalories, 1) : 0;
                            const overOffset = circumference * (1 - overRatio);
                            
                            return (
                              <>
                                <circle
                                  cx="70"
                                  cy="70"
                                  r={radius}
                                  fill="none"
                                  stroke="#F5E7DD"
                                  strokeWidth="10"
                                />
                                <circle
                                  cx="70"
                                  cy="70"
                                  r={radius}
                                  fill="none"
                                  stroke="#FF8A65"
                                  strokeWidth="10"
                                  strokeDasharray={circumference}
                                  strokeDashoffset={baseOffset}
                                  strokeLinecap="round"
                                />
                                {isExceeded && (
                                  <circle
                                    cx="70"
                                    cy="70"
                                    r={radius}
                                    fill="none"
                                    stroke="#C25235"
                                    strokeWidth="10"
                                    strokeDasharray={circumference}
                                    strokeDashoffset={overOffset}
                                    strokeLinecap="round"
                                  />
                                )}
                              </>
                            );
                          })()}
                        </svg>
                        <div className="absolute flex flex-col items-center justify-center text-[#4A453E]">
                          <span className={`font-serif-brand text-4xl font-bold ${isExceeded ? 'text-[#C25235]' : ''}`}>
                            {formatCalories(intake)}
                          </span>
                          <span className="mt-1 text-xs font-semibold text-[#4A453E]/50">
                            / {targetCalories} kcal
                          </span>
                        </div>
                      </div>
                      <p className={`mt-5 text-sm font-semibold ${isExceeded ? 'text-[#C25235]' : 'text-[#4A453E]/55'}`}>
                        {isExceeded 
                          ? `已超出 ${formatCalories(exceededCalories)} kcal` 
                          : `剩余 ${formatCalories(remainingCalories)} kcal`}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-col rounded-[28px] border border-[#4A453E]/08 bg-white p-6 shadow-sm">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                      营养素分布
                    </p>

                    <div className="flex flex-1 flex-col justify-evenly pt-2">
                      {[
                        {
                          label: '蛋白质',
                          value: totalProtein,
                          icon: 'protein',
                          color: '#FF9A76',
                          backendRatio: agg?.proteinRatio,
                        },
                        {
                          label: '碳水化合物',
                          value: totalCarbs,
                          icon: 'carbs',
                          color: '#FFD166',
                          backendRatio: agg?.carbsRatio,
                        },
                        {
                          label: '脂肪',
                          value: totalFat,
                          icon: 'fat',
                          color: '#A1887F',
                          backendRatio: agg?.fatRatio,
                        },
                      ].map((macro) => {
                        const macroTotal = totalProtein + totalCarbs + totalFat;
                        const percent = macro.backendRatio != null
                          ? macro.backendRatio
                          : macroTotal > 0 ? getPercent(macro.value, macroTotal) : 0;

                        return (
                          <div
                            key={macro.label}
                            className="flex items-center gap-3"
                          >
                            {/* 左侧极简线条图标 */}
                            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border border-[#4A453E]/5 bg-[#FFF7EF] text-[#4A453E]/60">
                                {macro.icon === 'protein' && (
                                  <svg
                                    viewBox="0 0 24 24"
                                    className="h-4 w-4"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="1.4"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                  >
                                    <path d="M6 5c1.5-1 3.5-1 5 0l4 2.5c1.2.8 1.7 2.4 1 3.7l-1.8 3.3c-.8 1.4-2.6 2-4.1 1.3L6 14.5C4.8 13.9 4.3 12.4 5 11.1L6.8 7.8" />
                                    <path d="M9 7.2 11.8 9" />
                                  </svg>
                                )}
                                {macro.icon === 'carbs' && (
                                  <svg
                                    viewBox="0 0 24 24"
                                    className="h-4 w-4"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="1.4"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                  >
                                    <path d="M5 16c0-4.5 3.2-8.5 7-10 3.8 1.5 7 5.5 7 10 0 2-1.5 3.5-3.5 3.5h-7C6.5 19.5 5 18 5 16Z" />
                                    <path d="M9 13h6" />
                                    <path d="M9 16h4" />
                                  </svg>
                                )}
                                {macro.icon === 'fat' && (
                                  <svg
                                    viewBox="0 0 24 24"
                                    className="h-4 w-4"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="1.4"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                  >
                                    <path d="M12 4C9.5 7.2 7 10.5 7 13.5 7 16.5 9 19 12 19s5-2.5 5-5.5C17 10.5 14.5 7.2 12 4Z" />
                                    <path d="M11 11.5c.6-.3 1.3-.3 1.9 0" />
                                  </svg>
                                )}
                            </div>

                            {/* 中间名称和进度条区域 + 右侧数据组 */}
                            <div className="flex min-w-0 flex-1 items-center">
                              {/* 中间部分：名称 + 进度条 */}
                              <div className="mr-3 flex min-w-0 flex-1 flex-col">
                                <span className="font-serif-brand text-sm font-semibold text-[#4A453E]">
                                  {macro.label}
                                </span>
                                <div className="mt-2 h-[6px] w-[88%] overflow-hidden rounded-full bg-[#F5F2ED]">
                                  <div
                                    className="h-full rounded-full transition-all"
                                    style={{
                                      width: `${percent}%`,
                                      backgroundColor: macro.color,
                                    }}
                                  />
                                </div>
                              </div>

                              {/* 右侧数据组：克数 + 百分比，右对齐 */}
                              <div className="min-w-[56px] text-right">
                                <span className="block font-sans text-sm font-extrabold text-[#3F3932]">
                                  {formatNumber(macro.value)} g
                                </span>
                                <span className="mt-0.5 block font-sans text-[12px] font-semibold text-[#4A453E]/60">
                                  {percent.toFixed(0)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
            </div>

            {mode === 'week' && weeklyTrend && (
              <div className="mt-4 rounded-[28px] border border-[#4A453E]/08 bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                    周趋势图
                  </h2>
                  <span className="rounded-full bg-[#FFF7EF] px-3 py-1 text-[11px] font-semibold text-[#FF8A65]">
                    活跃记录 {weeklyTrend.activeDays}/{weeklyTrend.points.length} 天
                  </span>
                </div>
                <p className="mt-2 text-xs leading-6 text-[#4A453E]/60">
                  {weeklyTrend.trendLabel} · {weeklyTrend.volatilityLabel} · {weeklyTrend.cycleLabel}
                </p>

                <div className="mt-4 inline-flex items-center gap-1 rounded-full border border-[#4A453E]/10 bg-[#FFFDF9] p-1">
                  {[
                    { key: 'calories' as const, label: '热量' },
                    { key: 'protein' as const, label: '蛋白质' },
                    { key: 'carbs' as const, label: '碳水' },
                    { key: 'fat' as const, label: '脂肪' },
                  ].map((metric) => (
                    <button
                      key={metric.key}
                      type="button"
                      onClick={() => setWeekMetric(metric.key)}
                      className={`rounded-full px-3 py-1 text-xs font-bold transition-all ${
                        weekMetric === metric.key
                          ? 'bg-[#4A453E] text-white shadow-sm'
                          : 'text-[#4A453E]/65 hover:bg-[#4A453E]/5'
                      }`}
                    >
                      {metric.label}
                    </button>
                  ))}
                </div>

                <div className="mt-4 rounded-2xl border border-[#4A453E]/7 bg-[#FFFDF8] p-4">
                  {selectedWeekSeries && weekChartModel && (
                    <>
                      <div className="relative">
                        <svg
                          viewBox={`0 0 ${weekChartModel.width} ${weekChartModel.height}`}
                          className="h-[230px] w-full"
                          role="img"
                          aria-label={`${selectedWeekSeries.label}周趋势折线图`}
                        >
                          <line
                            x1={weekChartModel.leftPad}
                            y1={weekChartModel.averageY}
                            x2={weekChartModel.width - weekChartModel.rightPad}
                            y2={weekChartModel.averageY}
                            stroke="#A1887F"
                            strokeDasharray="4 4"
                            strokeWidth="1.2"
                          />
                          <path
                            d={weekChartModel.path}
                            fill="none"
                            stroke="#FF8A65"
                            strokeWidth="3"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                          {selectedWeekSeries.points.map((point, index) => {
                            const x = weekChartModel.toX(index);
                            const y = weekChartModel.toY(point.value);
                            const isPeak = selectedWeekSeries.peakPoint?.date === point.date;
                            const isLow = selectedWeekSeries.lowPoint?.date === point.date;
                            const isHovered = hoveredWeekPointDate === point.date;
                            const pointColor = isPeak ? '#C25235' : isLow ? '#4CAF50' : '#FF8A65';
                            return (
                              <g key={point.date}>
                                <circle
                                  cx={x}
                                  cy={y}
                                  r={isHovered ? 6 : 4}
                                  fill={pointColor}
                                  onMouseEnter={() => setHoveredWeekPointDate(point.date)}
                                  onMouseLeave={() => setHoveredWeekPointDate((current) => (
                                    current === point.date ? null : current
                                  ))}
                                  style={{ cursor: 'pointer' }}
                                />
                                <text
                                  x={x}
                                  y={weekChartModel.height - 14}
                                  textAnchor="middle"
                                  fontSize="11"
                                  fill="#6E655B"
                                >
                                  {point.label}
                                </text>
                              </g>
                            );
                          })}
                        </svg>

                        {(() => {
                          const hoverIndex = selectedWeekSeries.points.findIndex(
                            (point) => point.date === hoveredWeekPointDate,
                          );
                          if (hoverIndex < 0) {
                            return null;
                          }
                          const hoverPoint = selectedWeekSeries.points[hoverIndex];
                          const tooltipWidth = 104;
                          const anchorX = weekChartModel.toX(hoverIndex);
                          const minAnchorX = tooltipWidth / 2 + 10;
                          const maxAnchorX = weekChartModel.width - tooltipWidth / 2 - 10;
                          const safeAnchorX = Math.min(Math.max(anchorX, minAnchorX), maxAnchorX);
                          const tooltipLeft = (safeAnchorX / weekChartModel.width) * 100;
                          const tooltipTop = (weekChartModel.toY(hoverPoint.value) / weekChartModel.height) * 100;
                          const tooltipValue = selectedWeekSeries.unit === 'kcal'
                            ? `${Math.round(hoverPoint.value)} kcal`
                            : `${formatNumber(hoverPoint.value)} g`;
                          return (
                            <div
                              className="pointer-events-none absolute z-20 rounded-lg border border-[#4A453E]/10 bg-white px-3 py-2 text-[11px] shadow-md"
                              style={{
                                left: `${tooltipLeft}%`,
                                top: `${tooltipTop}%`,
                                transform: 'translate(-50%, -115%)',
                              }}
                            >
                              <p className="font-semibold text-[#4A453E]/70">
                                {`${hoverPoint.label} (${hoverPoint.date.slice(5)})`}
                              </p>
                              <p className="mt-0.5 font-bold text-[#4A453E]">{tooltipValue}</p>
                            </div>
                          );
                        })()}
                      </div>
                    </>
                  )}
                </div>

                {selectedWeekSeries && (
                  <div className="mt-3 grid grid-cols-1 gap-2 text-center text-xs font-semibold sm:grid-cols-3">
                    <div className="rounded-xl bg-white px-3 py-2 text-[#4A453E]/70">
                      平均 {Math.round(selectedWeekSeries.average)} {selectedWeekSeries.unit}
                    </div>
                    <div className="rounded-xl bg-[#FDECE7] px-3 py-2 text-[#C25235]">
                      {selectedWeekSeries.peakPoint
                        ? `最高 ${selectedWeekSeries.peakPoint.label} ${Math.round(selectedWeekSeries.peakPoint.value)} ${selectedWeekSeries.unit}`
                        : '最高 -'}
                    </div>
                    <div className="rounded-xl bg-[#EAF6EC] px-3 py-2 text-[#2E7D32]">
                      {selectedWeekSeries.lowPoint
                        ? `最低 ${selectedWeekSeries.lowPoint.label} ${Math.round(selectedWeekSeries.lowPoint.value)} ${selectedWeekSeries.unit}`
                        : '最低 -'}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="mt-4 rounded-[28px] border border-[#4A453E]/08 bg-white p-6 shadow-sm">
              <div className="mb-5 flex items-center justify-between">
                <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                  已选菜品
                </h2>
                <div className="inline-flex items-center gap-1 rounded-full bg-[#FFF7EF] px-3 py-1 text-[11px] font-semibold text-[#FF8A65]">
                  <span className="material-symbols-outlined text-[14px]">restaurant</span>
                  <span>{filteredItems.length} 项</span>
                </div>
              </div>

              {filteredItems.length > 0 ? (
                <div className="space-y-3">
                  {filteredItems.map((item) => (
                    <div
                      key={item.basketId}
                      className="group flex items-center justify-between rounded-[22px] border border-[#4A453E]/06 bg-[#FFFDF9] p-4 transition-colors hover:bg-white"
                    >
                      <div className="flex min-w-0 items-center gap-4">
                        <div className="size-12 overflow-hidden rounded-[14px] border border-[#4A453E]/05 bg-[#F7F3E9]">
                          <FoodLogImage
                            src={item.image}
                            alt={item.name}
                            compact
                            className="h-full w-full object-cover"
                          />
                        </div>

                        <div className="min-w-0">
                          <h4 className="truncate text-sm font-bold text-[#4A453E]">{item.name}</h4>
                          <p className="mt-1 text-xs text-[#4A453E]/50">
                            {formatCalories(item.calories)} kcal
                          </p>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => onRemove(item.basketId)}
                        className="flex size-9 items-center justify-center rounded-full text-[#4A453E]/20 transition-all hover:bg-red-50 hover:text-red-500"
                      >
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex min-h-[120px] flex-col items-center justify-center rounded-[22px] bg-[#FFFDF9] px-4 py-6 text-center">
                  <span className="mb-2 text-sm font-semibold text-[#4A453E]">
                    该日期暂无记录
                  </span>
                  <p className="text-xs leading-6 text-[#4A453E]/55">
                    从 Food Log 中将已保存的菜品添加到当日分析即可在此显示。
                  </p>
                </div>
              )}
            </div>
            </div>
            )}
          </div>
        </section>

        <aside className="hidden w-[420px] shrink-0 border-l border-[#4A453E]/05 bg-white lg:flex lg:flex-col">
          <div className="border-b border-[#4A453E]/05 px-6 py-6">
            <h3 className="font-serif-brand text-2xl font-bold text-[#4A453E]">
              AI 饮食建议
            </h3>
            <p className="mt-2 text-sm leading-6 text-[#4A453E]/50">
              {modeAIPanelDescription}
            </p>
          </div>

          <div className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-6 py-6">
            {!insightsHistoryLoaded && analysisState.status !== 'loading' && analysisState.status !== 'success' && (
              <div className="flex h-full flex-col items-center justify-center px-4 text-center">
                <div className="mb-5 flex size-16 items-center justify-center rounded-full bg-[#FFF2EC]">
                  <span className="material-symbols-outlined animate-spin text-3xl text-[#FF8A65]/70">
                    progress_activity
                  </span>
                </div>
                <p className="text-sm font-semibold leading-7 text-[#4A453E]/60">
                  正在加载已保存的分析…
                </p>
              </div>
            )}
            {insightsHistoryLoaded && analysisState.status === 'idle' && (
              <div className="flex h-full flex-col items-center justify-center px-4 text-center">
                <div className="mb-5 flex size-16 items-center justify-center rounded-full bg-[#FFF2EC]">
                  <span className="material-symbols-outlined text-3xl text-[#FF8A65]/50">
                    chat
                  </span>
                </div>
                <p className="text-sm leading-7 text-[#4A453E]/50">
                  {modeIdleHint}
                </p>
              </div>
            )}

            {analysisState.status === 'loading' && (
              <div className="flex h-full flex-col items-center justify-center px-4 text-center">
                <div className="mb-5 flex size-16 items-center justify-center rounded-full bg-[#FFF2EC]">
                  <span className="material-symbols-outlined animate-spin text-3xl text-[#FF8A65]">
                    progress_activity
                  </span>
                </div>
                <p className="text-sm font-semibold leading-7 text-[#4A453E]/60">
                  {modeLoadingHint}
                </p>
              </div>
            )}

            {analysisState.status === 'error' && (
              <div className="flex h-full flex-col items-center justify-center px-4 text-center">
                <div className="mb-5 flex size-16 items-center justify-center rounded-full bg-red-50">
                  <span className="material-symbols-outlined text-3xl text-red-400">
                    error
                  </span>
                </div>
                <p className="text-sm font-semibold text-[#4A453E]">分析失败</p>
                <p className="mt-2 text-sm leading-7 text-[#4A453E]/55">
                  {analysisState.message}
                </p>
                {analysisState.retryable && (
                  <button
                    type="button"
                    onClick={() => void handleAnalyze(true)}
                    className="mt-5 flex items-center gap-2 rounded-full bg-[#FF8A65] px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-[#FF8A65]/20 transition-all hover:bg-[#FF8A65]/90"
                  >
                    <span className="material-symbols-outlined text-[16px]">refresh</span>
                    重试
                  </button>
                )}
              </div>
            )}

            {analysisState.status === 'success' && (
              <div className="space-y-6">
                <div>
                  <h4 className="mb-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[#4A453E]/35">
                    <span className="material-symbols-outlined text-[16px] text-[#FF8A65]">summarize</span>
                    综合评估
                  </h4>
                  <p className="text-sm leading-7 text-[#4A453E]/75">
                    {analysisState.data.ai.summary}
                  </p>
                </div>

                {analysisState.data.ai.risks.length > 0 && (
                  <div>
                    <h4 className="mb-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[#4A453E]/35">
                      <span className="material-symbols-outlined text-[16px] text-[#C25235]">warning</span>
                      风险提示
                    </h4>
                    <ul className="space-y-2">
                      {analysisState.data.ai.risks.map((risk, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-sm leading-7 text-[#4A453E]/70">
                          <span className="mt-1.5 inline-block size-1.5 shrink-0 rounded-full bg-[#C25235]/50" />
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysisState.data.ai.actions.length > 0 && (
                  <div>
                    <h4 className="mb-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[#4A453E]/35">
                      <span className="material-symbols-outlined text-[16px] text-[#4CAF50]">task_alt</span>
                      改善建议
                    </h4>
                    <ol className="space-y-2">
                      {analysisState.data.ai.actions.map((action, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-sm leading-7 text-[#4A453E]/70">
                          <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-[#4CAF50]/10 text-[10px] font-bold text-[#4CAF50]">
                            {i + 1}
                          </span>
                          {action}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="border-t border-[#4A453E]/05 bg-[#FFFDF8] px-6 py-6">
            <button
              type="button"
              onClick={() => void handleAnalyze(shouldForceReanalyze(analysisState.status))}
              disabled={analysisState.status === 'loading' || filteredItems.length === 0}
              className={`flex h-12 w-full items-center justify-center gap-2 rounded-full px-5 text-sm font-bold text-white shadow-lg transition-all ${
                analysisState.status === 'loading' || filteredItems.length === 0
                  ? 'cursor-not-allowed bg-[#4A453E]/20 shadow-none'
                  : 'bg-[#FF8A65] shadow-[#FF8A65]/20 hover:bg-[#FF8A65]/90'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">
                {analysisState.status === 'loading' ? 'progress_activity' : 'forum'}
              </span>
              {getInsightsAnalyzeButtonText(analysisState.status, mode)}
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
};

interface SummaryCardProps {
  label: string;
  value: string;
  unit: string;
  accent?: boolean;
}

interface SelectedEntryPanelProps {
  entry: FoodLogEntry;
  isEditing: boolean;
  editDraft: FoodLogEditDraft | null;
  isSavingEdit: boolean;
  isDeleting: boolean;
  onClose: () => void;
  onEdit: () => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onIngredientGramsChange: (ingredientIndex: number, newGrams: string) => void;
  onDelete: () => void;
  onOpenChat: () => void;
  onAddToAnalysis: () => void;
}

const SelectedEntryPanel: React.FC<SelectedEntryPanelProps> = ({
  entry,
  isEditing,
  editDraft,
  isSavingEdit,
  isDeleting,
  onClose,
  onEdit,
  onCancelEdit,
  onSaveEdit,
  onIngredientGramsChange,
  onDelete,
  onOpenChat,
  onAddToAnalysis,
}) => {
  const savedMoment = formatSavedMoment(entry.savedAt);
  const totalCalories = isEditing && editDraft
    ? getDraftTotalCalories(editDraft)
    : entry.calories;

  return (
    <div className="flex min-h-0 w-full flex-1 flex-col bg-white">
      <div className="shrink-0 border-b border-[#4A453E]/05 px-5 py-5 md:px-6 md:py-6">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="min-w-0">
            <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#FF8A65]">
              {isEditing ? '编辑克重' : 'Saved Entry'}
            </span>
            <p className="mt-2 text-[11px] font-semibold text-[#4A453E]/35">
              Last updated {savedMoment.date} / {savedMoment.time}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {!isEditing && (
              <button
                type="button"
                onClick={onEdit}
                className="flex size-9 items-center justify-center rounded-full text-[#4A453E]/40 transition-all hover:bg-[#FF8A65]/5 hover:text-[#FF8A65]"
                title="Edit saved entry"
              >
                <span className="material-symbols-outlined text-lg">edit</span>
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              disabled={isSavingEdit}
              className="shrink-0 rounded-full p-1 text-[#4A453E]/20 transition-colors hover:bg-[#4A453E]/5 hover:text-[#4A453E] disabled:cursor-not-allowed disabled:opacity-40"
            >
              <span className="material-symbols-outlined text-xl">close</span>
            </button>
          </div>
        </div>

        <h2 className="text-balance font-serif-brand text-[28px] font-bold italic leading-[1.14] text-[#4A453E] md:text-[34px]">
          {entry.name}
        </h2>
      </div>

      <div className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-5 py-5 md:px-6 md:py-6">
        <div className="space-y-5 md:space-y-6">
          <div className="relative aspect-[4/3] overflow-hidden rounded-[24px] border border-[#4A453E]/05 shadow-sm md:aspect-video md:rounded-[28px]">
            <FoodLogImage
              src={entry.image}
              alt={entry.name}
              className="h-full w-full object-cover"
            />
            {entry.image && (entry.imageSource || entry.imageLicense) && (
              <div
                className="absolute bottom-2 right-2 rounded-lg bg-[#4A453E]/60 px-2 py-1 text-[10px] font-medium text-white/90 backdrop-blur-sm"
                title={
                  [entry.imageSource, entry.imageLicense].filter(Boolean).join(' · ')
                }
              >
                {entry.imageSource || entry.imageLicense}
              </div>
            )}
          </div>

          <div className="rounded-[24px] border border-[#4A453E]/8 bg-white p-5 shadow-sm md:rounded-[28px] md:p-6">
            <h5 className="mb-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[#4A453E]/40">
              <span className="material-symbols-outlined text-lg text-[#FF8A65]">
                notes
              </span>
              Description
            </h5>

            <p className="text-sm leading-7 text-[#4A453E]/60">
              {entry.description}
            </p>
          </div>

          <div className="rounded-[24px] border border-[#4A453E]/8 bg-[#FFFDF5] p-5 shadow-sm md:rounded-[28px] md:p-6">
            <div className="mb-5 flex flex-col gap-2 md:mb-6 md:flex-row md:items-center md:justify-between">
              <h5 className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[#4A453E]/40">
                <span className="material-symbols-outlined text-lg text-[#FF8A65]">
                  analytics
                </span>
                Nutrition Details
              </h5>
              <span className="font-serif-brand text-[26px] font-bold italic leading-none text-[#4A453E] md:text-[28px]">
                {formatCalories(totalCalories)}{' '}
                <span className="font-sans text-xs font-bold not-italic uppercase tracking-wide text-[#4A453E]/20">
                  kcal
                </span>
              </span>
            </div>

            {isEditing && editDraft ? (
              <div className="mb-5 md:mb-6">
                <p className="mb-3 text-[10px] font-bold text-[#FF8A65]/70">
                  调整克重后，热量与营养素自动按比例重新计算
                </p>
                <div className="space-y-2.5">
                  {editDraft.ingredients.map((item, index) => {
                    const currentGrams = extractGramsFromPortion(item.portion);
                    const originalItem = editDraft.originalIngredients[index];
                    const unit = originalItem ? getPortionUnit(originalItem.portion) : 'g';
                    return (
                      <div
                        key={`edit-ingredient-${index}`}
                        className="rounded-[16px] border border-[#4A453E]/06 bg-[#FFFDF9] p-3.5"
                      >
                        <div className="mb-2 flex items-center justify-between gap-3">
                          <span className="text-[13px] font-bold text-[#4A453E]">{item.name}</span>
                          <span className="shrink-0 text-[11px] font-bold text-[#FF8A65]">{formatEnergyString(item.energy)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-[#4A453E]/35">份量</span>
                          <input
                            type="number"
                            min="0"
                            step="1"
                            value={currentGrams || ''}
                            placeholder="0"
                            onChange={(event) => onIngredientGramsChange(index, event.target.value)}
                            className="w-20 rounded-[10px] border border-[#FF8A65]/20 bg-white px-3 py-1.5 text-center text-[13px] font-bold text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/10"
                          />
                          <span className="text-[10px] font-bold text-[#4A453E]/35">{unit}</span>
                          {hasAnyIngredientMacro(editDraft.originalIngredients) && (
                            <div className="ml-auto flex items-center gap-2 text-[10px] text-[#4A453E]/45">
                              {item.protein && <span>蛋白 {item.protein}</span>}
                              {item.carbs && <span>碳水 {item.carbs}</span>}
                              {item.fat && <span>脂肪 {item.fat}</span>}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="mb-5 md:mb-6">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-[#4A453E]/08 text-[9px] font-bold uppercase tracking-[0.14em] text-[#4A453E]/35">
                      <th className="pb-2.5 pr-2">食材</th>
                      <th className="pb-2.5 px-2">份量</th>
                      <th className="pb-2.5 pl-2 text-right">热量</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#4A453E]/05">
                    {entry.breakdown.map((item, index) => (
                      <tr key={`${item.name}-${index}`} className="group/row">
                        <td className="py-2.5 pr-2 text-[13px] font-bold text-[#4A453E] transition-colors group-hover/row:text-[#FF8A65]">
                          {item.name}
                        </td>
                        <td className="py-2.5 px-2 text-[10px] font-bold uppercase tracking-wider text-[#4A453E]/40">
                          {item.portion}
                        </td>
                        <td className="py-2.5 pl-2 text-right text-[11px] font-bold text-[#4A453E]/80">
                          {formatEnergyString(item.energy)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

          </div>

          {(() => {
            const showMacro = isEditing && editDraft
              ? hasAnyIngredientMacro(editDraft.originalIngredients)
              : hasMacroData(entry);
            if (!showMacro) {
              return (
                <div className="rounded-[20px] border border-dashed border-[#4A453E]/10 bg-white/50 px-4 py-3 text-[13px] leading-6 text-[#4A453E]/55">
                  营养成分表暂无数据。新分析的菜品将自动包含三大营养素信息。
                </div>
              );
            }
            const draftProtein = editDraft?.ingredients.reduce(
              (s, it) => s + extractNutritionValue(it.protein), 0,
            ) ?? 0;
            const draftCarbs = editDraft?.ingredients.reduce(
              (s, it) => s + extractNutritionValue(it.carbs), 0,
            ) ?? 0;
            const draftFat = editDraft?.ingredients.reduce(
              (s, it) => s + extractNutritionValue(it.fat), 0,
            ) ?? 0;
            return (
              <NutritionFactsLabel
                protein={isEditing && editDraft ? `${formatNumber(draftProtein)} g` : entry.protein}
                carbs={isEditing && editDraft ? `${formatNumber(draftCarbs)} g` : entry.carbs}
                fat={isEditing && editDraft ? `${formatNumber(draftFat)} g` : entry.fat}
              />
            );
          })()}
        </div>
      </div>

      <div className="shrink-0 border-t border-[#4A453E]/05 bg-white px-5 py-4 md:px-6 md:py-6">
        <div className="flex flex-col gap-3">
          {isEditing ? (
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onCancelEdit}
                disabled={isSavingEdit}
                className="flex-1 rounded-full bg-[#4A453E]/5 px-4 py-3.5 text-sm font-bold text-[#4A453E]/45 transition-all hover:bg-[#4A453E]/10 disabled:cursor-not-allowed disabled:opacity-70"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={onSaveEdit}
                disabled={isSavingEdit}
                className="flex-[1.5] rounded-full bg-[#FF8A65] px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-[#FF8A65]/20 transition-all hover:bg-[#FF8A65]/90 disabled:cursor-wait disabled:opacity-80"
              >
                {isSavingEdit ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          ) : (
            <>
              <button
                type="button"
                onClick={onDelete}
                disabled={isDeleting}
                className={`flex h-11 w-full items-center justify-center gap-2 rounded-full border px-5 text-sm font-bold transition-all ${
                  isDeleting
                    ? 'cursor-wait border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E]/45'
                    : 'border-red-200 bg-red-50 text-red-500 hover:bg-red-100'
                }`}
              >
                <span className="material-symbols-outlined text-lg">delete</span>
                {isDeleting ? 'Removing...' : 'Remove Entry'}
              </button>

              <button
                type="button"
                onClick={onOpenChat}
                disabled={!entry.sessionId}
                className={`flex h-12 w-full items-center justify-center gap-2 rounded-full px-5 text-sm font-bold text-white shadow-lg transition-all ${
                  entry.sessionId
                    ? 'bg-[#FF8A65] shadow-[#FF8A65]/20 hover:bg-[#FF8A65]/90'
                    : 'cursor-not-allowed bg-[#4A453E]/20 shadow-none'
                }`}
              >
                <span className="material-symbols-outlined text-lg">forum</span>
                {entry.sessionId ? 'Open Source Chat' : 'Source Chat Deleted'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const SummaryCard: React.FC<SummaryCardProps> = ({ label, value, unit, accent = false }) => (
  <div
    className={`rounded-[24px] border p-6 shadow-sm ${
      accent
        ? 'border-[#FF8A65]/10 bg-[#FF8A65]/5'
        : 'border-[#4A453E]/5 bg-white/60'
    }`}
  >
    <span
      className={`mb-2 block text-[10px] font-bold uppercase tracking-widest ${
        accent ? 'text-[#FF8A65]/60' : 'text-[#4A453E]/40'
      }`}
    >
      {label}
    </span>
    <div className="flex items-baseline gap-1">
      <span
        className={`font-serif-brand text-3xl font-bold ${
          accent ? 'text-[#FF8A65]' : 'text-[#4A453E]'
        }`}
      >
        {value}
      </span>
      <span
        className={`text-xs font-bold uppercase ${
          accent ? 'text-[#FF8A65]/40' : 'text-[#4A453E]/30'
        }`}
      >
        {unit}
      </span>
    </div>
  </div>
);

interface NutritionFactsLabelProps {
  protein?: string | null;
  carbs?: string | null;
  fat?: string | null;
}

const NutritionFactsLabel: React.FC<NutritionFactsLabelProps> = ({
  protein,
  carbs,
  fat,
}) => {
  const proteinNum = extractNutritionValue(protein);
  const carbsNum = extractNutritionValue(carbs);
  const fatNum = extractNutritionValue(fat);

  const proteinKcal = proteinNum * 4;
  const carbsKcal = carbsNum * 4;
  const fatKcal = fatNum * 9;
  const macroKcalTotal = proteinKcal + carbsKcal + fatKcal;
  const proteinPct = macroKcalTotal > 0 ? Math.round((proteinKcal / macroKcalTotal) * 100) : 0;
  const carbsPct = macroKcalTotal > 0 ? Math.round((carbsKcal / macroKcalTotal) * 100) : 0;
  const fatPct = macroKcalTotal > 0 ? Math.round((fatKcal / macroKcalTotal) * 100) : 0;

  const macros = [
    { label: '蛋白质', sub: 'Protein', value: proteinNum, pct: proteinPct, color: '#FF9A76' },
    { label: '碳水化合物', sub: 'Carbs', value: carbsNum, pct: carbsPct, color: '#FFD166' },
    { label: '脂肪', sub: 'Fat', value: fatNum, pct: fatPct, color: '#A1887F' },
  ];

  return (
    <div className="rounded-[24px] border border-[#4A453E]/8 bg-[#FFFDF5] p-5 shadow-sm md:rounded-[28px] md:p-6">
      <h5 className="mb-5 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[#4A453E]/40 md:mb-6">
        <span className="material-symbols-outlined text-lg text-[#FF8A65]">nutrition</span>
        营养成分 / Nutrition Facts
      </h5>

      <div className="mb-5 flex h-2.5 w-full overflow-hidden rounded-full bg-[#F5F2ED] md:mb-6">
        {macros.map((m) => m.pct > 0 && (
          <div
            key={m.label}
            className="h-full transition-all"
            style={{ width: `${m.pct}%`, backgroundColor: m.color }}
          />
        ))}
      </div>

      <div className="space-y-0">
        {macros.map((m, i) => (
          <div
            key={m.label}
            className={`flex items-center justify-between py-2.5 ${
              i < macros.length - 1 ? 'border-b border-[#4A453E]/05' : ''
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span
                className="inline-block size-2 rounded-full"
                style={{ backgroundColor: m.color }}
              />
              <span className="text-[13px] font-bold text-[#4A453E]">{m.label}</span>
            </div>
            <div className="flex items-baseline gap-3">
              <span className="text-[11px] font-bold text-[#4A453E]/80">
                {formatNumber(m.value)} g
              </span>
              <span className="min-w-[32px] text-right text-[10px] font-bold uppercase tracking-wider text-[#4A453E]/40">
                {m.pct}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

interface FoodLogImageProps {
  src?: string;
  alt: string;
  className?: string;
  compact?: boolean;
}

const FoodLogImage: React.FC<FoodLogImageProps> = ({
  src,
  alt,
  className = '',
  compact = false,
}) => {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setHasError(false);
  }, [src]);

  if (!src || hasError) {
    return <ImagePlaceholder compact={compact} />;
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setHasError(true)}
    />
  );
};

interface ImagePlaceholderProps {
  compact?: boolean;
}

const ImagePlaceholder: React.FC<ImagePlaceholderProps> = ({ compact = false }) => (
  <div className={`flex h-full w-full items-center justify-center bg-[#F7F3E9] ${compact ? 'px-2' : 'px-6'}`}>
    <div className="text-center">
      <span className={`material-symbols-outlined text-[#4A453E]/20 ${compact ? 'text-[20px]' : 'text-5xl'}`}>
        image_not_supported
      </span>
      {!compact && (
        <>
          <p className="mt-3 text-sm font-semibold text-[#4A453E]/55">No photo available</p>
          <p className="mt-1 text-xs text-[#4A453E]/35">
            This saved entry was stored without an image.
          </p>
        </>
      )}
    </div>
  </div>
);

function buildEditDraft(entry: FoodLogEntry): FoodLogEditDraft {
  return {
    name: entry.name,
    description: entry.description,
    calories: entry.calories,
    ingredients: entry.breakdown.map((item) => ({ ...item })),
    originalIngredients: entry.breakdown.map((item) => ({ ...item })),
  };
}

function hasMacroData(entry: FoodLogEntry): boolean {
  return Boolean(entry.protein || entry.carbs || entry.fat);
}

function hasAnyIngredientMacro(breakdown: IngredientResult[]): boolean {
  return breakdown.some((item) => item.protein || item.carbs || item.fat);
}

function extractGramsFromPortion(portion: string): number {
  const match = String(portion).match(/(\d+(?:\.\d+)?)\s*(?:g|克|毫升|ml)?/i);
  if (!match) return 0;
  const parsed = Number.parseFloat(match[1]);
  return Number.isFinite(parsed) ? parsed : 0;
}

function getPortionUnit(portion: string): string {
  const unitMatch = String(portion).match(/\d+(?:\.\d+)?\s*(毫升|ml|克|g)/i);
  return unitMatch ? unitMatch[1] : 'g';
}

function getDraftTotalCalories(draft: FoodLogEditDraft): string {
  const total = draft.ingredients.reduce(
    (sum, ingredient) => sum + extractCaloriesValue(ingredient.energy),
    0,
  );

  if (total > 0 || draft.ingredients.length > 0) {
    return String(Math.ceil(total));
  }

  return draft.calories;
}

function extractCaloriesValue(value: string | number): number {
  const match = String(value).match(/(\d+(?:\.\d+)?)/);
  if (!match) {
    return 0;
  }

  const parsed = Number.parseFloat(match[1]);
  return Number.isFinite(parsed) ? Math.ceil(parsed) : 0;
}

function extractNutritionValue(value?: string | null): number {
  if (!value) {
    return 0;
  }

  const match = String(value).match(/(\d+(?:\.\d+)?)/);
  if (!match) {
    return 0;
  }

  const parsed = Number.parseFloat(match[1]);
  return Number.isFinite(parsed) ? parsed : 0;
}

function getPercent(value: number, total: number): number {
  if (total <= 0) {
    return 0;
  }
  return Number(((value / total) * 100).toFixed(2));
}

function formatNumber(value: number): string {
  if (Number.isInteger(value)) {
    return String(value);
  }
  return value.toFixed(1);
}

function formatCalories(value: string | number): string {
  if (typeof value === 'number') {
    return String(Math.round(value));
  }
  return String(Math.round(extractCaloriesValue(value)));
}

function formatEnergyString(energy: string): string {
  const num = extractCaloriesValue(energy);
  return `${Math.round(num)} kcal`;
}

function getWeekRange(dateString: string): { start: string; end: string } {
  const [y, m, d] = dateString.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  const day = date.getDay();
  const diffToMonday = date.getDate() - day + (day === 0 ? -6 : 1);
  
  const monday = new Date(y, m - 1, diffToMonday);
  const sunday = new Date(y, m - 1, diffToMonday + 6);

  const format = (dt: Date) => {
    const yy = dt.getFullYear();
    const mm = String(dt.getMonth() + 1).padStart(2, '0');
    const dd = String(dt.getDate()).padStart(2, '0');
    return `${yy}-${mm}-${dd}`;
  };

  return { start: format(monday), end: format(sunday) };
}


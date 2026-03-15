import React, { useEffect, useState } from 'react';

import {
  buildFoodLogCollectionStats,
  buildFoodLogEditPayload,
  formatSavedMoment,
  sortFoodLogEntries,
} from '../app/foodLogFavorites';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { FoodLogEntry, FoodLogPatchInput, IngredientResult } from '../types/types';

interface ExplorerProps {
  logEntries: FoodLogEntry[];
  onNavigateToSession: (sessionId: string) => void;
  onDeleteFoodLog: (entryId: string) => Promise<void>;
  onRestoreFoodLog: (entryId: string) => Promise<void>;
  onUpdateFoodLog: (entryId: string, payload: FoodLogPatchInput) => Promise<void>;
}

interface FoodLogEditDraft {
  name: string;
  description: string;
  calories: string;
  ingredients: IngredientResult[];
}

export const Explorer: React.FC<ExplorerProps> = ({
  logEntries,
  onNavigateToSession,
  onDeleteFoodLog,
  onRestoreFoodLog,
  onUpdateFoodLog,
}) => {
  const orderedEntries = sortFoodLogEntries(logEntries);
  const [selectedEntry, setSelectedEntry] = useState<FoodLogEntry | null>(
    orderedEntries[0] ?? null,
  );
  const [isMobileDetailOpen, setIsMobileDetailOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [deletingEntryId, setDeletingEntryId] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [undoableDeletedEntry, setUndoableDeletedEntry] = useState<FoodLogEntry | null>(null);
  const [restoringEntryId, setRestoringEntryId] = useState<string | null>(null);
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [editDraft, setEditDraft] = useState<FoodLogEditDraft | null>(null);
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
        return orderedEntries[0];
      }

      return orderedEntries.find((entry) => entry.id === current.id) ?? orderedEntries[0];
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

  const handleEditFieldChange = (
    field: keyof Omit<FoodLogEditDraft, 'ingredients'>,
    value: string,
  ) => {
    setEditDraft((current) => (current ? { ...current, [field]: value } : current));
  };

  const handleIngredientChange = (
    ingredientIndex: number,
    field: keyof IngredientResult,
    value: string,
  ) => {
    setEditDraft((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        ingredients: current.ingredients.map((ingredient, currentIndex) => (
          currentIndex === ingredientIndex
            ? { ...ingredient, [field]: value }
            : ingredient
        )),
      };
    });
  };

  const handleAddIngredient = () => {
    setEditDraft((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        ingredients: [
          ...current.ingredients,
          { name: '', portion: '', energy: '' },
        ],
      };
    });
  };

  const handleRemoveIngredient = (ingredientIndex: number) => {
    setEditDraft((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        ingredients: current.ingredients.filter(
          (_ingredient, currentIndex) => currentIndex !== ingredientIndex,
        ),
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
                  <button
                    key={entry.id}
                    type="button"
                    onClick={() => handleSelectEntry(entry)}
                    className={`group flex w-full flex-col rounded-[28px] border p-5 text-left transition-all md:flex-row md:items-center ${
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

                    <div className="mt-4 flex items-center justify-between md:mt-0 md:gap-4">
                      <div className="flex flex-col items-start md:items-end">
                        <div className="flex items-baseline gap-1">
                          <span className="font-serif-brand text-2xl font-bold text-[#4A453E]">
                            {entry.calories}
                          </span>
                          <span className="text-[10px] font-bold uppercase text-[#4A453E]/30">
                            kcal
                          </span>
                        </div>
                      </div>

                      <div className="border-l border-[#4A453E]/05 pl-4">
                        <span className="flex size-10 items-center justify-center rounded-full text-[#4A453E]/20 transition-all group-hover:bg-[#FF8A65]/5 group-hover:text-[#FF8A65]">
                          <span className="material-symbols-outlined text-xl">chevron_right</span>
                        </span>
                      </div>
                    </div>
                  </button>
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
              onEditFieldChange={handleEditFieldChange}
              onIngredientChange={handleIngredientChange}
              onAddIngredient={handleAddIngredient}
              onRemoveIngredient={handleRemoveIngredient}
              onDelete={() => setIsDeleteDialogOpen(true)}
              onOpenChat={() => selectedEntry.sessionId && onNavigateToSession(selectedEntry.sessionId)}
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
                  onEditFieldChange={handleEditFieldChange}
                  onIngredientChange={handleIngredientChange}
                  onAddIngredient={handleAddIngredient}
                  onRemoveIngredient={handleRemoveIngredient}
                  onDelete={() => setIsDeleteDialogOpen(true)}
                  onOpenChat={() => selectedEntry.sessionId && onNavigateToSession(selectedEntry.sessionId)}
                />
              </div>
            </div>
          )}
        </>
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
  onEditFieldChange: (
    field: keyof Omit<FoodLogEditDraft, 'ingredients'>,
    value: string,
  ) => void;
  onIngredientChange: (
    ingredientIndex: number,
    field: keyof IngredientResult,
    value: string,
  ) => void;
  onAddIngredient: () => void;
  onRemoveIngredient: (ingredientIndex: number) => void;
  onDelete: () => void;
  onOpenChat: () => void;
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
  onEditFieldChange,
  onIngredientChange,
  onAddIngredient,
  onRemoveIngredient,
  onDelete,
  onOpenChat,
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
              Saved Entry
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

        {isEditing && editDraft ? (
          <input
            type="text"
            value={editDraft.name}
            onChange={(event) => onEditFieldChange('name', event.target.value)}
            autoFocus
            placeholder="Meal name"
            className="w-full rounded-[18px] border border-[#4A453E]/10 bg-[#F7F3E9]/40 px-4 py-3 font-serif-brand text-[26px] font-bold italic leading-[1.16] text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/30 focus:ring-2 focus:ring-[#FF8A65]/15 md:text-[32px]"
          />
        ) : (
          <h2 className="text-balance font-serif-brand text-[28px] font-bold italic leading-[1.14] text-[#4A453E] md:text-[34px]">
            {entry.name}
          </h2>
        )}
      </div>

      <div className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-5 py-5 md:px-6 md:py-6">
        <div className="space-y-5 md:space-y-6">
          <div className="rounded-[24px] border border-[#4A453E]/8 bg-[#FFFDF5] p-5 shadow-sm md:rounded-[28px] md:p-6">
            <div className="mb-5 flex flex-col gap-2 md:mb-6 md:flex-row md:items-center md:justify-between">
              <h5 className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[#4A453E]/40">
                <span className="material-symbols-outlined text-lg text-[#FF8A65]">
                  analytics
                </span>
                Nutrition Details
              </h5>
              <span className="font-serif-brand text-[26px] font-bold italic leading-none text-[#4A453E] md:text-[28px]">
                {totalCalories}{' '}
                <span className="font-sans text-xs font-bold not-italic uppercase tracking-wide text-[#4A453E]/20">
                  kcal
                </span>
              </span>
            </div>

            {isEditing && editDraft ? (
              <div className="mb-5 space-y-3 md:mb-6 md:space-y-4">
                {editDraft.ingredients.map((item, index) => (
                  <div
                    key={`edit-ingredient-${index}`}
                    className="group/edit-row relative rounded-[20px] border border-[#4A453E]/05 bg-white p-3.5 shadow-sm"
                  >
                    <button
                      type="button"
                      onClick={() => onRemoveIngredient(index)}
                      className="absolute -right-2 -top-2 flex size-7 items-center justify-center rounded-full bg-red-500 text-white opacity-100 shadow-sm transition-opacity sm:opacity-0 sm:group-hover/edit-row:opacity-100 focus:opacity-100"
                      aria-label={`Remove ingredient ${index + 1}`}
                    >
                      <span className="material-symbols-outlined text-sm">close</span>
                    </button>

                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      <input
                        type="text"
                        value={item.name}
                        placeholder="Ingredient"
                        onChange={(event) => onIngredientChange(index, 'name', event.target.value)}
                        className="rounded-[12px] border border-transparent bg-[#F7F3E9]/20 px-3 py-2 text-[13px] font-bold text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/30 focus:bg-white"
                      />
                      <input
                        type="text"
                        value={item.energy}
                        placeholder="Energy, e.g. 100 kcal"
                        onChange={(event) => onIngredientChange(index, 'energy', event.target.value)}
                        className="rounded-[12px] border border-transparent bg-[#F7F3E9]/20 px-3 py-2 text-[13px] font-bold text-[#4A453E]/80 outline-none transition-all focus:border-[#FF8A65]/30 focus:bg-white sm:text-right"
                      />
                    </div>

                    <input
                      type="text"
                      value={item.portion}
                      placeholder="Portion, e.g. 150g"
                      onChange={(event) => onIngredientChange(index, 'portion', event.target.value)}
                      className="mt-2 w-full rounded-[12px] border border-transparent bg-[#F7F3E9]/20 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.14em] text-[#4A453E]/45 outline-none transition-all focus:border-[#FF8A65]/30 focus:bg-white"
                    />
                  </div>
                ))}

                {editDraft.ingredients.length === 0 && (
                  <div className="rounded-[20px] border border-dashed border-[#4A453E]/10 bg-white/70 px-4 py-6 text-center text-sm text-[#4A453E]/45">
                    Add at least one ingredient before saving.
                  </div>
                )}

                <button
                  type="button"
                  onClick={onAddIngredient}
                  className="flex w-full items-center justify-center gap-2 rounded-[18px] border border-dashed border-[#4A453E]/10 py-3 text-[10px] font-bold uppercase tracking-[0.18em] text-[#4A453E]/35 transition-all hover:border-[#FF8A65]/30 hover:text-[#FF8A65]"
                >
                  <span className="material-symbols-outlined text-sm">add</span>
                  Add Ingredient
                </button>
              </div>
            ) : (
              <div className="mb-5 space-y-3 md:mb-6 md:space-y-4">
                {entry.breakdown.map((item, index) => (
                  <div key={`${item.name}-${index}`} className="group/row flex items-center justify-between gap-4 py-1">
                    <div className="min-w-0 flex flex-col">
                      <span className="text-[13px] font-bold text-[#4A453E] transition-colors group-hover/row:text-[#FF8A65] md:text-sm">
                        {item.name}
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#4A453E]/40">
                        {item.portion}
                      </span>
                    </div>
                    <span className="shrink-0 text-[11px] font-bold text-[#4A453E]/80 md:text-xs">{item.energy}</span>
                  </div>
                ))}
              </div>
            )}

            {hasMacroData(entry) ? (
              <>
                <div className="grid grid-cols-3 gap-2 border-t border-[#4A453E]/05 pt-5 md:gap-3 md:pt-6">
                  <MacroStat label="Protein" value={entry.protein ?? 'N/A'} accent />
                  <MacroStat label="Carbs" value={entry.carbs ?? 'N/A'} />
                  <MacroStat label="Fat" value={entry.fat ?? 'N/A'} />
                </div>
                {isEditing && (
                  <p className="mt-3 text-center text-[10px] leading-5 text-[#4A453E]/40">
                    Macro values stay read-only for now. This editor updates the title,
                    description, calories, and ingredient breakdown.
                  </p>
                )}
              </>
            ) : (
              <div className="rounded-[20px] border border-dashed border-[#4A453E]/10 bg-white/50 px-4 py-3 text-[13px] leading-6 text-[#4A453E]/55">
                Macro nutrients were not recorded for this saved entry. Food Log currently
                stores the calorie estimate and ingredient-level breakdown only.
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

            {isEditing && editDraft ? (
              <textarea
                value={editDraft.description}
                onChange={(event) => onEditFieldChange('description', event.target.value)}
                rows={4}
                placeholder="Meal description"
                className="custom-scrollbar w-full rounded-[16px] border border-[#4A453E]/10 bg-[#F7F3E9]/40 px-4 py-3 text-sm leading-7 text-[#4A453E]/70 outline-none transition-all focus:border-[#FF8A65]/30 focus:ring-2 focus:ring-[#FF8A65]/15"
              />
            ) : (
              <p className="text-sm leading-7 text-[#4A453E]/60">
                {entry.description}
              </p>
            )}
          </div>

          <div className="relative aspect-[4/3] overflow-hidden rounded-[24px] border border-[#4A453E]/05 shadow-sm md:aspect-video md:rounded-[28px]">
            <FoodLogImage
              src={entry.image}
              alt={entry.name}
              className="h-full w-full object-cover"
            />
          </div>
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

interface MacroStatProps {
  label: string;
  value: string;
  accent?: boolean;
}

const MacroStat: React.FC<MacroStatProps> = ({ label, value, accent = false }) => (
  <div className="text-center">
    <span className="mb-1 block text-[9px] font-bold uppercase tracking-[0.14em] text-[#4A453E]/30">
      {label}
    </span>
    <span className={`text-[17px] font-bold md:text-lg ${accent ? 'text-[#FF8A65]' : 'text-[#4A453E]'}`}>
      {value}
    </span>
  </div>
);

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
  };
}

function hasMacroData(entry: FoodLogEntry): boolean {
  return Boolean(entry.protein || entry.carbs || entry.fat);
}

function getDraftTotalCalories(draft: FoodLogEditDraft): string {
  const total = draft.ingredients.reduce(
    (sum, ingredient) => sum + extractCaloriesValue(ingredient.energy),
    0,
  );

  if (total > 0 || draft.ingredients.length > 0) {
    return Number.isInteger(total) ? String(total) : total.toFixed(1);
  }

  return draft.calories;
}

function extractCaloriesValue(value: string): number {
  const match = value.match(/(\d+(?:\.\d+)?)/);
  if (!match) {
    return 0;
  }

  const parsed = Number.parseFloat(match[1]);
  return Number.isFinite(parsed) ? parsed : 0;
}

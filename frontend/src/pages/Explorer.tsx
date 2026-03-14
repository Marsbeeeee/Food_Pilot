import React, { useEffect, useState } from 'react';

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
  const [deletingEntryId, setDeletingEntryId] = useState<string | null>(null);
  const [undoableDeletedEntry, setUndoableDeletedEntry] = useState<FoodLogEntry | null>(null);
  const [restoringEntryId, setRestoringEntryId] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [editDraft, setEditDraft] = useState<FoodLogEditDraft | null>(null);
  const collectionStats = buildCollectionStats(orderedEntries);
  const selectedEntrySavedMoment = selectedEntry
    ? formatSavedMoment(selectedEntry.savedAt)
    : null;

  useEffect(() => {
    if (orderedEntries.length === 0) {
      setSelectedEntry(null);
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

    const shouldDelete = window.confirm(
      'Remove this saved favorite from Food Log? It will disappear from your collection, but you can save it again from a new analysis later.',
    );
    if (!shouldDelete) {
      return;
    }

    setDeletingEntryId(selectedEntry.id);
    try {
      await onDeleteFoodLog(selectedEntry.id);
      setUndoableDeletedEntry(selectedEntry);
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : 'Unable to remove this saved favorite right now.';
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
        : 'Unable to restore this saved favorite right now.';
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
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    if (isSavingEdit) {
      return;
    }

    setIsEditModalOpen(false);
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

    setIsSavingEdit(true);
    try {
      await onUpdateFoodLog(selectedEntry.id, buildFoodLogPatchPayload(editDraft));
      setIsEditModalOpen(false);
      setEditDraft(null);
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : 'Unable to update this saved favorite right now.';
      window.alert(message);
    } finally {
      setIsSavingEdit(false);
    }
  };

  return (
    <div className="flex h-full flex-1 flex-col overflow-hidden bg-[#FFFDF5] lg:flex-row">
      <main className="custom-scrollbar flex min-w-0 flex-1 flex-col overflow-y-auto p-6 md:p-8 lg:p-12">
        <div className="mx-auto mb-10 w-full max-w-4xl">
          <div className="mb-8 flex flex-col gap-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#FF8A65]/70">
              Food Log
            </span>
            <h1 className="font-serif-brand text-4xl font-bold text-[#4A453E] md:text-5xl">
              Saved Favorites
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-[#4A453E]/60 md:text-base">
              Food Log is your saved collection of meal analyses. Think of it as a favorites shelf
              for analyses you want to keep and refine over time, not a full eating diary. The
              collection is organized around when each favorite was last saved or edited.
            </p>
          </div>

          <div className="mb-12 grid grid-cols-1 gap-4 md:grid-cols-3">
            <SummaryCard
              label="Saved Favorites"
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
                Saved Collection
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
                    onClick={() => setSelectedEntry(entry)}
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
        <aside className="flex h-full w-full flex-col border-t border-[#4A453E]/05 bg-white shadow-[-10px_0_30px_rgba(0,0,0,0.02)] lg:w-[440px] lg:shrink-0 lg:border-l lg:border-t-0">
          <div className="border-b border-[#4A453E]/05 p-6 md:p-8">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#FF8A65]">
                  Saved Favorite
                </span>
                <p className="mt-2 text-[11px] font-semibold text-[#4A453E]/35">
                  Last updated {selectedEntrySavedMoment?.date} / {selectedEntrySavedMoment?.time}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedEntry(null)}
                className="rounded-full p-1 text-[#4A453E]/20 transition-colors hover:bg-[#4A453E]/5 hover:text-[#4A453E]"
              >
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>
            <h2 className="mb-2 font-serif-brand text-3xl font-bold italic leading-tight text-[#4A453E]">
              {selectedEntry.name}
            </h2>
            <p className="text-sm leading-relaxed text-[#4A453E]/60">
              {selectedEntry.description}
            </p>
          </div>

          <div className="custom-scrollbar flex-1 space-y-8 overflow-y-auto p-6 md:p-8">
            <div className="relative aspect-video overflow-hidden rounded-[32px] border border-[#4A453E]/05 shadow-sm">
              <FoodLogImage
                src={selectedEntry.image}
                alt={selectedEntry.name}
                className="h-full w-full object-cover"
              />
            </div>

            <div className="rounded-[32px] border border-[#4A453E]/8 bg-[#FFFDF5] p-6 shadow-sm md:p-8">
              <div className="mb-8 flex items-center justify-between gap-4">
                <h5 className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.1em] text-[#4A453E]/40">
                  <span className="material-symbols-outlined text-lg text-[#FF8A65]">
                    analytics
                  </span>
                  Nutrition Breakdown
                </h5>
                <span className="font-serif-brand text-[28px] font-bold italic text-[#4A453E]">
                  {selectedEntry.calories}{' '}
                  <span className="font-sans text-sm font-bold not-italic text-[#4A453E]/20">
                    kcal
                  </span>
                </span>
              </div>

              <div className="mb-8 space-y-4">
                {selectedEntry.breakdown.map((item, index) => (
                  <div key={`${item.name}-${index}`} className="group/row flex items-center justify-between py-1">
                    <div className="flex flex-col">
                      <span className="text-sm font-bold text-[#4A453E] transition-colors group-hover/row:text-[#FF8A65]">
                        {item.name}
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#4A453E]/40">
                        {item.portion}
                      </span>
                    </div>
                    <span className="text-xs font-bold text-[#4A453E]/80">{item.energy}</span>
                  </div>
                ))}
              </div>

              {hasMacroData(selectedEntry) ? (
                <div className="grid grid-cols-3 gap-3 border-t border-[#4A453E]/05 pt-8">
                  <MacroStat label="Protein" value={selectedEntry.protein ?? 'N/A'} accent />
                  <MacroStat label="Carbs" value={selectedEntry.carbs ?? 'N/A'} />
                  <MacroStat label="Fat" value={selectedEntry.fat ?? 'N/A'} />
                </div>
              ) : (
                <div className="rounded-[24px] border border-dashed border-[#4A453E]/10 bg-white/50 px-5 py-4 text-sm text-[#4A453E]/55">
                  Macro nutrients were not recorded for this saved favorite. Food Log currently
                  stores the calorie estimate and ingredient-level breakdown only.
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-3 border-t border-[#4A453E]/05 bg-white p-6 md:p-8">
            <div className="rounded-[20px] border border-[#4A453E]/8 bg-[#FFFDF5] px-4 py-3 text-sm leading-6 text-[#4A453E]/55">
              Food Log treats saved analyses like favorites. Editing this card refines the saved
              version in place instead of creating a duplicate record.
            </div>
            <button
              type="button"
              onClick={handleOpenEditModal}
              className="flex h-12 w-full items-center justify-center gap-2 rounded-full border border-[#FF8A65]/15 bg-[#FF8A65] text-sm font-bold text-white shadow-lg shadow-[#FF8A65]/20 transition-all hover:bg-[#FF8A65]/90"
            >
              <span className="material-symbols-outlined text-lg">edit</span>
              Edit Saved Favorite
            </button>
            <button
              type="button"
              onClick={() => void handleDeleteSelectedEntry()}
              disabled={deletingEntryId === selectedEntry.id}
              className={`flex h-12 w-full items-center justify-center gap-2 rounded-full border text-sm font-bold transition-all ${
                deletingEntryId === selectedEntry.id
                  ? 'cursor-wait border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E]/45'
                  : 'border-red-200 bg-red-50 text-red-500 hover:bg-red-100'
              }`}
            >
              <span className="material-symbols-outlined text-lg">delete</span>
              {deletingEntryId === selectedEntry.id ? 'Removing...' : 'Remove Favorite'}
            </button>
            <button
              type="button"
              onClick={() => selectedEntry.sessionId && onNavigateToSession(selectedEntry.sessionId)}
              disabled={!selectedEntry.sessionId}
              className={`flex h-14 w-full items-center justify-center gap-2 rounded-full text-sm font-bold text-white shadow-lg transition-all ${
                selectedEntry.sessionId
                  ? 'bg-[#FF8A65] shadow-[#FF8A65]/20 hover:bg-[#FF8A65]/90'
                  : 'cursor-not-allowed bg-[#4A453E]/20 shadow-none'
              }`}
            >
              <span className="material-symbols-outlined text-lg">forum</span>
              {selectedEntry.sessionId ? 'Open Source Chat' : 'Source Chat Deleted'}
            </button>
          </div>
        </aside>
      )}

      {isEditModalOpen && editDraft && selectedEntry && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 px-6 py-8"
          onClick={handleCloseEditModal}
        >
          <div
            className="custom-scrollbar max-h-full w-full max-w-3xl overflow-y-auto rounded-[28px] border border-[#4A453E]/10 bg-[#FFFDF5] p-6 shadow-[0_28px_70px_rgba(74,69,62,0.18)] md:p-8"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-bold text-[#4A453E]">Edit Saved Favorite</h3>
                <p className="mt-1 text-sm text-[#4A453E]/55">
                  Update the saved card without creating a new Food Log entry.
                </p>
              </div>
              <button
                type="button"
                onClick={handleCloseEditModal}
                disabled={isSavingEdit}
                className="rounded-full p-1 text-[#4A453E]/20 transition-colors hover:bg-[#4A453E]/5 hover:text-[#4A453E]"
              >
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <label className="flex flex-col gap-2">
                <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/40">
                  Meal Name
                </span>
                <input
                  type="text"
                  value={editDraft.name}
                  onChange={(event) => handleEditFieldChange('name', event.target.value)}
                  autoFocus
                  className="rounded-[18px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm font-medium text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15"
                />
              </label>
              <label className="flex flex-col gap-2">
                <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/40">
                  Total Calories
                </span>
                <input
                  type="text"
                  value={editDraft.calories}
                  onChange={(event) => handleEditFieldChange('calories', event.target.value)}
                  placeholder="260 kcal"
                  className="rounded-[18px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm font-medium text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15"
                />
              </label>
            </div>

            <label className="mt-5 flex flex-col gap-2">
              <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/40">
                Description
              </span>
              <textarea
                value={editDraft.description}
                onChange={(event) => handleEditFieldChange('description', event.target.value)}
                rows={4}
                className="custom-scrollbar rounded-[18px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm leading-6 text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15"
              />
            </label>

            <div className="mt-6 rounded-[24px] border border-[#4A453E]/8 bg-white/70 p-5">
              <div className="mb-4 flex items-center justify-between gap-4">
                <div>
                  <h4 className="text-sm font-bold text-[#4A453E]">Ingredient Breakdown</h4>
                  <p className="mt-1 text-xs text-[#4A453E]/45">
                    Update each ingredient line or add your own corrected breakdown.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleAddIngredient}
                  className="inline-flex h-10 items-center gap-2 rounded-full border border-[#4A453E]/10 bg-[#FFFDF5] px-4 text-sm font-bold text-[#4A453E]/75 transition-colors hover:border-[#FF8A65]/20 hover:text-[#FF8A65]"
                >
                  <span className="material-symbols-outlined text-[18px]">add</span>
                  Add Ingredient
                </button>
              </div>

              <div className="space-y-4">
                {editDraft.ingredients.map((ingredient, index) => (
                  <div
                    key={`edit-ingredient-${index}`}
                    className="grid grid-cols-1 gap-3 rounded-[20px] border border-[#4A453E]/8 bg-[#FFFDF5] p-4 md:grid-cols-[1.3fr_1fr_1fr_auto]"
                  >
                    <input
                      type="text"
                      value={ingredient.name}
                      onChange={(event) => handleIngredientChange(index, 'name', event.target.value)}
                      placeholder="Ingredient"
                      className="rounded-[14px] border border-[#4A453E]/10 bg-white px-3 py-2.5 text-sm text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15"
                    />
                    <input
                      type="text"
                      value={ingredient.portion}
                      onChange={(event) => handleIngredientChange(index, 'portion', event.target.value)}
                      placeholder="Portion"
                      className="rounded-[14px] border border-[#4A453E]/10 bg-white px-3 py-2.5 text-sm text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15"
                    />
                    <input
                      type="text"
                      value={ingredient.energy}
                      onChange={(event) => handleIngredientChange(index, 'energy', event.target.value)}
                      placeholder="Energy"
                      className="rounded-[14px] border border-[#4A453E]/10 bg-white px-3 py-2.5 text-sm text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveIngredient(index)}
                      className="inline-flex h-11 items-center justify-center rounded-[14px] border border-red-200 bg-red-50 px-4 text-sm font-bold text-red-500 transition-colors hover:bg-red-100"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                {editDraft.ingredients.length === 0 && (
                  <div className="rounded-[20px] border border-dashed border-[#4A453E]/10 bg-[#FFFDF5] px-4 py-6 text-center text-sm text-[#4A453E]/45">
                    Add at least one ingredient before saving.
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={handleCloseEditModal}
                disabled={isSavingEdit}
                className="rounded-[14px] border border-[#4A453E]/10 bg-white px-4 py-2.5 text-sm font-semibold text-[#4A453E]/55 transition-colors hover:bg-[#F7F3E9] disabled:cursor-not-allowed disabled:opacity-70"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleSaveEdit()}
                disabled={isSavingEdit}
                className="rounded-[14px] bg-[#FF8A65] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#FF8A65]/20 transition-colors hover:bg-[#FF8A65]/90 disabled:cursor-wait disabled:opacity-80"
              >
                {isSavingEdit ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
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
    </div>
  );
};

interface SummaryCardProps {
  label: string;
  value: string;
  unit: string;
  accent?: boolean;
}

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
    <span className="mb-1 block text-[10px] font-bold uppercase text-[#4A453E]/30">{label}</span>
    <span className={`text-lg font-bold ${accent ? 'text-[#FF8A65]' : 'text-[#4A453E]'}`}>
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
            This saved favorite was stored without an image.
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

function buildFoodLogPatchPayload(draft: FoodLogEditDraft): FoodLogPatchInput {
  const ingredients = draft.ingredients.map((ingredient, index) => ({
    name: normalizeRequiredText(ingredient.name, `Ingredient ${index + 1} name`),
    portion: normalizeRequiredText(ingredient.portion, `Ingredient ${index + 1} portion`),
    energy: normalizeEnergyText(ingredient.energy, `Ingredient ${index + 1} energy`),
  }));

  if (ingredients.length === 0) {
    throw new Error('Add at least one ingredient before saving.');
  }

  return {
    resultTitle: normalizeRequiredText(draft.name, 'Meal name'),
    resultDescription: normalizeRequiredText(draft.description, 'Description'),
    totalCalories: normalizeEnergyText(draft.calories, 'Total calories'),
    ingredients,
  };
}

function normalizeRequiredText(value: string, fieldLabel: string): string {
  const normalized = value.trim().replace(/\s+/g, ' ');
  if (!normalized) {
    throw new Error(`${fieldLabel} cannot be empty.`);
  }
  return normalized;
}

function normalizeEnergyText(value: string, fieldLabel: string): string {
  const normalized = normalizeRequiredText(value, fieldLabel);
  return /\bkcal\b/i.test(normalized) ? normalized : `${normalized} kcal`;
}

function hasMacroData(entry: FoodLogEntry): boolean {
  return Boolean(entry.protein || entry.carbs || entry.fat);
}

function buildCollectionStats(logEntries: FoodLogEntry[]): {
  updatedThisWeek: number;
  chatLinked: number;
} {
  const now = new Date();
  const windowStart = new Date(now);
  windowStart.setHours(0, 0, 0, 0);
  windowStart.setDate(windowStart.getDate() - 6);

  let updatedThisWeek = 0;
  let chatLinked = 0;

  logEntries.forEach((entry) => {
    if (entry.sessionId) {
      chatLinked += 1;
    }

    const savedAt = parseSavedAt(entry.savedAt);
    if (savedAt && savedAt >= windowStart) {
      updatedThisWeek += 1;
    }
  });

  return {
    updatedThisWeek,
    chatLinked,
  };
}

function sortFoodLogEntries(logEntries: FoodLogEntry[]): FoodLogEntry[] {
  return [...logEntries].sort((left, right) => (
    resolveSortTimestamp(right).getTime() - resolveSortTimestamp(left).getTime()
  ));
}

function resolveSortTimestamp(entry: FoodLogEntry): Date {
  return parseSavedAt(entry.savedAt) ?? new Date(0);
}

function formatSavedMoment(value: string | undefined): { date: string; time: string } {
  const timestamp = parseSavedAt(value);
  if (!timestamp) {
    return {
      date: '--',
      time: '--:--',
    };
  }

  return {
    date: timestamp.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    time: timestamp.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  };
}

function parseSavedAt(value: string | undefined): Date | null {
  if (!value) {
    return null;
  }

  const normalized = value.replace(' ', 'T');
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

import React, { useEffect, useState } from 'react';

import { FoodLogEntry } from '../types/types';

interface ExplorerProps {
  logEntries: FoodLogEntry[];
  onNavigateToSession: (sessionId: string) => void;
  onDeleteFoodLog: (entryId: string) => Promise<void>;
}

export const Explorer: React.FC<ExplorerProps> = ({
  logEntries,
  onNavigateToSession,
  onDeleteFoodLog,
}) => {
  const [selectedEntry, setSelectedEntry] = useState<FoodLogEntry | null>(
    logEntries.length > 0 ? logEntries[0] : null,
  );
  const [deletingEntryId, setDeletingEntryId] = useState<string | null>(null);
  const collectionStats = buildCollectionStats(logEntries);

  useEffect(() => {
    if (logEntries.length === 0) {
      setSelectedEntry(null);
      return;
    }

    setSelectedEntry((current) => {
      if (!current) {
        return logEntries[0];
      }

      return logEntries.find((entry) => entry.id === current.id) ?? logEntries[0];
    });
  }, [logEntries]);

  const handleDeleteSelectedEntry = async () => {
    if (!selectedEntry || deletingEntryId) {
      return;
    }

    const shouldDelete = window.confirm(
      'Remove this saved analysis from Food Log? It will disappear from the default list, but you can save it again from a new analysis later.',
    );
    if (!shouldDelete) {
      return;
    }

    setDeletingEntryId(selectedEntry.id);
    try {
      await onDeleteFoodLog(selectedEntry.id);
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : 'Unable to remove this saved analysis from Food Log right now.';
      window.alert(message);
    } finally {
      setDeletingEntryId((current) => (current === selectedEntry.id ? null : current));
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
              My Food Log
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-[#4A453E]/60 md:text-base">
              Food Log is your saved collection of meal analyses. It only includes items you
              explicitly save, not your complete eating history. It also does not support direct
              edits. To change a saved item, run a new analysis and save it again. Timestamps on
              this page refer to save time or last re-save time, not when you ate the meal.
            </p>
          </div>

          <div className="mb-12 grid grid-cols-1 gap-4 md:grid-cols-3">
            <SummaryCard
              label="Saved Analyses"
              value={String(logEntries.length)}
              unit="items"
              accent
            />
            <SummaryCard
              label="Saved This Week"
              value={String(collectionStats.savedThisWeek)}
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
              {logEntries.length > 0 && (
                <span className="text-[11px] font-semibold text-[#4A453E]/35">
                  Sorted by last save time, newest first
                </span>
              )}
            </div>

            {logEntries.length > 0 ? (
              logEntries.map((entry) => {
                const isActive = selectedEntry?.id === entry.id;

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
                        Saved {entry.date} / {entry.time}
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
                <p className="text-base font-bold text-[#4A453E]/45">No saved analyses yet.</p>
                <p className="mt-2 text-sm text-[#4A453E]/35">
                  Food Log only contains meal analyses you explicitly save. Unsaved chat and estimate
                  results will not appear here.
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
                  Saved Analysis
                </span>
                <p className="mt-2 text-[11px] font-semibold text-[#4A453E]/35">
                  Last saved {selectedEntry.date} / {selectedEntry.time}
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
                  Macro nutrients were not recorded for this saved analysis. Food Log currently stores
                  the calorie estimate and ingredient-level breakdown only.
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-3 border-t border-[#4A453E]/05 bg-white p-6 md:p-8">
            <div className="rounded-[20px] border border-[#4A453E]/8 bg-[#FFFDF5] px-4 py-3 text-sm leading-6 text-[#4A453E]/55">
              Food Log does not provide a standalone edit flow. If you want to change this saved
              analysis, reopen the chat or run a new analysis, then save again to overwrite it.
            </div>
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
              {deletingEntryId === selectedEntry.id ? 'Removing...' : 'Remove from Food Log'}
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
              {selectedEntry.sessionId ? 'Open Related Chat' : 'Related Chat Deleted'}
            </button>
          </div>
        </aside>
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
            This saved analysis was stored without an image.
          </p>
        </>
      )}
    </div>
  </div>
);

function hasMacroData(entry: FoodLogEntry): boolean {
  return Boolean(entry.protein || entry.carbs || entry.fat);
}

function buildCollectionStats(logEntries: FoodLogEntry[]): {
  savedThisWeek: number;
  chatLinked: number;
} {
  const now = new Date();
  const windowStart = new Date(now);
  windowStart.setHours(0, 0, 0, 0);
  windowStart.setDate(windowStart.getDate() - 6);

  let savedThisWeek = 0;
  let chatLinked = 0;

  logEntries.forEach((entry) => {
    if (entry.sessionId) {
      chatLinked += 1;
    }

    const savedAt = parseSavedAt(entry.savedAt);
    if (savedAt && savedAt >= windowStart) {
      savedThisWeek += 1;
    }
  });

  return {
    savedThisWeek,
    chatLinked,
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

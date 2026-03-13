import React, { useEffect, useMemo, useState } from 'react';

import { FoodLogEntry } from '../types/types';

interface ExplorerProps {
  logEntries: FoodLogEntry[];
  onNavigateToSession: (sessionId: string) => void;
}

export const Explorer: React.FC<ExplorerProps> = ({ logEntries, onNavigateToSession }) => {
  const [selectedEntry, setSelectedEntry] = useState<FoodLogEntry | null>(
    logEntries.length > 0 ? logEntries[0] : null,
  );

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

  const totalCalories = useMemo(
    () => logEntries.reduce((sum, entry) => sum + parseCalories(entry.calories), 0),
    [logEntries],
  );

  const averageCalories = useMemo(
    () => (logEntries.length > 0 ? Math.round(totalCalories / logEntries.length) : 0),
    [logEntries.length, totalCalories],
  );

  return (
    <div className="flex h-full flex-1 flex-col overflow-hidden bg-[#FFFDF5] lg:flex-row">
      <main className="custom-scrollbar flex min-w-0 flex-1 flex-col overflow-y-auto p-6 md:p-8 lg:p-12">
        <div className="mx-auto mb-10 w-full max-w-4xl">
          <div className="mb-8 flex flex-col gap-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#FF8A65]/70">
              Food Log
            </span>
            <h1 className="font-serif-brand text-4xl font-bold text-[#4A453E] md:text-5xl">
              我的饮食日志
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-[#4A453E]/60 md:text-base">
              回看近期的热量估算与食材拆分，快速找到每次分析记录，并跳转回对应对话。
            </p>
          </div>

          <div className="mb-12 grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-6">
            <SummaryCard
              label="累计热量"
              value={String(totalCalories)}
              unit="kcal"
            />
            <SummaryCard
              label="每餐平均"
              value={String(averageCalories)}
              unit="kcal"
            />
            <SummaryCard
              label="记录总数"
              value={String(logEntries.length)}
              unit="条"
              accent
            />
          </div>

          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                最近记录
              </h2>
              {logEntries.length > 0 && (
                <span className="text-[11px] font-semibold text-[#4A453E]/35">
                  最近一次记录已自动置顶
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
                      <img
                        src={entry.image}
                        alt={entry.name}
                        className="h-full w-full object-cover grayscale-[20%] transition-all group-hover:grayscale-0"
                      />
                    </div>

                    <div className="min-w-0 flex-1 md:px-6">
                      <span className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-[#4A453E]/30">
                        {entry.date} · {entry.time}
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
                <p className="text-base font-bold text-[#4A453E]/45">还没有饮食日志记录</p>
                <p className="mt-2 text-sm text-[#4A453E]/35">
                  去 Workshop 发起一次食物分析，结果会自动出现在这里。
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
                  分析详情
                </span>
                <p className="mt-2 text-[11px] font-semibold text-[#4A453E]/35">
                  {selectedEntry.date} · {selectedEntry.time}
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
              <img
                src={selectedEntry.image}
                className="h-full w-full object-cover"
                alt={selectedEntry.name}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent"></div>
              <div className="absolute bottom-4 left-6">
                <span className="rounded-full border border-white/10 bg-white/20 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-white backdrop-blur-md">
                  AI 视觉匹配
                </span>
              </div>
            </div>

            <div className="rounded-[32px] border border-[#4A453E]/8 bg-[#FFFDF5] p-6 shadow-sm md:p-8">
              <div className="mb-8 flex items-center justify-between gap-4">
                <h5 className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.1em] text-[#4A453E]/40">
                  <span className="material-symbols-outlined text-lg text-[#FF8A65]">
                    analytics
                  </span>
                  营养拆分
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

              <div className="grid grid-cols-3 gap-3 border-t border-[#4A453E]/05 pt-8">
                <MacroStat label="蛋白质" value={selectedEntry.protein} accent />
                <MacroStat label="碳水" value={selectedEntry.carbs} />
                <MacroStat label="脂肪" value={selectedEntry.fat} />
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3 border-t border-[#4A453E]/05 bg-white p-6 md:p-8">
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
              前往对应对话
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

function parseCalories(value: string): number {
  const match = value.replace(/,/g, '').match(/\d+(\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

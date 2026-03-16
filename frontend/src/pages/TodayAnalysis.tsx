import React from 'react';

import type { FoodLogEntry } from '../types/types';

interface TodayAnalysisProps {
  foodLog: FoodLogEntry[];
}

export const TodayAnalysis: React.FC<TodayAnalysisProps> = ({ foodLog }) => {
  const today = new Date().toISOString().slice(0, 10);

  const todayItems = foodLog.filter(
    (entry) => entry.status === 'active' && entry.mealOccurredAt.startsWith(today),
  );

  const totalCalories = todayItems.reduce((sum, entry) => {
    const numeric = parseFloat(entry.calories || '0');
    return sum + (Number.isFinite(numeric) ? numeric : 0);
  }, 0);

  return (
    <div className="flex h-full flex-col bg-[#FDFBF7]">
      <header className="flex items-center justify-between border-b border-[#F0EDE6] bg-white px-8 py-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#FF8A65]">
            Today&apos;s Analysis
          </p>
          <h1 className="mt-2 text-2xl font-serif font-medium text-[#2D2D2A]">
            {today} 的摄入概览
          </h1>
        </div>
        <div className="rounded-full bg-[#FFF3E9] px-4 py-2 text-sm font-bold text-[#FF8A65]">
          {todayItems.length} items · {totalCalories} kcal
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-8 py-6 space-y-4 custom-scrollbar">
        {todayItems.length === 0 ? (
          <div className="mt-24 text-center text-sm text-[#8E8E84]">
            今日还没有被加入分析的菜品。请在 Food Log 中保存或选择想要分析的结果。
          </div>
        ) : (
          todayItems.map((entry) => (
            <div
              key={entry.id}
              className="flex items-center justify-between rounded-2xl border border-[#F0EDE6] bg-white px-4 py-3"
            >
              <div>
                <div className="text-sm font-medium text-[#4A453E]">{entry.name}</div>
                <div className="text-xs text-[#8E8E84]">{entry.description}</div>
              </div>
              <div className="text-right">
                <div className="text-lg font-serif font-medium text-[#4A453E]">
                  {entry.calories}
                </div>
                <div className="text-[10px] font-bold uppercase tracking-widest text-[#A5A59E]">
                  kcal
                </div>
              </div>
            </div>
          ))
        )}
      </main>
    </div>
  );
}



import React, { useState, useEffect } from 'react';
import { FoodLogEntry } from '../types/types';

interface ExplorerProps {
  logEntries: FoodLogEntry[];
  onNavigateToSession: (sessionId: string) => void;
}

export const Explorer: React.FC<ExplorerProps> = ({ logEntries, onNavigateToSession }) => {
    const [selectedEntry, setSelectedEntry] = useState<FoodLogEntry | null>(logEntries.length > 0 ? logEntries[0] : null);

  useEffect(() => {
    if (logEntries.length > 0) {
      setSelectedEntry(logEntries[0]);
    } else {
      setSelectedEntry(null);
    }
  }, [logEntries]);

  return (
    <div className="flex flex-1 overflow-hidden h-full">
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto custom-scrollbar bg-[#FFFDF5] p-8 lg:p-12">
        <div className="max-w-4xl w-full mx-auto mb-10">
          <div className="flex flex-col gap-1 mb-8">
            <h1 className="text-4xl font-serif-brand font-bold text-[#4A453E]">我的饮食日志</h1>
            <p className="text-[#4A453E]/60 text-base">回顾你近期的热量预估和营养洞察。</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="bg-white/60 border border-[#4A453E]/05 rounded-[24px] p-6 shadow-sm">
              <span className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest block mb-2">今日总计</span>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-serif-brand font-bold text-[#4A453E]">{logEntries.length > 0 ? '790' : '0'}</span>
                <span className="text-xs font-bold text-[#4A453E]/30 uppercase">kcal</span>
              </div>
            </div>
            <div className="bg-white/60 border border-[#4A453E]/05 rounded-[24px] p-6 shadow-sm">
              <span className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest block mb-2">每餐平均</span>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-serif-brand font-bold text-[#4A453E]">{logEntries.length > 0 ? '470' : '0'}</span>
                <span className="text-xs font-bold text-[#4A453E]/30 uppercase">kcal</span>
              </div>
            </div>
            <div className="bg-[#FF8A65]/5 border border-[#FF8A65]/10 rounded-[24px] p-6 shadow-sm">
              <span className="text-[10px] font-bold text-[#FF8A65]/60 uppercase tracking-widest block mb-2">记录项</span>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-serif-brand font-bold text-[#FF8A65]">{logEntries.length}</span>
                <span className="text-xs font-bold text-[#FF8A65]/40 uppercase">本周</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <h2 className="text-xs font-bold text-[#4A453E]/30 uppercase tracking-[0.2em] px-2 mb-2">最近记录</h2>
            {logEntries.length > 0 ? (
              logEntries.map((entry) => (
                <div 
                  key={entry.id}
                  onClick={() => setSelectedEntry(entry)}
                  className={`group flex items-center p-5 rounded-[28px] cursor-pointer transition-all border ${
                    selectedEntry?.id === entry.id 
                      ? 'bg-white border-[#4A453E]/10 shadow-md translate-x-1' 
                      : 'bg-white/40 border-transparent hover:bg-white hover:border-[#4A453E]/05 hover:shadow-sm'
                  }`}
                >
                  <div className="size-14 rounded-[20px] overflow-hidden shrink-0 border border-[#4A453E]/05">
                    <img src={entry.image} alt={entry.name} className="w-full h-full object-cover grayscale-[20%] group-hover:grayscale-0 transition-all" />
                  </div>
                  <div className="flex-1 min-w-0 px-6">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold text-[#4A453E]/30 uppercase tracking-wider">{entry.date} • {entry.time}</span>
                    </div>
                    <h4 className="text-lg font-bold text-[#4A453E] truncate">{entry.name}</h4>
                    <p className="text-xs text-[#4A453E]/50 truncate">{entry.description}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1 px-4">
                    <div className="flex items-baseline gap-0.5">
                      <span className="text-2xl font-serif-brand font-bold text-[#4A453E]">{entry.calories}</span>
                      <span className="text-[10px] font-bold text-[#4A453E]/30 uppercase">kcal</span>
                    </div>
                  </div>
                  <div className="pl-4 border-l border-[#4A453E]/05">
                    <button className="size-10 rounded-full flex items-center justify-center text-[#4A453E]/20 group-hover:text-[#FF8A65] group-hover:bg-[#FF8A65]/5 transition-all">
                      <span className="material-symbols-outlined text-xl">chevron_right</span>
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-20 bg-white/40 border border-dashed border-[#4A453E]/10 rounded-[32px]">
                <span className="material-symbols-outlined text-4xl text-[#4A453E]/20 mb-4">history_toggle_off</span>
                <p className="text-[#4A453E]/40 font-bold">未发现饮食记录。快去 "咨询 FoodPilot" 记录你的第一餐吧！</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {selectedEntry && (
        <aside className="w-[440px] bg-white border-l border-[#4A453E]/05 flex flex-col h-full shadow-[-10px_0_30px_rgba(0,0,0,0.02)]">
          <div className="p-8 border-b border-[#4A453E]/05">
            <div className="flex justify-between items-start mb-6">
              <span className="text-[10px] font-bold text-[#FF8A65] uppercase tracking-[0.15em]">分析详情</span>
              <button onClick={() => setSelectedEntry(null)} className="text-[#4A453E]/20 hover:text-[#4A453E] transition-colors">
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>
            <h2 className="text-3xl font-serif-brand font-bold text-[#4A453E] leading-tight mb-2 italic">{selectedEntry.name}</h2>
            <p className="text-sm text-[#4A453E]/60 leading-relaxed">{selectedEntry.description}</p>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
            <div className="relative rounded-[32px] overflow-hidden aspect-video border border-[#4A453E]/05 shadow-sm">
              <img src={selectedEntry.image} className="w-full h-full object-cover" alt="Food analysis" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent"></div>
              <div className="absolute bottom-4 left-6">
                <span className="px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-[10px] font-bold text-white uppercase tracking-widest border border-white/10">AI 视觉匹配</span>
              </div>
            </div>
            <div className="bg-[#FFFDF5] rounded-[32px] border border-[#4A453E]/08 p-8 shadow-sm">
              <div className="flex items-center justify-between mb-8">
                <h5 className="text-[11px] font-bold text-[#4A453E]/40 uppercase tracking-[0.1em] flex items-center gap-2">
                  <span className="material-symbols-outlined text-lg text-[#FF8A65]">analytics</span> 营养细分
                </h5>
                <span className="text-[28px] font-serif-brand font-bold text-[#4A453E] italic">
                  {selectedEntry.calories} <span className="text-sm font-sans not-italic font-bold text-[#4A453E]/20">kcal</span>
                </span>
              </div>
              <div className="space-y-4 mb-8">
                {selectedEntry.breakdown.map((item, i) => (
                  <div key={i} className="flex justify-between items-center py-1 group/row">
                    <div className="flex flex-col">
                      <span className="text-sm font-bold text-[#4A453E] group-hover/row:text-[#FF8A65] transition-colors">{item.name}</span>
                      <span className="text-[10px] text-[#4A453E]/40 uppercase font-bold tracking-wider">{item.portion}</span>
                    </div>
                    <span className="text-xs font-bold text-[#4A453E]/80">{item.energy}</span>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-3 border-t border-[#4A453E]/05 pt-8">
                <div className="text-center"><span className="text-[10px] font-bold text-[#4A453E]/30 uppercase block mb-1">蛋白质</span><span className="text-lg font-bold text-[#FF8A65]">{selectedEntry.protein}</span></div>
                <div className="text-center"><span className="text-[10px] font-bold text-[#4A453E]/30 uppercase block mb-1">碳水</span><span className="text-lg font-bold text-[#4A453E]">{selectedEntry.carbs}</span></div>
                <div className="text-center"><span className="text-[10px] font-bold text-[#4A453E]/30 uppercase block mb-1">脂肪</span><span className="text-lg font-bold text-[#4A453E]">{selectedEntry.fat}</span></div>
              </div>
            </div>
          </div>
          <div className="p-8 bg-white border-t border-[#4A453E]/05 flex flex-col gap-3">
            <button 
              onClick={() => selectedEntry.sessionId && onNavigateToSession(selectedEntry.sessionId)}
              disabled={!selectedEntry.sessionId}
              className={`w-full h-14 rounded-full text-white font-bold text-sm shadow-lg transition-all flex items-center justify-center gap-2 ${
                selectedEntry.sessionId 
                ? 'bg-[#FF8A65] shadow-[#FF8A65]/20 hover:bg-[#FF8A65]/90' 
                : 'bg-[#4A453E]/20 cursor-not-allowed shadow-none'
              }`}
            >              
            <span className="material-symbols-outlined text-lg">forum</span> 前往对应对话
            </button>
          </div>
        </aside>
      )}
    </div>
  );
};

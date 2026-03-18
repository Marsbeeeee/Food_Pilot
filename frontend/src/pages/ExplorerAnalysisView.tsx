import React, { useEffect, useState } from 'react';

import { FoodLogEntry } from '../types/types';

interface AnalysisViewProps {
  items: {
    id: string;
    name: string;
    calories: string;
    protein?: string | null;
    carbs?: string | null;
    fat?: string | null;
    analysisDate: string;
  }[];
  onBack: () => void;
  onRemove: (basketId: string) => void;
  onAnalyzeSelection?: (entries: FoodLogEntry[], date: string) => Promise<string>;
}

export const AnalysisView: React.FC<AnalysisViewProps> = ({
  items,
  onBack,
  onRemove,
  onAnalyzeSelection,
}) => {
  const [currentDate, setCurrentDate] = useState(getLocalDateKey());
  const [aiAdvice, setAiAdvice] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const filteredItems = items.filter((item) => item.analysisDate === currentDate);

  const totalCalories = filteredItems.reduce(
    (sum, item) => sum + extractCaloriesValue(item.calories),
    0,
  );

  const totalProtein = filteredItems.reduce(
    (sum, item) => sum + extractNutritionValue(item.protein),
    0,
  );

  const totalCarbs = filteredItems.reduce(
    (sum, item) => sum + extractNutritionValue(item.carbs),
    0,
  );

  const totalFat = filteredItems.reduce(
    (sum, item) => sum + extractNutritionValue(item.fat),
    0,
  );

  const handleAnalyze = async () => {
    if (filteredItems.length === 0 || isAnalyzing) {
      return;
    }

    setIsAnalyzing(true);
    try {
      if (onAnalyzeSelection) {
        const result = await onAnalyzeSelection(filteredItems, currentDate);
        setAiAdvice(result);
      } else {
        setAiAdvice(
          buildFallbackAnalysis({
            totalCalories,
            protein: totalProtein,
            carbs: totalCarbs,
            fat: totalFat,
            itemNames: filteredItems.map((item) => item.name),
          }),
        );
      }
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : '暂时无法生成分析，请稍后重试。';
      setAiAdvice(message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    setAiAdvice(null);
  }, [currentDate]);

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden bg-[#FFFDF5]">
      {/* Header */}
      <header className="flex shrink-0 items-center justify-between border-b border-[#4A453E]/05 bg-white px-6 py-4 md:px-8 md:py-5">
        <div className="flex items-center gap-3 md:gap-4">
          <button
            type="button"
            onClick={onBack}
            className="flex size-9 items-center justify-center rounded-full text-[#4A453E]/50 transition-colors hover:bg-[#F7F3E9] hover:text-[#4A453E]"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>

          <h1 className="font-serif-brand text-2xl font-bold text-[#4A453E] md:text-3xl">
            每日营养分析
          </h1>
        </div>

        <div className="hidden rounded-full bg-[#FFF2EC] px-3 py-1.5 text-xs font-bold text-[#FF8A65] md:flex md:items-center md:gap-2">
          <span className="material-symbols-outlined text-[18px]">restaurant</span>
          已选 {filteredItems.length} 项
        </div>
      </header>

      {/* Body */}
      <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto px-6 py-6 md:px-8 md:py-8 lg:flex-row lg:gap-8">
        <section className="mx-auto flex w-full max-w-4xl flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-[28px] border border-[#4A453E]/08 bg-white p-6 shadow-sm">
              <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                  总热量
                </p>
                <input
                  type="date"
                  value={currentDate}
                  onChange={(event) => setCurrentDate(event.target.value)}
                  className="rounded-full border border-[#FF8A65]/20 bg-[#FFF7F2] px-3 py-1.5 text-[11px] font-bold text-[#FF8A65] outline-none transition-all focus:border-[#FF8A65]/40"
                />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="font-serif-brand text-5xl font-bold text-[#4A453E]">
                  {totalCalories || 0}
                </span>
                <span className="text-sm font-bold uppercase tracking-[0.2em] text-[#4A453E]/25">
                  kcal
                </span>
              </div>
            </div>
            {/* 右侧卡片占位，后续可放宏量营养等 */}
            <div className="rounded-[28px] border border-dashed border-[#4A453E]/10 bg-white/60 p-6 text-sm text-[#4A453E]/55">
              Select more saved entries from Food Log to enrich today&apos;s analysis. This panel can
              later show macro breakdowns or other insights.
            </div>
          </div>
          {/* 其余分析内容可按需继续扩展 */}
        </section>
      </div>
    </div>
  );
}

function getLocalDateKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
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

function buildFallbackAnalysis(input: {
  totalCalories: number;
  protein: number;
  carbs: number;
  fat: number;
  itemNames: string[];
}): string {
  const { totalCalories, protein, carbs, fat, itemNames } = input;
  const macroTotal = protein + carbs + fat;
  const proteinRatio = macroTotal > 0 ? (protein / macroTotal) * 100 : 0;
  const fatRatio = macroTotal > 0 ? (fat / macroTotal) * 100 : 0;

  let balanceComment = '三大营养素比例较为均衡。';
  if (proteinRatio >= 35) {
    balanceComment = '蛋白质占比较高，适合增肌或高蛋白需求。';
  } else if (fatRatio >= 35) {
    balanceComment = '脂肪占比偏高，建议关注油脂摄入。';
  } else if (carbs > protein && carbs > fat) {
    balanceComment = '碳水化合物为主要供能来源，注意搭配优质蛋白。';
  }

  return [
    `今日分析包含：${itemNames.join('、')}。`,
    '',
    `估算总摄入：${Math.round(totalCalories)} kcal`,
    `蛋白质：${Math.round(protein)} g　碳水：${Math.round(carbs)} g　脂肪：${Math.round(fat)} g`,
    '',
    balanceComment,
    '',
    '改善建议：',
    '1. 如果这是正餐，确保蛋白质摄入充足（建议每餐 20-30g）。',
    '2. 如果整天摄入偏高，下一餐可减少酱料或高油脂配料。',
    '3. 如果膳食纤维不足，建议当天补充蔬菜或水果。',
  ].join('\n');
}



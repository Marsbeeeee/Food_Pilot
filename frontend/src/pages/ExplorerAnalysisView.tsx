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
        : 'Unable to generate today analysis right now.';
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
            Nutrition Analysis
          </h1>
        </div>

        <div className="hidden rounded-full bg-[#FFF2EC] px-3 py-1.5 text-xs font-bold text-[#FF8A65] md:flex md:items-center md:gap-2">
          <span className="material-symbols-outlined text-[18px]">restaurant</span>
          {filteredItems.length} items selected
        </div>
      </header>

      {/* Body */}
      <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto px-6 py-6 md:px-8 md:py-8 lg:flex-row lg:gap-8">
        <section className="mx-auto flex w-full max-w-4xl flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-[28px] border border-[#4A453E]/08 bg-white p-6 shadow-sm">
              <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                  Total Energy
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
  return Number.isFinite(parsed) ? parsed : 0;
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

  let balanceComment = 'The macro balance is relatively neutral.';
  if (proteinRatio >= 35) {
    balanceComment = 'Protein is relatively strong in this selection.';
  } else if (fatRatio >= 35) {
    balanceComment = 'Fat is relatively prominent in this selection.';
  } else if (carbs > protein && carbs > fat) {
    balanceComment = 'Carbohydrates are the main contributor in this selection.';
  }

  return [
    `Today’s analysis covers: ${itemNames.join(', ')}.`,
    '',
    `Total estimated intake: ${totalCalories.toFixed(1)} kcal.`,
    `Protein: ${protein.toFixed(1)} g, Carbs: ${carbs.toFixed(1)} g, Fat: ${fat.toFixed(1)} g.`,
    '',
    balanceComment,
    '',
    'General suggestion:',
    '1. Keep protein adequate if this is meant to be a main meal window.',
    '2. If the overall day feels heavy, reduce dense sauces or oil-heavy components in the next meal.',
    '3. Add vegetables or fruit later in the day if fiber looks light.',
  ].join('\n');
}



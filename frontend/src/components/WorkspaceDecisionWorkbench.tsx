import React from 'react';

import {
  buildDecisionWorkspaceSummary,
  getDecisionRoleLabel,
} from '../app/workspaceDecisionUiState.js';
import {
  DecisionCardProductComponent,
  WorkspaceClarificationPresentation,
  WorkspaceMealEstimatePresentation,
} from '../types/types';

type RenderedEstimateBlock = {
  title: string;
  confidence?: string;
  description?: string;
  items: Array<{
    name: string;
    portion: string;
    energy: string;
    protein?: string;
    carbs?: string;
    fat?: string;
  }>;
  total: string;
};

type SavePresentationState = {
  state: 'saved' | 'saving' | 'failed' | 'not_saved';
  badgeIcon: string;
  badgeLabel: string;
  saveActionIcon: string;
  saveActionLabel: string;
  helperText: string;
};

interface DecisionWorkbenchActionProps {
  savePresentation: SavePresentationState;
  canSaveFromWorkspace: boolean;
  isSavedToFoodLog: boolean;
  isDeletingSavedFoodLog: boolean;
  isAddingToAnalysis: boolean;
  analysisActionLabel: string;
  analysisActionDisabled: boolean;
  onSave: () => void;
  onUndoSave: () => void;
  onAddToAnalysis: () => void;
  onRerun: () => void;
  onEditQuery: () => void;
  onContinueCompare: () => void;
}

interface WorkspaceEstimateWorkbenchProps extends DecisionWorkbenchActionProps {
  presentation: WorkspaceMealEstimatePresentation;
  renderedEstimates: RenderedEstimateBlock[] | null;
  mealDescription: string | null;
  messageTime: string;
}

interface WorkspaceClarificationWorkbenchProps extends DecisionWorkbenchActionProps {
  presentation: WorkspaceClarificationPresentation;
  messageTime: string;
}

export const WorkspaceEstimateWorkbench: React.FC<WorkspaceEstimateWorkbenchProps> = ({
  presentation,
  renderedEstimates,
  mealDescription,
  messageTime,
  savePresentation,
  canSaveFromWorkspace,
  isSavedToFoodLog,
  isDeletingSavedFoodLog,
  isAddingToAnalysis,
  analysisActionLabel,
  analysisActionDisabled,
  onSave,
  onUndoSave,
  onAddToAnalysis,
  onRerun,
  onEditQuery,
  onContinueCompare,
}) => {
  const decisionCard = presentation.decisionCard;
  const summary = buildDecisionWorkspaceSummary(decisionCard, {
    isSaved: isSavedToFoodLog,
    canSaveFromWorkspace,
    hasMealDescription: Boolean(mealDescription),
  });
  const normalizedProduct = decisionCard?.normalizedProduct ?? null;
  const comboItems = Array.isArray(normalizedProduct?.comboItems)
    ? normalizedProduct.comboItems
    : [];
  const shouldShowGroupedBlocks = Boolean(renderedEstimates?.length && renderedEstimates.length > 1);
  const nutritionItems = presentation.items ?? [];

  return (
    <div className={`w-full overflow-hidden rounded-[28px] border shadow-[0_18px_48px_rgba(74,69,62,0.08)] ${
      summary.tone === 'low_confidence'
        ? 'border-[#F5C16C]/35 bg-white'
        : 'border-[#4A453E]/6 bg-white'
    }`}>
      <div className="border-b border-[#4A453E]/6 bg-white px-5 py-5 md:px-7 md:py-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="min-w-0 flex-1 md:flex md:min-h-[112px] md:flex-col md:justify-center">
            <h3 className="text-balance font-serif-brand text-[24px] font-bold leading-[1.16] text-[#4A453E] md:text-[28px]">
              {presentation.title || normalizedProduct?.productName || '本次决策结果'}
            </h3>
            <p className="mt-2.5 max-w-3xl text-[13px] leading-6 text-[#4A453E]/70 md:text-[14px]">
              {decisionCard?.adaptationNote || presentation.description || '当前结果已整理为可直接扫读的决策卡片。'}
            </p>
          </div>
          <div className="w-fit max-w-full shrink-0 self-start rounded-[20px] border border-[#E8DCCB] bg-[#FFFDF7] px-4 py-3 shadow-sm md:self-center md:text-right">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/35">
              热量
            </p>
            <p className="mt-1.5 whitespace-nowrap font-serif-brand text-[24px] font-bold leading-none text-[#FF8A65] md:text-[26px]">
              {formatEnergyInteger(presentation.total)}
            </p>
          </div>
        </div>
      </div>

      <div className="border-b border-[#4A453E]/6 px-5 py-4 md:px-7 md:py-5">
        <TagPanel
          title="分类标签"
          icon="sell"
          tags={buildPrimaryTags(normalizedProduct)}
          emptyText="当前结果还没有足够的标签信息。"
        />
      </div>

      {summary.tone === 'low_confidence' && (
        <div className="border-b border-[#F5C16C]/20 bg-[#FFF6E4] px-5 py-5 md:px-8">
          <SectionHeading icon="warning" title="低置信提醒" />
          <p className="mt-3 text-[14px] leading-7 text-[#7E5B1C]">
            当前结果已经能形成初步判断，但仍带有较高不确定性。建议优先参考风险和补充说明，再决定是否直接保存或继续点单。
          </p>
          {presentation.confidenceReasons.length > 0 && (
            <ul className="mt-4 space-y-2">
              {presentation.confidenceReasons.map((reason) => (
                <li key={reason} className="rounded-[16px] border border-[#F5C16C]/20 bg-white/80 px-4 py-3 text-[13px] leading-6 text-[#4A453E]/75">
                  {reason}
                </li>
              ))}
            </ul>
          )}
          {presentation.missingConfigurationLabels.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {presentation.missingConfigurationLabels.map((label) => (
                <Pill key={label} label={`待确认：${label}`} tone="warn" />
              ))}
            </div>
          )}
        </div>
      )}

      <div className="space-y-6 bg-white px-5 py-6 md:px-8 md:py-8">
        {shouldShowGroupedBlocks && renderedEstimates ? (
          <div className="space-y-4">
            <SectionHeading icon="local_dining" title="套餐结构" />
            <div className="grid gap-4 lg:grid-cols-2">
              {renderedEstimates.map((block) => (
                <GroupedEstimateCard
                  key={`${block.title}-${block.total}`}
                  block={block}
                />
              ))}
            </div>
          </div>
        ) : comboItems.length > 0 ? (
          <div className="space-y-4">
            <SectionHeading icon="local_dining" title="组成项关系" />
            <div className="grid gap-3 md:grid-cols-2">
              {comboItems.map((item, index) => (
                <ComboItemCard key={`${index}-${item.productName}`} item={item} />
              ))}
            </div>
          </div>
        ) : null}

        {presentation.estimationMeta && (
          <MetaDetailSection presentation={presentation} />
        )}

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
          <div className="space-y-4">
            <SectionHeading icon="table_rows" title={shouldShowGroupedBlocks ? '整体营养明细' : '营养明细'} />
            <NutritionTable items={nutritionItems} total={presentation.total} mobileCardTone="neutral" />
          </div>
          <DecisionGuidancePanel presentation={presentation} />
        </div>

        <DecisionWorkbenchActions
          savePresentation={savePresentation}
          canSaveFromWorkspace={canSaveFromWorkspace}
          isSavedToFoodLog={isSavedToFoodLog}
          isDeletingSavedFoodLog={isDeletingSavedFoodLog}
          isAddingToAnalysis={isAddingToAnalysis}
          analysisActionLabel={analysisActionLabel}
          analysisActionDisabled={analysisActionDisabled}
          onSave={onSave}
          onUndoSave={onUndoSave}
          onAddToAnalysis={onAddToAnalysis}
          onRerun={onRerun}
          onEditQuery={onEditQuery}
          onContinueCompare={onContinueCompare}
        />
      </div>

      <div className="border-t border-[#4A453E]/6 bg-white px-5 py-3 text-right text-[10px] font-bold uppercase tracking-[0.18em] text-[#4A453E]/25 md:px-8">
        {messageTime || '刚刚'}
      </div>
    </div>
  );
};

export const WorkspaceClarificationWorkbench: React.FC<WorkspaceClarificationWorkbenchProps> = ({
  presentation,
  messageTime,
  savePresentation,
  canSaveFromWorkspace,
  isSavedToFoodLog,
  isDeletingSavedFoodLog,
  isAddingToAnalysis,
  analysisActionLabel,
  analysisActionDisabled,
  onSave,
  onUndoSave,
  onAddToAnalysis,
  onRerun,
  onEditQuery,
  onContinueCompare,
}) => {
  const decisionCard = presentation.decisionCard;
  const summary = buildDecisionWorkspaceSummary(decisionCard, {
    isSaved: isSavedToFoodLog,
    canSaveFromWorkspace,
    hasMealDescription: true,
  });
  const normalizedProduct = decisionCard?.normalizedProduct ?? null;
  const comboItems = Array.isArray(normalizedProduct?.comboItems)
    ? normalizedProduct.comboItems
    : [];

  return (
      <div className="w-full overflow-hidden rounded-[28px] border border-[#F5C16C]/35 bg-white shadow-[0_18px_48px_rgba(74,69,62,0.08)]">
      <div className="bg-white px-5 py-5 md:px-7 md:py-6">
        <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#B5791A]">
          {summary.eyebrow}
        </p>
        <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="text-balance font-serif-brand text-[24px] font-bold leading-[1.16] text-[#4A453E] md:text-[28px]">
              {presentation.title || '商品信息待补充'}
            </h3>
            <p className="mt-2.5 max-w-3xl text-[13px] leading-6 text-[#4A453E]/72 md:text-[14px]">
              {presentation.description || presentation.content || summary.description}
            </p>
            {presentation.inputSummary && (
              <div className="mt-4 rounded-[20px] border border-[#F5C16C]/20 bg-[#FFF8EE] px-4 py-4 shadow-sm">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#8C6517]/60">
                  当前输入
                </p>
                <p className="mt-2 text-[14px] leading-7 text-[#4A453E]/78">
                  {presentation.inputSummary}
                </p>
              </div>
            )}
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:w-[360px] lg:grid-cols-1">
            <HighlightBadge
              icon="warning"
              label="当前状态"
              value={summary.title}
              tone="warn"
            />
            <HighlightBadge
              icon="verified"
              label="置信状态"
              value={summary.confidenceLabel}
              tone="warn"
            />
            {presentation.matchLevelLabel && (
              <HighlightBadge
                icon="target"
                label="识别层级"
                value={presentation.matchLevelLabel}
                tone="neutral"
              />
            )}
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {summary.specBadges.map((badge) => (
            <Pill key={badge} label={badge} tone="warn" />
          ))}
          {presentation.summaryBadges.map((badge) => (
            <Pill key={badge} label={badge} tone="neutral" />
          ))}
        </div>
      </div>

      <div className="border-b border-[#F5C16C]/20 px-5 py-4 md:px-7 md:py-5">
        <TagPanel
          title="分类标签"
          icon="sell"
          tags={buildPrimaryTags(normalizedProduct)}
          emptyText="当前还没有足够的标签信息。"
          tone="warn"
        />
      </div>

      <div className="space-y-6 bg-white px-5 py-6 md:px-8 md:py-8">
        {presentation.content && presentation.content !== presentation.description && (
          <MessageBlock icon="forum" title="需要你补充的内容" content={presentation.content} tone="warn" />
        )}

        {presentation.missingFields.length > 0 && (
          <div className="space-y-3">
            <SectionHeading icon="error" title={presentation.missingFieldLabel} tone="warn" />
            <div className="flex flex-wrap gap-2">
              {presentation.missingFields.map((field) => (
                <Pill key={field} label={field} tone="warn" />
              ))}
            </div>
          </div>
        )}

        {(comboItems.length > 0 || presentation.comboItems.length > 0) && (
          <div className="space-y-4">
            <SectionHeading icon="local_dining" title={presentation.comboLabel} tone="warn" />
            <div className="grid gap-3 md:grid-cols-2">
              {comboItems.length > 0
                ? comboItems.map((item, index) => (
                  <ComboItemCard key={`${index}-${item.productName}`} item={item} tone="warn" />
                ))
                : presentation.comboItems.map((item) => (
                  <div key={item} className="rounded-[20px] border border-[#F5C16C]/20 bg-white/75 px-4 py-4">
                    <p className="text-[13px] font-semibold text-[#4A453E]/78">{item}</p>
                  </div>
                ))}
            </div>
          </div>
        )}

        {presentation.riskTags.length > 0 && (
          <div className="space-y-3">
            <SectionHeading icon="warning" title={presentation.riskLabel} tone="warn" />
            <div className="flex flex-wrap gap-2">
              {presentation.riskTags.map((tag) => (
                <Pill key={tag} label={tag} tone="warn" />
              ))}
            </div>
          </div>
        )}

        {presentation.adjustments.length > 0 && (
          <div className="space-y-3">
            <SectionHeading icon="tips_and_updates" title={presentation.actionLabel} tone="warn" />
            <div className="space-y-2">
              {presentation.adjustments.map((item) => (
                <div key={item} className="rounded-[18px] border border-[#F5C16C]/16 bg-white/78 px-4 py-3 text-[14px] leading-7 text-[#4A453E]/75">
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}

        <DecisionWorkbenchActions
          savePresentation={savePresentation}
          canSaveFromWorkspace={canSaveFromWorkspace}
          isSavedToFoodLog={isSavedToFoodLog}
          isDeletingSavedFoodLog={isDeletingSavedFoodLog}
          isAddingToAnalysis={isAddingToAnalysis}
          analysisActionLabel={analysisActionLabel}
          analysisActionDisabled={analysisActionDisabled}
          onSave={onSave}
          onUndoSave={onUndoSave}
          onAddToAnalysis={onAddToAnalysis}
          onRerun={onRerun}
          onEditQuery={onEditQuery}
          onContinueCompare={onContinueCompare}
          tone="warn"
        />
      </div>

      <div className="border-t border-[#F5C16C]/20 bg-[#FFF6E4] px-5 py-3 text-right text-[10px] font-bold uppercase tracking-[0.18em] text-[#8C6517]/45 md:px-8">
        {messageTime || '刚刚'}
      </div>
    </div>
  );
};

const DecisionWorkbenchActions: React.FC<DecisionWorkbenchActionProps & { tone?: 'warn' | 'neutral' }> = ({
  savePresentation,
  canSaveFromWorkspace,
  isSavedToFoodLog,
  isDeletingSavedFoodLog,
  isAddingToAnalysis,
  analysisActionLabel,
  analysisActionDisabled,
  onSave,
  onUndoSave,
  onAddToAnalysis,
  onRerun,
  onEditQuery,
  onContinueCompare,
  tone = 'neutral',
}) => (
  <div className={`rounded-[28px] border px-4 py-4 md:px-5 md:py-5 ${
    tone === 'warn' ? 'border-[#F5C16C]/20 bg-[#FFF8EE]' : 'border-[#4A453E]/8 bg-[#FFFDF7]'
  }`}>
    <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
      {isSavedToFoodLog ? (
        <button
          type="button"
          onClick={onUndoSave}
          disabled={isDeletingSavedFoodLog}
          className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-full border px-5 text-sm font-bold transition-all ${
            isDeletingSavedFoodLog
              ? 'cursor-wait border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E]/45'
              : 'border-red-200 bg-red-50 text-red-500 hover:bg-red-100'
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">bookmark_remove</span>
          {isDeletingSavedFoodLog ? '撤销中...' : '撤销保存'}
        </button>
      ) : (
        <button
          type="button"
          onClick={onSave}
          disabled={!canSaveFromWorkspace || savePresentation.state === 'saving'}
          className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-full border px-5 text-sm font-bold transition-all ${
            !canSaveFromWorkspace || savePresentation.state === 'saving'
              ? 'cursor-not-allowed border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E]/45'
              : savePresentation.state === 'failed'
                ? 'border-red-200 bg-red-50 text-red-500 hover:bg-red-100'
                : 'border-[#FF8A65]/20 bg-[#FF8A65] text-white shadow-lg shadow-[#FF8A65]/18 hover:bg-[#FF8A65]/90'
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">{savePresentation.saveActionIcon}</span>
          {savePresentation.saveActionLabel}
        </button>
      )}

      <button
        type="button"
        onClick={onAddToAnalysis}
        disabled={analysisActionDisabled || isAddingToAnalysis}
        className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-full border px-5 text-sm font-bold transition-all ${
          analysisActionDisabled || isAddingToAnalysis
            ? 'cursor-not-allowed border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E]/45'
            : 'border-[#81C784]/28 bg-[#EEF8EE] text-[#3F8752] hover:border-[#81C784]/40 hover:bg-[#E5F5E7]'
        }`}
      >
        <span className="material-symbols-outlined text-[18px]">
          {isAddingToAnalysis ? 'hourglass_top' : 'analytics'}
        </span>
        {isAddingToAnalysis ? '加入中...' : analysisActionLabel}
      </button>

      <button
        type="button"
        onClick={onRerun}
        className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-[#4A453E]/10 bg-[#FFFDF7] px-5 text-sm font-bold text-[#4A453E]/72 transition-all hover:bg-[#F7F3E9]"
      >
        <span className="material-symbols-outlined text-[18px]">refresh</span>
        重新分析
      </button>
    </div>

    <div className="mt-4 flex flex-wrap gap-2">
      <SecondaryActionButton icon="edit" label="修改后重跑" onClick={onEditQuery} />
      <SecondaryActionButton icon="compare_arrows" label="继续比较" onClick={onContinueCompare} />
    </div>
  </div>
);

const DecisionGuidancePanel: React.FC<{
  presentation: WorkspaceMealEstimatePresentation;
}> = ({ presentation }) => {
  const blocks = [
    presentation.riskLabels.length > 0 ? {
      title: '风险标签',
      icon: 'warning',
      content: (
        <div className="flex flex-wrap gap-2">
          {presentation.riskLabels.map((label) => (
            <Pill key={label} label={label} tone="warn" />
          ))}
        </div>
      ),
    } : null,
    presentation.adjustments.length > 0 ? {
      title: '调整建议',
      icon: 'tune',
      content: (
        <div className="space-y-2">
          {presentation.adjustments.map((item) => (
            <div key={item} className="rounded-[16px] border border-[#E8DCCB] bg-[#FFFDF7] px-4 py-3 text-[14px] leading-7 text-[#4A453E]/74">
              {item}
            </div>
          ))}
        </div>
      ),
    } : null,
    presentation.alternatives.length > 0 ? {
      title: '替代建议',
      icon: 'swap_horiz',
      content: (
        <div className="space-y-2">
          {presentation.alternatives.map((item) => (
            <div key={item} className="rounded-[16px] border border-[#E8DCCB] bg-[#FFFDF7] px-4 py-3 text-[14px] leading-7 text-[#4A453E]/74">
              {item}
            </div>
          ))}
        </div>
      ),
    } : null,
  ].filter(Boolean) as Array<{ title: string; icon: string; content: React.ReactNode }>;

  if (blocks.length === 0) {
    return (
      <div className="rounded-[24px] border border-[#4A453E]/8 bg-[#FFFDF7] p-5 shadow-sm">
        <SectionHeading icon="psychology" title="决策建议" />
        <p className="mt-3 text-[14px] leading-7 text-[#4A453E]/70">
          当前结果还没有返回更多结构化建议，可以直接参考上方热量和分类标签继续判断。
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-[24px] border border-[#E8DCCB] bg-[#FFFDF7] p-5 shadow-sm">
      <SectionHeading icon="psychology" title="决策建议" />
      <div className="mt-4 space-y-4">
        {blocks.map((block) => (
          <div key={block.title}>
            <SectionHeading icon={block.icon} title={block.title} compact />
            <div className="mt-3">{block.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const MetaDetailSection: React.FC<{
  presentation: WorkspaceMealEstimatePresentation;
}> = ({ presentation }) => {
  const hasMeta = Boolean(
    presentation.templateHitLabel
    || presentation.templateSourceLabel
    || presentation.templateVersionLabel
    || presentation.configVersionLabel
    || presentation.fallbackPathLabels.length
    || presentation.confidenceReasons.length
    || presentation.appliedRules.length
    || presentation.missingConfigurationLabels.length,
  );

  if (!hasMeta) {
    return null;
  }

  return (
    <div className="rounded-[24px] border border-[#4A453E]/8 bg-[#FFFDF7] p-5 shadow-sm">
      <SectionHeading icon="dataset" title="估算依据" />
      <div className="mt-4 flex flex-wrap gap-2">
        {presentation.templateHitLabel && <Pill label={presentation.templateHitLabel} tone="accent" />}
        {presentation.templateSourceLabel && <Pill label={`来源：${presentation.templateSourceLabel}`} tone="neutral" />}
        {presentation.templateVersionLabel && <Pill label={presentation.templateVersionLabel} tone="neutral" />}
        {presentation.configVersionLabel && <Pill label={presentation.configVersionLabel} tone="neutral" />}
        {presentation.fallbackPathLabels.length > 0 && <Pill label={`路径：${presentation.fallbackPathLabels.join(' → ')}`} tone="neutral" />}
      </div>
      {presentation.confidenceReasons.length > 0 && (
        <div className="mt-4 space-y-2">
          {presentation.confidenceReasons.map((reason) => (
            <div key={reason} className="rounded-[16px] border border-[#4A453E]/6 bg-[#FFFDF9] px-4 py-3 text-[13px] leading-6 text-[#4A453E]/72">
              {reason}
            </div>
          ))}
        </div>
      )}
      {presentation.appliedRules.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {presentation.appliedRules.map((rule) => (
            <Pill key={rule} label={rule} tone="neutral" />
          ))}
        </div>
      )}
      {presentation.missingConfigurationLabels.length > 0 && (
        <div className="mt-4">
          <SectionHeading icon="rule" title="缺失配置" compact />
          <div className="mt-3 flex flex-wrap gap-2">
            {presentation.missingConfigurationLabels.map((label) => (
              <Pill key={label} label={label} tone="warn" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const NutritionTable: React.FC<{
  items: WorkspaceMealEstimatePresentation['items'];
  total?: string | null;
  mobileCardTone: 'neutral' | 'warn';
}> = ({ items, total, mobileCardTone }) => {
  const totalProtein = items.reduce((sum, item) => sum + extractMacroNum(item.protein), 0);
  const totalCarbs = items.reduce((sum, item) => sum + extractMacroNum(item.carbs), 0);
  const totalFat = items.reduce((sum, item) => sum + extractMacroNum(item.fat), 0);

  return (
    <div className="overflow-hidden rounded-[24px] border border-[#4A453E]/8 bg-[#FFFDF7] shadow-sm">
      <div className="grid gap-3 border-b border-[#4A453E]/6 bg-[#FFFDF7] px-4 py-4 sm:grid-cols-2 xl:grid-cols-4">
        <MacroSummaryCard label="总热量" value={formatEnergyInteger(total)} tone="accent" />
        <MacroSummaryCard label="蛋白质" value={formatMacroValue(totalProtein)} />
        <MacroSummaryCard label="碳水" value={formatMacroValue(totalCarbs)} />
        <MacroSummaryCard label="脂肪" value={formatMacroValue(totalFat)} />
      </div>

      <div className="md:hidden">
        <div className="divide-y divide-[#4A453E]/6">
          {items.map((item, index) => (
            <div key={`${item.name}-${index}`} className={`px-4 py-4 ${mobileCardTone === 'warn' ? 'bg-[#FFFDF9]' : 'bg-[#FFFDF7]'}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[14px] font-bold text-[#4A453E]">{item.name}</p>
                  <p className="mt-1 text-[12px] text-[#4A453E]/45">{item.portion}</p>
                </div>
                <p className="text-[13px] font-bold text-[#4A453E]">{formatEnergyInteger(item.energy)}</p>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Pill label={`蛋白 ${item.protein || '—'}`} tone="neutral" />
                <Pill label={`碳水 ${item.carbs || '—'}`} tone="neutral" />
                <Pill label={`脂肪 ${item.fat || '—'}`} tone="neutral" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[680px] text-left">
          <thead className="bg-[#FBF6EC] text-[10px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/35">
            <tr>
              <th className="px-5 py-4">食材</th>
              <th className="px-4 py-4">份量</th>
              <th className="px-4 py-4 text-right">热量</th>
              <th className="px-4 py-4 text-right">蛋白质</th>
              <th className="px-4 py-4 text-right">碳水</th>
              <th className="px-5 py-4 text-right">脂肪</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#4A453E]/6 text-[14px]">
            {items.map((item, index) => (
              <tr key={`${item.name}-${index}`}>
                <td className="px-5 py-4 font-semibold text-[#4A453E]">{item.name}</td>
                <td className="px-4 py-4 text-[#4A453E]/58">{item.portion}</td>
                <td className="px-4 py-4 text-right font-semibold text-[#4A453E]">{formatEnergyInteger(item.energy)}</td>
                <td className="px-4 py-4 text-right text-[#4A453E]/68">{item.protein || '—'}</td>
                <td className="px-4 py-4 text-right text-[#4A453E]/68">{item.carbs || '—'}</td>
                <td className="px-5 py-4 text-right text-[#4A453E]/68">{item.fat || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const GroupedEstimateCard: React.FC<{
  block: RenderedEstimateBlock;
}> = ({ block }) => (
  <div className="rounded-[24px] border border-[#4A453E]/8 bg-[#FFFDF7] p-5 shadow-sm">
    <div className="flex items-start justify-between gap-3">
      <div>
        <h4 className="text-[18px] font-bold text-[#4A453E]">{block.title}</h4>
        {block.description && (
          <p className="mt-2 text-[13px] leading-6 text-[#4A453E]/65">{block.description}</p>
        )}
      </div>
      <div className="shrink-0 text-right">
        {block.confidence && (
          <Pill label={block.confidence} tone="neutral" />
        )}
        <p className="mt-2 font-serif-brand text-[24px] font-bold text-[#FF8A65]">
          {formatEnergyInteger(block.total)}
        </p>
      </div>
    </div>

    <div className="mt-4 space-y-2">
      {block.items.map((item, index) => (
        <div key={`${item.name}-${index}`} className="rounded-[18px] border border-[#4A453E]/6 bg-[#FFFDF7] px-4 py-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[14px] font-semibold text-[#4A453E]">{item.name}</p>
              <p className="mt-1 text-[12px] text-[#4A453E]/45">{item.portion}</p>
            </div>
            <p className="text-[13px] font-bold text-[#4A453E]">{formatEnergyInteger(item.energy)}</p>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const ComboItemCard: React.FC<{
  item: DecisionCardProductComponent;
  tone?: 'warn' | 'neutral';
}> = ({ item, tone = 'neutral' }) => (
  <div className={`rounded-[20px] border px-4 py-4 ${
    tone === 'warn'
      ? 'border-[#F5C16C]/20 bg-[#FFF8EE]'
      : 'border-[#4A453E]/8 bg-[#FFFDF7]'
  }`}>
    <div className="flex items-start justify-between gap-3">
      <div>
        <p className="text-[14px] font-semibold text-[#4A453E]">{item.productName}</p>
        <p className="mt-1 text-[12px] text-[#4A453E]/48">
          {[item.brandName, item.categoryName].filter(Boolean).join(' / ') || '组成项'}
        </p>
      </div>
      <Pill label={getDecisionRoleLabel(item.itemRole)} tone={tone === 'warn' ? 'warn' : 'neutral'} />
    </div>
    {item.quantity && (
      <p className="mt-3 text-[12px] font-semibold text-[#4A453E]/56">份量：{item.quantity}</p>
    )}
  </div>
);

const TagPanel: React.FC<{
  title: string;
  icon: string;
  tags: string[];
  emptyText: string;
  tone?: 'warn' | 'neutral';
}> = ({ title, icon, tags, emptyText, tone = 'neutral' }) => (
  <div className={`rounded-[22px] border px-4 py-4 shadow-sm ${
    tone === 'warn'
      ? 'border-[#F5C16C]/20 bg-[#FFF8EE]'
      : 'border-[#E8DCCB] bg-[#FFFDF7]'
  }`}>
    <SectionHeading icon={icon} title={title} tone={tone} />
    {tags.length > 0 ? (
      <div className="mt-3 flex flex-wrap gap-2.5">
        {tags.map((tag) => (
          <span
            key={tag}
            className={`inline-flex items-center rounded-full px-3.5 py-1.5 text-[12px] font-semibold ${
              tone === 'warn'
                ? 'border border-[#F5C16C]/28 bg-[#FFF1D9] text-[#8C6517]'
                : 'border border-[#FF8A65]/18 bg-[#FFF1EB] text-[#C95B3A]'
            }`}
          >
            {tag}
          </span>
        ))}
      </div>
    ) : (
      <p className="mt-3 text-[14px] leading-7 text-[#4A453E]/58">{emptyText}</p>
    )}
  </div>
);

const InfoPanel: React.FC<{
  title: string;
  icon: string;
  items: Array<{ label: string; value: string }>;
  emptyText: string;
}> = ({ title, icon, items, emptyText }) => (
  <div className="rounded-[24px] border border-[#4A453E]/8 bg-[#FFFDF7] p-5 shadow-sm">
    <SectionHeading icon={icon} title={title} />
    {items.length > 0 ? (
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div key={`${item.label}-${item.value}`} className="rounded-[18px] border border-[#4A453E]/6 bg-[#FFFDF7] px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/35">{item.label}</p>
            <p className="mt-2 text-[14px] font-semibold text-[#4A453E]">{item.value}</p>
          </div>
        ))}
      </div>
    ) : (
      <p className="mt-3 text-[14px] leading-7 text-[#4A453E]/58">{emptyText}</p>
    )}
  </div>
);

const MetaCard: React.FC<{
  icon: string;
  title: string;
  detail: string;
  tone?: 'warn' | 'neutral';
}> = ({ icon, title, detail, tone = 'neutral' }) => (
  <div className={`rounded-[24px] border px-4 py-4 shadow-sm ${
    tone === 'warn'
      ? 'border-[#F5C16C]/20 bg-[#FBF4E5]'
      : 'border-[#E8DCCB] bg-[#FFFDF7]'
  }`}>
    <SectionHeading icon={icon} title={title} compact />
    <p className="mt-3 text-[13px] leading-6 text-[#4A453E]/64">{detail}</p>
  </div>
);

const MessageBlock: React.FC<{
  icon: string;
  title: string;
  content: string;
  tone?: 'warn' | 'neutral';
}> = ({ icon, title, content, tone = 'neutral' }) => (
  <div className={`rounded-[24px] border px-5 py-5 shadow-sm ${
    tone === 'warn'
      ? 'border-[#F5C16C]/20 bg-[#FFF8EE]'
      : 'border-[#4A453E]/8 bg-[#FFFDF7]'
  }`}>
    <SectionHeading icon={icon} title={title} />
    <p className="mt-3 text-[14px] leading-7 text-[#4A453E]/74">{content}</p>
  </div>
);

const HighlightBadge: React.FC<{
  icon: string;
  label: string;
  value: string;
  tone: 'success' | 'warn' | 'neutral';
}> = ({ icon, label, value, tone }) => (
  <div className={`rounded-[22px] border px-4 py-4 shadow-sm ${
    tone === 'success'
      ? 'border-[#81C784]/22 bg-[#EEF8EE]'
      : tone === 'warn'
        ? 'border-[#F5C16C]/24 bg-[#FFF3D8]'
        : 'border-[#E8DCCB] bg-[#FFFDF7]'
  }`}>
    <div className="flex items-center gap-2">
      <span className={`material-symbols-outlined text-[18px] ${
        tone === 'success' ? 'text-[#4E9E63]' : tone === 'warn' ? 'text-[#B5791A]' : 'text-[#FF8A65]'
      }`}>
        {icon}
      </span>
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/38">{label}</p>
    </div>
    <p className="mt-3 text-[15px] font-semibold leading-6 text-[#4A453E]">{value}</p>
  </div>
);

const MacroSummaryCard: React.FC<{
  label: string;
  value: string;
  tone?: 'accent' | 'neutral';
}> = ({ label, value, tone = 'neutral' }) => (
  <div className={`rounded-[18px] px-4 py-3 ${
    tone === 'accent' ? 'bg-[#FFF1EB]' : 'bg-[#FFFDF7]'
  }`}>
    <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/35">{label}</p>
    <p className={`mt-2 text-[16px] font-semibold ${
      tone === 'accent' ? 'text-[#C95B3A]' : 'text-[#4A453E]'
    }`}>
      {value}
    </p>
  </div>
);

const SecondaryActionButton: React.FC<{
  icon: string;
  label: string;
  onClick: () => void;
}> = ({ icon, label, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className="inline-flex min-h-10 items-center gap-2 rounded-full border border-[#4A453E]/10 bg-[#FFFDF7] px-4 text-[12px] font-semibold text-[#4A453E]/68 transition-all hover:bg-[#F7F3E9]"
  >
    <span className="material-symbols-outlined text-[16px]">{icon}</span>
    {label}
  </button>
);

const SectionHeading: React.FC<{
  icon: string;
  title: string;
  compact?: boolean;
  tone?: 'warn' | 'neutral';
}> = ({ icon, title, compact = false, tone = 'neutral' }) => (
  <div className="flex items-center gap-2">
    <span className={`material-symbols-outlined ${compact ? 'text-[18px]' : 'text-[20px]'} ${
      tone === 'warn' ? 'text-[#B5791A]' : 'text-[#FF8A65]'
    }`}>
      {icon}
    </span>
    <p className={`font-bold uppercase tracking-[0.16em] ${
      compact ? 'text-[10px] text-[#4A453E]/35' : 'text-[11px] text-[#4A453E]/40'
    }`}>
      {title}
    </p>
  </div>
);

const Pill: React.FC<{
  label: string;
  tone: 'warn' | 'neutral' | 'accent';
}> = ({ label, tone }) => (
  <span className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold ${
    tone === 'warn'
      ? 'border-[#F5C16C]/28 bg-[#FFF3D8] text-[#8C6517]'
      : tone === 'accent'
        ? 'border-[#FF8A65]/20 bg-[#FFF1EB] text-[#C95B3A]'
        : 'border-[#4A453E]/10 bg-[#FFFDF7] text-[#4A453E]/68'
  }`}>
    {label}
  </span>
);

function extractMacroNum(value?: string | null): number {
  if (!value) return 0;
  const match = String(value).match(/(\d+(?:\.\d+)?)/);
  if (!match) return 0;
  const parsed = Number.parseFloat(match[1]);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatMacroValue(value: number): string {
  if (value <= 0) {
    return '—';
  }
  return `${Number.isInteger(value) ? String(value) : value.toFixed(1)} g`;
}

function formatEnergyInteger(energy?: string | null): string {
  const num = extractMacroNum(energy);
  if (!num) {
    return energy || '未知';
  }
  return `${Math.round(num)} kcal`;
}

function buildPrimaryTags(
  normalizedProduct?: WorkspaceMealEstimatePresentation['normalizedProduct'] | WorkspaceClarificationPresentation['normalizedProduct'] | null,
): string[] {
  if (!normalizedProduct) {
    return [];
  }

  const tags = [
    normalizeCategoryTag(normalizedProduct.categoryName),
    normalizedProduct.brandName || null,
  ].filter(Boolean) as string[];

  return [...new Set(tags)];
}

function normalizeCategoryTag(categoryName?: string | null): string | null {
  if (!categoryName) {
    return null;
  }

  const normalized = categoryName.trim();
  if (!normalized) {
    return null;
  }

  if (
    normalized.includes('茶')
    || normalized.includes('咖啡')
    || normalized.includes('饮')
    || normalized.includes('奶')
    || normalized.includes('果汁')
    || normalized.includes('汽水')
  ) {
    return '饮料';
  }

  return normalized;
}


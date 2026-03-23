import React, { useEffect, useMemo, useRef, useState } from 'react';

export type FoodLogSort = 'created_desc' | 'created_asc' | 'calories_desc' | 'calories_asc' | 'updated_desc';
export type FoodLogCaloriesPreset = 'any' | 'under_200' | '200_500' | '500_800' | '800_plus';

type ToolbarPanel = 'sort' | 'filter' | null;
type FilterType = 'date' | 'calories';

interface FoodLogSearchToolbarProps {
  searchQuery: string;
  onSearchQueryChange: (value: string) => void;
  sort: FoodLogSort;
  onSortChange: (value: FoodLogSort) => void;
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  caloriePreset: FoodLogCaloriesPreset;
  customMinCalories: string;
  customMaxCalories: string;
  onCaloriePresetChange: (value: FoodLogCaloriesPreset) => void;
  onCustomMinCaloriesChange: (value: string) => void;
  onCustomMaxCaloriesChange: (value: string) => void;
  hasActiveFilters: boolean;
  onClearFilters: () => void;
}

interface FilterDraft {
  dateFrom: string;
  dateTo: string;
  preset: FoodLogCaloriesPreset;
  minCalories: string;
  maxCalories: string;
}

const SORT_OPTIONS: Array<{ value: FoodLogSort; label: string }> = [
  { value: 'created_desc', label: 'Latest save first' },
  { value: 'created_asc', label: 'Oldest first' },
  { value: 'calories_desc', label: 'Calories high -> low' },
  { value: 'calories_asc', label: 'Calories low -> high' },
];

const CALORIE_OPTIONS: Array<{ value: FoodLogCaloriesPreset; label: string }> = [
  { value: 'any', label: 'Any calories' },
  { value: 'under_200', label: 'Under 200 kcal' },
  { value: '200_500', label: '200-500 kcal' },
  { value: '500_800', label: '500-800 kcal' },
  { value: '800_plus', label: '800+ kcal' },
];

const PANEL_ENTER_ANIMATION = 'food-log-toolbar-panel-enter 180ms cubic-bezier(0.22, 1, 0.36, 1) both';
const PANEL_ANIMATION_STYLE = `
@keyframes food-log-toolbar-panel-enter {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
`;

const RANGE_INPUT_CLASS = 'rounded-xl border border-[#4A453E]/15 bg-[#FFFEFB] px-2.5 py-2 text-xs text-[#4A453E] outline-none ring-0 transition-all duration-200 ease-out hover:border-[#4A453E]/22 focus:border-[#FF8A65]/45 focus:outline-none focus:ring-2 focus:ring-[#FF8A65]/12';

export const FoodLogSearchToolbar: React.FC<FoodLogSearchToolbarProps> = ({
  searchQuery,
  onSearchQueryChange,
  sort,
  onSortChange,
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  caloriePreset,
  customMinCalories,
  customMaxCalories,
  onCaloriePresetChange,
  onCustomMinCaloriesChange,
  onCustomMaxCaloriesChange,
  hasActiveFilters,
  onClearFilters,
}) => {
  const [openPanel, setOpenPanel] = useState<ToolbarPanel>(null);
  const [activeFilterType, setActiveFilterType] = useState<FilterType>('date');
  const [filterDraft, setFilterDraft] = useState<FilterDraft>(() => (
    buildFilterDraft(dateFrom, dateTo, caloriePreset, customMinCalories, customMaxCalories)
  ));
  const toolbarRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onDocumentClick = (event: MouseEvent) => {
      if (!toolbarRef.current) {
        return;
      }
      if (!toolbarRef.current.contains(event.target as Node)) {
        setOpenPanel(null);
      }
    };

    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpenPanel(null);
      }
    };

    document.addEventListener('mousedown', onDocumentClick);
    document.addEventListener('keydown', onEscape);
    return () => {
      document.removeEventListener('mousedown', onDocumentClick);
      document.removeEventListener('keydown', onEscape);
    };
  }, []);

  const filterLabel = useMemo(() => {
    const calorieLabel = getCalorieSummaryLabel(caloriePreset, customMinCalories, customMaxCalories);
    if (calorieLabel !== 'Any calories') {
      return calorieLabel;
    }
    if (dateFrom || dateTo) {
      return getDateSummaryLabel(dateFrom, dateTo);
    }
    return 'Any calories';
  }, [caloriePreset, customMinCalories, customMaxCalories, dateFrom, dateTo]);

  const appliedHasCustomCalories = useMemo(
    () => Boolean(customMinCalories.trim() || customMaxCalories.trim()),
    [customMinCalories, customMaxCalories],
  );

  const draftHasCustomCalories = useMemo(
    () => Boolean(filterDraft.minCalories.trim() || filterDraft.maxCalories.trim()),
    [filterDraft.maxCalories, filterDraft.minCalories],
  );

  const isSortSelected = sort !== 'created_desc';
  const isFilterSelected = appliedHasCustomCalories || caloriePreset !== 'any' || Boolean(dateFrom || dateTo);

  const togglePanel = (panel: Exclude<ToolbarPanel, null>) => {
    setOpenPanel((current) => {
      if (current === panel) {
        return null;
      }
      if (panel === 'filter') {
        setActiveFilterType('date');
        setFilterDraft(buildFilterDraft(dateFrom, dateTo, caloriePreset, customMinCalories, customMaxCalories));
      }
      return panel;
    });
  };

  const applyDraftLastNDays = (days: number) => {
    const today = new Date();
    const end = formatDateValue(today);
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - (days - 1));
    setFilterDraft((current) => ({
      ...current,
      dateFrom: formatDateValue(startDate),
      dateTo: end,
    }));
  };

  const handleDraftAnyTime = () => {
    setFilterDraft((current) => ({
      ...current,
      dateFrom: '',
      dateTo: '',
    }));
  };

  const handleFilterPresetSelect = (preset: FoodLogCaloriesPreset) => {
    setFilterDraft((current) => ({
      ...current,
      preset,
      minCalories: '',
      maxCalories: '',
    }));
  };

  const handleFilterMinChange = (value: string) => {
    setFilterDraft((current) => ({
      ...current,
      preset: 'any',
      minCalories: normalizeNumericInput(value),
    }));
  };

  const handleFilterMaxChange = (value: string) => {
    setFilterDraft((current) => ({
      ...current,
      preset: 'any',
      maxCalories: normalizeNumericInput(value),
    }));
  };

  const handleFilterReset = () => {
    setFilterDraft({
      dateFrom: '',
      dateTo: '',
      preset: 'any',
      minCalories: '',
      maxCalories: '',
    });
  };

  const handleFilterConfirm = () => {
    onDateFromChange(filterDraft.dateFrom);
    onDateToChange(filterDraft.dateTo);
    onCaloriePresetChange(filterDraft.preset);
    onCustomMinCaloriesChange(filterDraft.minCalories);
    onCustomMaxCaloriesChange(filterDraft.maxCalories);
    setOpenPanel(null);
  };

  return (
    <div
      ref={toolbarRef}
      className="rounded-[28px] border border-[#E7DED0] bg-white/95 p-4 shadow-[0_14px_36px_rgba(74,69,62,0.10)] backdrop-blur-sm md:p-5"
    >
      <style>{PANEL_ANIMATION_STYLE}</style>

      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <label className="group flex h-14 flex-1 items-center gap-3 rounded-full border border-[#E5DCCE] bg-[#FCFAF5] px-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)] transition-all duration-200 ease-out hover:border-[#D9CEBE] focus-within:border-[#FF8A65]/45 focus-within:shadow-[0_0_0_4px_rgba(255,138,101,0.10)]">
          <span className="material-symbols-outlined text-[20px] text-[#4A453E]/30 transition-colors duration-200 group-hover:text-[#4A453E]/45">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(event) => onSearchQueryChange(event.target.value)}
            placeholder="Search saved meals, notes, or ingredients"
            className="w-full appearance-none border-none bg-transparent text-[15px] leading-none text-[#3F3A34] outline-none ring-0 shadow-none placeholder:text-[#4A453E]/38 focus:border-none focus:outline-none focus:ring-0 focus-visible:outline-none"
          />
        </label>

        <div className="relative shrink-0">
          <ToolbarTrigger
            label="Filter"
            value={filterLabel}
            open={openPanel === 'filter'}
            selected={isFilterSelected}
            onClick={() => togglePanel('filter')}
          />
          {openPanel === 'filter' && (
            <div
              style={{ animation: PANEL_ENTER_ANIMATION }}
              className="absolute right-0 top-[calc(100%+10px)] z-30 w-[min(96vw,680px)] max-w-[680px] origin-top-right"
            >
              <div className="overflow-hidden rounded-[24px] border border-[#4A453E]/10 bg-[#FFFDF9] shadow-[0_18px_40px_rgba(74,69,62,0.12)]">
                <div className="grid min-h-[290px] grid-cols-[170px_1fr]">
                  <div className="border-r border-[#4A453E]/9 bg-[#FCFAF6] p-3">
                    <p className="px-2 text-[10px] font-semibold uppercase tracking-[0.09em] text-[#4A453E]/45">
                      Filter by
                    </p>
                    <div className="mt-2 space-y-2">
                      <FilterTypeButton
                        label="Date"
                        selected={activeFilterType === 'date'}
                        onClick={() => setActiveFilterType('date')}
                      />
                      <FilterTypeButton
                        label="Calories"
                        selected={activeFilterType === 'calories'}
                        onClick={() => setActiveFilterType('calories')}
                      />
                    </div>
                  </div>

                  <div className="p-5">
                    {activeFilterType === 'date' && (
                      <div className="space-y-4">
                        <div>
                          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#4A453E]/45">
                            Date
                          </p>
                          <div className="flex flex-wrap gap-2">
                            <PresetButton
                              label="Any time"
                              active={!filterDraft.dateFrom && !filterDraft.dateTo}
                              onClick={handleDraftAnyTime}
                            />
                            <PresetButton
                              label="Last 7 days"
                              active={isLastNDaysRange(filterDraft.dateFrom, filterDraft.dateTo, 7)}
                              onClick={() => applyDraftLastNDays(7)}
                            />
                            <PresetButton
                              label="Last 30 days"
                              active={isLastNDaysRange(filterDraft.dateFrom, filterDraft.dateTo, 30)}
                              onClick={() => applyDraftLastNDays(30)}
                            />
                          </div>
                        </div>
                        <div>
                          <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#4A453E]/45">
                            Custom range
                          </p>
                          <div className="grid grid-cols-2 gap-2">
                            <label className="flex flex-col gap-1 text-[11px] font-semibold text-[#4A453E]/55">
                              From
                              <input
                                type="date"
                                value={filterDraft.dateFrom}
                                onChange={(event) => setFilterDraft((current) => ({ ...current, dateFrom: event.target.value }))}
                                className={RANGE_INPUT_CLASS}
                              />
                            </label>
                            <label className="flex flex-col gap-1 text-[11px] font-semibold text-[#4A453E]/55">
                              To
                              <input
                                type="date"
                                value={filterDraft.dateTo}
                                onChange={(event) => setFilterDraft((current) => ({ ...current, dateTo: event.target.value }))}
                                className={RANGE_INPUT_CLASS}
                              />
                            </label>
                          </div>
                        </div>
                      </div>
                    )}
                    {activeFilterType === 'calories' && (
                      <div className="space-y-4">
                        <div>
                          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#4A453E]/45">
                            Calories
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {CALORIE_OPTIONS.map((option) => (
                              <PresetButton
                                key={option.value}
                                label={option.label}
                                active={!draftHasCustomCalories && filterDraft.preset === option.value}
                                onClick={() => handleFilterPresetSelect(option.value)}
                              />
                            ))}
                          </div>
                        </div>

                        <div>
                          <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#4A453E]/45">
                            Custom range
                          </p>
                          <div className="grid grid-cols-2 gap-2">
                            <label className="flex flex-col gap-1 text-[11px] font-semibold text-[#4A453E]/55">
                              Min kcal
                              <input
                                type="number"
                                min="0"
                                step="1"
                                value={filterDraft.minCalories}
                                onChange={(event) => handleFilterMinChange(event.target.value)}
                                placeholder="0"
                                className={RANGE_INPUT_CLASS}
                              />
                            </label>
                            <label className="flex flex-col gap-1 text-[11px] font-semibold text-[#4A453E]/55">
                              Max kcal
                              <input
                                type="number"
                                min="0"
                                step="1"
                                value={filterDraft.maxCalories}
                                onChange={(event) => handleFilterMaxChange(event.target.value)}
                                placeholder="1200"
                                className={RANGE_INPUT_CLASS}
                              />
                            </label>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-[#4A453E]/10 bg-[#FFFEFB] px-5 py-4">
                  <button
                    type="button"
                    onClick={handleFilterReset}
                    className="rounded-full border border-[#4A453E]/14 bg-white px-4 py-2 text-xs font-semibold text-[#4A453E]/65 transition-all duration-200 ease-out hover:border-[#4A453E]/22 hover:bg-[#F5F0E8] active:translate-y-[1px]"
                  >
                    Reset
                  </button>
                  <button
                    type="button"
                    onClick={handleFilterConfirm}
                    className="rounded-full border border-[#FF8A65] bg-[#FF8A65] px-5 py-2 text-xs font-semibold text-white shadow-[0_8px_18px_rgba(255,138,101,0.30)] transition-all duration-200 ease-out hover:bg-[#F57D59] active:translate-y-[1px]"
                  >
                    Confirm
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="relative shrink-0">
          <SortIconTrigger
            open={openPanel === 'sort'}
            selected={isSortSelected}
            onClick={() => togglePanel('sort')}
          />
          {openPanel === 'sort' && (
            <div
              style={{ animation: PANEL_ENTER_ANIMATION }}
              className="absolute right-0 top-[calc(100%+10px)] z-30 w-[272px] origin-top-right rounded-[24px] border border-[#4A453E]/10 bg-[#FFFDF9] p-2 shadow-[0_18px_40px_rgba(74,69,62,0.12)]"
            >
              {SORT_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onSortChange(option.value);
                    setOpenPanel(null);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm font-semibold transition-all duration-200 ease-out active:translate-y-[1px] ${
                    sort === option.value
                      ? 'border border-[#FF8A65] bg-[#FF8A65] text-white shadow-[0_8px_18px_rgba(255,138,101,0.30)]'
                      : 'text-[#4A453E]/75 hover:bg-[#F4EFE7]'
                  }`}
                >
                  <span>{option.label}</span>
                  {sort === option.value && (
                    <span className="material-symbols-outlined text-[16px] text-white">check</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {hasActiveFilters && (
        <button
          type="button"
          onClick={onClearFilters}
          className="mt-3 inline-flex rounded-full border border-[#4A453E]/12 bg-[#FFFCF7] px-3 py-1.5 text-[11px] font-semibold text-[#4A453E]/62 transition-colors hover:bg-[#F8F1E7]"
        >
          Clear Filters
        </button>
      )}
    </div>
  );
};

interface ToolbarTriggerProps {
  label: string;
  value: string;
  open: boolean;
  selected: boolean;
  onClick: () => void;
}

const ToolbarTrigger: React.FC<ToolbarTriggerProps> = ({
  label,
  value,
  open,
  selected,
  onClick,
}) => (
  <button
    type="button"
    onClick={onClick}
    aria-expanded={open}
    className={`group inline-flex h-[50px] min-w-[170px] items-center justify-between gap-3 rounded-full border px-4 text-left shadow-[inset_0_1px_0_rgba(255,255,255,0.7)] transition-all duration-200 ease-out active:translate-y-[1px] ${
      open
        ? 'border-[#FF8A65] bg-[#FF8A65] text-white shadow-[0_10px_20px_rgba(255,138,101,0.34)]'
        : selected
          ? 'border-[#FF8A65] bg-[#FF8A65] text-white shadow-[0_8px_16px_rgba(255,138,101,0.30)]'
          : 'border-[#E5DCCE] bg-[#FCFAF5] text-[#4A453E]/72 hover:border-[#D9CEBE] hover:bg-[#F7F3EA]'
    }`}
  >
    <span className="min-w-0 truncate text-[13px] font-semibold">
      {label}: {value}
    </span>
    <span className={`material-symbols-outlined text-[17px] transition-transform duration-200 ${open ? 'rotate-180' : ''}`}>
      expand_more
    </span>
  </button>
);

interface SortIconTriggerProps {
  open: boolean;
  selected: boolean;
  onClick: () => void;
}

const SortIconTrigger: React.FC<SortIconTriggerProps> = ({ open, selected, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    aria-expanded={open}
    aria-label="Sort options"
    className={`inline-flex h-[50px] w-[50px] items-center justify-center rounded-full border shadow-[inset_0_1px_0_rgba(255,255,255,0.7)] transition-all duration-200 ease-out active:translate-y-[1px] ${
      open
        ? 'border-[#FF8A65] bg-[#FF8A65] text-white shadow-[0_10px_20px_rgba(255,138,101,0.34)]'
        : selected
          ? 'border-[#FF8A65] bg-[#FF8A65] text-white shadow-[0_8px_16px_rgba(255,138,101,0.30)]'
          : 'border-[#E5DCCE] bg-[#FCFAF5] text-[#4A453E]/72 hover:border-[#D9CEBE] hover:bg-[#F7F3EA]'
    }`}
  >
    <span className="material-symbols-outlined text-[20px]">tune</span>
  </button>
);

interface PresetButtonProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

const PresetButton: React.FC<PresetButtonProps> = ({ label, active, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition-all duration-200 ease-out active:translate-y-[1px] ${
      active
        ? 'border-[#FF8A65] bg-[#FF8A65] text-white shadow-[0_8px_16px_rgba(255,138,101,0.30)]'
        : 'border-[#4A453E]/12 bg-[#F4F1EB] text-[#4A453E]/66 hover:bg-[#ECE7DE]'
    }`}
  >
    {label}
  </button>
);

interface FilterTypeButtonProps {
  label: string;
  selected: boolean;
  onClick: () => void;
}

const FilterTypeButton: React.FC<FilterTypeButtonProps> = ({ label, selected, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={`w-full rounded-xl border px-3 py-2 text-left text-sm font-semibold transition-all duration-200 ease-out active:translate-y-[1px] ${
      selected
        ? 'border-[#FF8A65] bg-[#FF8A65] text-white shadow-[0_8px_16px_rgba(255,138,101,0.30)]'
        : 'border-transparent text-[#4A453E]/52 hover:border-[#4A453E]/10 hover:bg-[#F2EDE4]'
    }`}
  >
    {label}
  </button>
);

function buildFilterDraft(
  dateFrom: string,
  dateTo: string,
  preset: FoodLogCaloriesPreset,
  minCalories: string,
  maxCalories: string,
): FilterDraft {
  return {
    dateFrom,
    dateTo,
    preset,
    minCalories,
    maxCalories,
  };
}

function getDateSummaryLabel(dateFrom: string, dateTo: string): string {
  if (!dateFrom && !dateTo) {
    return 'Any time';
  }

  if (isLastNDaysRange(dateFrom, dateTo, 7)) {
    return 'Last 7 days';
  }

  if (dateFrom && dateTo) {
    if (dateFrom === dateTo) {
      return formatDateForLabel(dateFrom);
    }
    return `${formatDateForLabel(dateFrom)} - ${formatDateForLabel(dateTo)}`;
  }

  if (dateFrom) {
    return `From ${formatDateForLabel(dateFrom)}`;
  }

  return `Until ${formatDateForLabel(dateTo)}`;
}

function getCalorieSummaryLabel(
  preset: FoodLogCaloriesPreset,
  minCalories: string,
  maxCalories: string,
): string {
  const normalizedMin = normalizeCalorieInput(minCalories);
  const normalizedMax = normalizeCalorieInput(maxCalories);

  if (normalizedMin || normalizedMax) {
    if (normalizedMin && normalizedMax) {
      return `${normalizedMin}-${normalizedMax} kcal`;
    }
    if (normalizedMin) {
      return `>= ${normalizedMin} kcal`;
    }
    return `<= ${normalizedMax} kcal`;
  }

  return CALORIE_OPTIONS.find((option) => option.value === preset)?.label ?? 'Any calories';
}

function normalizeCalorieInput(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return '';
  }

  const parsed = Number.parseFloat(trimmed);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return '';
  }

  return String(Math.round(parsed));
}

function normalizeNumericInput(value: string): string {
  if (!value) {
    return '';
  }
  return value.replace(/\D+/g, '');
}

function isLastNDaysRange(dateFrom: string, dateTo: string, days: number): boolean {
  if (!dateFrom || !dateTo) {
    return false;
  }

  const today = new Date();
  const expectedTo = formatDateValue(today);
  const expectedFromDate = new Date(today);
  expectedFromDate.setDate(today.getDate() - (days - 1));
  const expectedFrom = formatDateValue(expectedFromDate);

  return dateFrom === expectedFrom && dateTo === expectedTo;
}

function formatDateForLabel(value: string): string {
  const parsed = parseDateValue(value);
  if (!parsed) {
    return value;
  }

  return parsed.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function parseDateValue(value: string): Date | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed;
}

function formatDateValue(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

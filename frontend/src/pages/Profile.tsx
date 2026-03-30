import React, { useEffect, useState } from 'react';

import {
  loadStoredProfile,
  normalizeProfileForm,
  ProfileApiError,
  saveProfile,
  toProfileForm,
} from '../api/profile';
import { UserProfileForm } from '../types/types';
import {
  getRecommendedCalories,
  PACE_OPTIONS,
} from '../utils/calorieRecommendation';

interface ProfileProps {
  profile: UserProfileForm;
  setProfile: React.Dispatch<React.SetStateAction<UserProfileForm>>;
}

const SEX_OPTIONS = [
  { value: 'Male', label: '男' },
  { value: 'Female', label: '女' },
  { value: 'Prefer not to say', label: '不透露' },
];
const ACTIVITY_OPTIONS = [
  { value: 'Sedentary', label: '久坐为主', description: '每周几乎不运动' },
  { value: 'Lightly active', label: '轻度活跃', description: '每周运动 1-3 天' },
  { value: 'Moderately active', label: '中度活跃', description: '每周运动 3-5 天' },
  { value: 'Highly active', label: '高度活跃', description: '每周运动 6-7 天' },
];
const GOAL_OPTIONS = [
  { value: 'Fat loss', label: '减脂' },
  { value: 'Muscle gain', label: '增肌' },
  { value: 'General health', label: '健康维护' },
  { value: 'Performance', label: '表现提升' },
];
const DIET_STYLE_OPTIONS = [
  { value: 'Balanced', label: '均衡饮食', icon: 'nutrition' },
  { value: 'High protein', label: '高蛋白', icon: 'fitness_center' },
  { value: 'Low carb', label: '低碳水', icon: 'grain' },
  { value: 'Vegetarian', label: '素食', icon: 'eco' },
];
const ALLERGY_OPTIONS = [
  { value: 'Nuts', label: '坚果' },
  { value: 'Dairy', label: '乳制品' },
  { value: 'Seafood', label: '海鲜' },
  { value: 'Gluten', label: '麸质' },
  { value: 'Soy', label: '大豆' },
  { value: 'Shellfish', label: '甲壳类' },
];
const EXERCISE_OPTIONS = ['瑜伽', '跑步', '游泳', '健身', '骑行'];

const INPUT_CLASSNAME =
  'w-full bg-[#F7F3E9]/30 border border-[#4A453E]/05 rounded-[18px] px-4 py-3 text-[15px] font-medium text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all placeholder:text-[#4A453E]/20 disabled:cursor-not-allowed disabled:opacity-70';

type FormStatus = 'loading' | 'idle' | 'saving' | 'success' | 'error';
type TextProfileField =
  | 'age'
  | 'height'
  | 'weight'
  | 'sex'
  | 'activityLevel'
  | 'goal'
  | 'pace'
  | 'kcalTarget'
  | 'dietStyle';

export const Profile: React.FC<ProfileProps> = ({ profile, setProfile }) => {
  const [status, setStatus] = useState<FormStatus>('loading');
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [lastSavedProfile, setLastSavedProfile] = useState<UserProfileForm>(cloneProfile(profile));
  const [showAddExercise, setShowAddExercise] = useState(false);
  const [customExerciseInput, setCustomExerciseInput] = useState('');

  useEffect(() => {
    if (profile.id) {
      const hydratedProfile = cloneProfile(profile);
      setLastSavedProfile(hydratedProfile);
      setStatus('idle');
      setInlineError(null);
      return;
    }

    let cancelled = false;

    const syncProfile = async () => {
      setStatus('loading');
      setInlineError(null);

      try {
        const storedProfile = await loadStoredProfile();
        if (cancelled) {
          return;
        }

        if (storedProfile) {
          const nextProfile = toProfileForm(storedProfile);
          setProfile(cloneProfile(nextProfile));
          setLastSavedProfile(cloneProfile(nextProfile));
        } else {
          const normalizedInitial = cloneProfile(profile);
          setProfile(normalizedInitial);
          setLastSavedProfile(cloneProfile(normalizedInitial));
        }

        setStatus('idle');
      } catch (error) {
        if (cancelled) {
          return;
        }
        setInlineError(getErrorMessage(error));
        setStatus('error');
      }
    };

    syncProfile();

    return () => {
      cancelled = true;
    };
  }, [profile.id, setProfile]);

  useEffect(() => {
    if (status !== 'success' && status !== 'error') {
      return;
    }

    const timer = window.setTimeout(() => {
      setStatus('idle');
      if (status === 'success') {
        setBannerMessage(null);
      }
    }, 3000);

    return () => window.clearTimeout(timer);
  }, [status]);

  const currentForm = normalizeProfileForm(profile);
  const savedForm = normalizeProfileForm(lastSavedProfile);
  const isDirty = serializeProfileForm(currentForm) !== serializeProfileForm(savedForm);
  const hasRequiredFields = hasProfileRequiredFields(currentForm);
  const isBusy = status === 'loading' || status === 'saving';
  const saveDisabled = isBusy || !isDirty || !hasRequiredFields;
  const cancelDisabled = isBusy || !isDirty;

  const updateField = (key: TextProfileField, value: string) => {
    setProfile((prev) => {
      const next = { ...prev, [key]: value };
      const rec = getRecommendedCalories({
        age: parseInt(next.age, 10) || 0,
        height: parseFloat(next.height) || 0,
        weight: parseFloat(next.weight) || 0,
        sex: next.sex,
        activityLevel: next.activityLevel,
        goal: next.goal,
        pace: next.pace,
      });
      if (rec.canCalculate && (key === 'pace' || key === 'goal' || key === 'age' || key === 'height' || key === 'weight' || key === 'sex' || key === 'activityLevel')) {
        next.kcalTarget = String(rec.recommendedKcal);
      }
      return next;
    });
    if (inlineError) {
      setInlineError(null);
    }
    if (bannerMessage && status !== 'success') {
      setBannerMessage(null);
    }
  };

  const toggleAllergy = (allergy: string) => {
    setProfile((prev) => {
      const exists = prev.allergies.includes(allergy);
      return {
        ...prev,
        allergies: exists
          ? prev.allergies.filter((item) => item !== allergy)
          : [...prev.allergies, allergy],
      };
    });
    if (inlineError) {
      setInlineError(null);
    }
  };

  const parseExerciseTypes = (value: string): string[] => {
    if (!value?.trim()) return [];
    return value.split(',').map((s) => s.trim()).filter(Boolean);
  };

  const toggleExercise = (exercise: string) => {
    setProfile((prev) => {
      const current = parseExerciseTypes(prev.exerciseType);
      const exists = current.includes(exercise);
      const next = exists ? current.filter((x) => x !== exercise) : [...current, exercise];
      return { ...prev, exerciseType: next.join(', ') };
    });
    if (inlineError) setInlineError(null);
  };

  const addCustomExercise = () => {
    const trimmed = customExerciseInput.trim();
    if (!trimmed) return;
    setProfile((prev) => {
      const current = parseExerciseTypes(prev.exerciseType);
      if (current.includes(trimmed)) return prev;
      return { ...prev, exerciseType: [...current, trimmed].join(', ') };
    });
    setCustomExerciseInput('');
    setShowAddExercise(false);
    if (inlineError) setInlineError(null);
  };

  const handleSave = async () => {
    if (saveDisabled) {
      return;
    }

    setStatus('saving');
    setInlineError(null);
    setBannerMessage(null);

    try {
      const savedProfile = await saveProfile(currentForm);
      const nextProfile = toProfileForm(savedProfile);
      setProfile(cloneProfile(nextProfile));
      setLastSavedProfile(cloneProfile(nextProfile));
      setBannerMessage('档案已保存。');
      setStatus('success');
    } catch (error) {
      setInlineError(getErrorMessage(error));
      setBannerMessage(getErrorMessage(error));
      setStatus('error');
    }
  };

  const handleCancel = () => {
    if (cancelDisabled) {
      return;
    }

    const restored = cloneProfile(lastSavedProfile);
    setProfile(restored);
    setInlineError(null);
    setBannerMessage(null);
    setStatus('idle');
  };

  return (
    <div className="relative mx-auto flex w-full max-w-[1200px] flex-1 flex-col overflow-y-auto custom-scrollbar px-8 py-12 lg:py-14">
      {(status === 'success' || status === 'error') && bannerMessage && (
        <div
          className={`fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 animate-in slide-in-from-bottom-4 duration-300 ${
            status === 'success' ? 'bg-[#81C784] text-white' : 'bg-red-400 text-white'
          }`}
        >
          <span className="material-symbols-outlined text-sm font-bold">
            {status === 'success' ? 'check_circle' : 'error'}
          </span>
          <span className="text-sm font-bold tracking-[0.08em]">{bannerMessage}</span>
        </div>
      )}

      <div className="mb-14 flex flex-col items-start justify-between gap-7 md:flex-row md:items-center">
        <div className="flex flex-col gap-2">
          <h1 className="font-serif-brand text-[2.5rem] font-bold leading-[1.18] text-[#4A453E] md:text-[2.9rem]">个人档案</h1>
          <p className="max-w-2xl text-[15px] leading-8 text-[#4A453E]/60 md:text-[16px]">
            个人档案用于告诉助手“它在为谁提供建议”，并让已保存的饮食记录始终基于相同的目标、偏好和限制条件。
          </p>
          {status === 'loading' && (
            <p className="text-sm font-bold text-[#FF8A65]">正在加载个人档案...</p>
          )}
          {inlineError && (
            <p className="text-sm font-medium text-red-500">{inlineError}</p>
          )}
          {!inlineError && isDirty && !hasRequiredFields && (
            <p className="text-sm font-medium text-[#FF8A65]">
              请先完善必填档案字段再保存。
            </p>
          )}
          {!inlineError && isDirty && status !== 'saving' && (
            <p className="text-sm font-medium text-[#FF8A65]">你有未保存的更改。</p>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/35">
            {status === 'saving'
              ? '保存中'
              : status === 'loading'
                ? '加载中'
                : isDirty
                  ? '未保存'
                  : '已保存'}
          </span>
          <button
            type="button"
            onClick={handleCancel}
            disabled={cancelDisabled}
            className="px-6 py-3 bg-white text-[#4A453E]/40 font-bold text-sm rounded-full border border-[#4A453E]/10 hover:bg-[#F7F3E9] transition-all disabled:cursor-not-allowed disabled:opacity-60"
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saveDisabled}
            className={`flex items-center gap-2 px-8 py-3 font-bold text-sm rounded-full shadow-lg transition-all min-w-[160px] justify-center ${
              saveDisabled
                ? 'bg-[#4A453E]/10 text-[#4A453E]/40 cursor-not-allowed shadow-none'
                : 'bg-[#FF8A65] text-white shadow-[#FF8A65]/20 hover:translate-y-[-1px]'
            }`}
          >
            {status === 'saving' ? (
              <>
                <span className="material-symbols-outlined text-sm font-bold animate-spin">progress_activity</span>
                <span>保存中...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-sm font-bold">check</span>
                <span>{profile.id ? '保存修改' : '创建档案'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      <fieldset disabled={isBusy} className="contents">
        <div className={`transition-opacity ${isBusy ? 'opacity-80' : 'opacity-100'}`}>
          <div className="mb-14 grid grid-cols-1 gap-10 lg:grid-cols-2">
            <div className="space-y-10">
              <section className="rounded-[32px] border border-[#4A453E]/05 bg-white p-9 shadow-sm lg:p-10">
                <div className="mb-9 flex items-center gap-3">
                  <div className="size-10 rounded-2xl bg-[#FF8A65]/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#FF8A65]">person</span>
                  </div>
                  <h3 className="font-serif-brand text-[22px] font-bold leading-[1.25] text-[#4A453E]">身体数据</h3>
                </div>

                <div className="mb-9 grid grid-cols-1 gap-6 sm:grid-cols-3">
                  <Field label="年龄">
                    <input type="number" value={profile.age} onChange={(event) => updateField('age', event.target.value)} placeholder="岁" className={INPUT_CLASSNAME} />
                  </Field>
                  <Field label="身高 (cm)">
                    <input type="number" value={profile.height} onChange={(event) => updateField('height', event.target.value)} placeholder="厘米" className={INPUT_CLASSNAME} />
                  </Field>
                  <Field label="体重 (kg)">
                    <input type="number" value={profile.weight} onChange={(event) => updateField('weight', event.target.value)} placeholder="千克" className={INPUT_CLASSNAME} />
                  </Field>
                </div>

                <div className="flex flex-col gap-2">
                  <label className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#4A453E]/40">
                    性别
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {SEX_OPTIONS.map((option) => (
                      <label key={option.value} className="flex-1 min-w-[120px] group relative flex items-center justify-center p-3 bg-[#F7F3E9]/30 border border-transparent rounded-[18px] cursor-pointer transition-all hover:bg-white hover:border-[#FF8A65]/10 has-[:checked]:border-[#FF8A65] has-[:checked]:bg-white">
                        <input type="radio" name="sex" className="sr-only" checked={profile.sex === option.value} onChange={() => updateField('sex', option.value)} />
                        <span className="text-xs font-bold text-[#4A453E]/60 group-has-[:checked]:text-[#FF8A65]">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </section>

              <section className="rounded-[32px] border border-[#4A453E]/05 bg-white p-9 shadow-sm lg:p-10">
                <div className="mb-9 flex items-center gap-3">
                  <div className="size-10 rounded-2xl bg-[#81C784]/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#81C784]">directions_run</span>
                  </div>
                  <h3 className="font-serif-brand text-[22px] font-bold leading-[1.25] text-[#4A453E]">生活方式与训练</h3>
                </div>

                <div className="space-y-7">
                  <div>
                    <label className="mb-4 block px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#4A453E]/40">
                      活动水平
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {ACTIVITY_OPTIONS.map((option) => (
                        <label key={option.value} className="group flex flex-col p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#81C784]/20 has-[:checked]:border-[#81C784] has-[:checked]:bg-white overflow-hidden">
                          <input type="radio" name="activity" className="sr-only" checked={profile.activityLevel === option.value} onChange={() => updateField('activityLevel', option.value)} />
                          <span className="text-sm font-bold text-[#4A453E] group-has-[:checked]:text-[#81C784] truncate">{option.label}</span>
                          <span className="text-[10px] text-[#4A453E]/40 font-bold uppercase mt-1 truncate">{option.description}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="mb-4 block px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#4A453E]/40">
                      运动类型
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {EXERCISE_OPTIONS.map((option) => {
                        const checked = parseExerciseTypes(profile.exerciseType).includes(option);
                        return (
                          <label key={option} className="group relative flex items-center gap-2 px-4 py-2 bg-[#F7F3E9]/30 border border-transparent rounded-full cursor-pointer transition-all hover:bg-white hover:border-[#4A453E]/10 has-[:checked]:bg-[#4A453E] has-[:checked]:text-white overflow-hidden">
                            <input type="checkbox" className="sr-only" checked={checked} onChange={() => toggleExercise(option)} />
                            <span className={`text-xs font-bold transition-colors truncate ${checked ? 'text-white' : 'text-[#4A453E]/60'}`}>{option}</span>
                            {checked && <span className="material-symbols-outlined text-sm font-bold text-white shrink-0">close</span>}
                          </label>
                        );
                      })}
                      {parseExerciseTypes(profile.exerciseType)
                        .filter((x) => !EXERCISE_OPTIONS.includes(x))
                        .map((custom) => (
                          <label key={custom} className="group relative flex items-center gap-2 px-4 py-2 bg-[#4A453E] text-white border border-transparent rounded-full cursor-pointer transition-all hover:bg-[#3a3630] overflow-hidden">
                            <input type="checkbox" className="sr-only" checked onChange={() => toggleExercise(custom)} />
                            <span className="text-xs font-bold truncate">{custom}</span>
                            <span className="material-symbols-outlined text-sm font-bold shrink-0">close</span>
                          </label>
                        ))}
                      {showAddExercise ? (
                        <div className="flex items-center gap-2 px-3 py-2 bg-white border border-[#81C784]/30 rounded-full">
                          <input
                            type="text"
                            value={customExerciseInput}
                            onChange={(e) => setCustomExerciseInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addCustomExercise()}
                            placeholder="输入运动名称"
                            className="w-24 text-xs font-bold text-[#4A453E] bg-transparent outline-none placeholder:text-[#4A453E]/30"
                            autoFocus
                          />
                          <button
                            type="button"
                            onClick={addCustomExercise}
                            disabled={!customExerciseInput.trim()}
                            className="p-1 rounded-full bg-[#81C784] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#6AB76B] transition-colors"
                          >
                            <span className="material-symbols-outlined text-sm font-bold">check</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => { setShowAddExercise(false); setCustomExerciseInput(''); }}
                            className="p-1 rounded-full text-[#4A453E]/50 hover:bg-[#4A453E]/10 transition-colors"
                          >
                            <span className="material-symbols-outlined text-sm font-bold">close</span>
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setShowAddExercise(true)}
                          className="flex items-center justify-center gap-1 px-4 py-2 bg-[#F7F3E9]/30 border border-dashed border-[#4A453E]/20 rounded-full cursor-pointer transition-all hover:bg-white hover:border-[#81C784]/30 hover:text-[#81C784] text-[#4A453E]/50"
                        >
                          <span className="material-symbols-outlined text-sm font-bold">add</span>
                          <span className="text-xs font-bold">添加</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </section>
            </div>

            <div className="space-y-10">
              <section className="rounded-[32px] border border-[#4A453E]/05 bg-white p-9 shadow-sm lg:p-10">
                <div className="mb-9 flex items-center gap-3">
                  <div className="size-10 rounded-2xl bg-[#FF8A65]/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#FF8A65]">flag</span>
                  </div>
                  <h3 className="font-serif-brand text-[22px] font-bold leading-[1.25] text-[#4A453E]">目标与节奏</h3>
                </div>

                <div className="space-y-9">
                  <div>
                    <label className="mb-4 block px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#4A453E]/40">
                      主要目标
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {GOAL_OPTIONS.map((option) => (
                        <label key={option.value} className="group p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#FF8A65]/20 has-[:checked]:border-[#FF8A65] has-[:checked]:bg-white overflow-hidden">
                          <input type="radio" name="goal" className="sr-only" checked={profile.goal === option.value} onChange={() => updateField('goal', option.value)} />
                          <span className="text-sm font-bold text-[#4A453E] group-has-[:checked]:text-[#FF8A65] truncate">{option.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="mb-4 block px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#4A453E]/40">
                      计划节奏
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-6">
                      {PACE_OPTIONS.map((option) => (
                        <label
                          key={option.value}
                          className="group flex flex-col p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#FF8A65]/20 has-[:checked]:border-[#FF8A65] has-[:checked]:bg-white overflow-hidden"
                        >
                          <input
                            type="radio"
                            name="pace"
                            className="sr-only"
                            checked={profile.pace === option.value}
                            onChange={() => updateField('pace', option.value)}
                          />
                          <span className="text-sm font-bold text-[#4A453E] group-has-[:checked]:text-[#FF8A65] truncate">
                            {option.label}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <Field label="每日热量目标">
                    <div className="relative group">
                      <input
                        type="number"
                        value={profile.kcalTarget}
                        onChange={(event) => updateField('kcalTarget', event.target.value)}
                        className={INPUT_CLASSNAME}
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[9px] font-bold text-[#4A453E]/20 uppercase">
                        kcal
                      </span>
                    </div>
                    {(() => {
                      const rec = getRecommendedCalories({
                        age: parseInt(profile.age, 10) || 0,
                        height: parseFloat(profile.height) || 0,
                        weight: parseFloat(profile.weight) || 0,
                        sex: profile.sex,
                        activityLevel: profile.activityLevel,
                        goal: profile.goal,
                        pace: profile.pace,
                      });
                      return rec.canCalculate ? (
                        <p className="text-[10px] text-[#4A453E]/50 mt-2 px-1">
                          基础代谢 BMR: {rec.bmr} · 总消耗 TDEE: {rec.tdee} kcal · 建议目标: {rec.recommendedKcal} kcal
                        </p>
                      ) : null;
                    })()}
                  </Field>
                </div>
              </section>

              <section className="rounded-[32px] border border-[#4A453E]/05 bg-white p-9 shadow-sm lg:p-10">
                <div className="mb-9 flex items-center gap-3">
                  <div className="size-10 rounded-2xl bg-[#81C784]/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#81C784]">restaurant</span>
                  </div>
                  <h3 className="font-serif-brand text-[22px] font-bold leading-[1.25] text-[#4A453E]">饮食偏好</h3>
                </div>

                <div className="space-y-9">
                  <div>
                    <label className="mb-4 block px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#4A453E]/40">
                      饮食风格
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {DIET_STYLE_OPTIONS.map((option) => (
                        <label key={option.value} className="group flex items-center gap-3 p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#81C784]/20 has-[:checked]:border-[#81C784] has-[:checked]:bg-white overflow-hidden min-h-[64px]">
                          <input type="radio" name="diet-style" className="sr-only" checked={profile.dietStyle === option.value} onChange={() => updateField('dietStyle', option.value)} />
                          <span className="material-symbols-outlined text-[#4A453E]/20 group-has-[:checked]:text-[#81C784] transition-colors shrink-0 w-6 flex justify-center">{option.icon}</span>
                          <span className="text-sm font-bold text-[#4A453E]/70 group-has-[:checked]:text-[#4A453E] truncate">{option.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="mb-4 block px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#4A453E]/40">
                      过敏与忌口
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {ALLERGY_OPTIONS.map((option) => {
                        const checked = profile.allergies.includes(option.value);
                        return (
                          <label key={option.value} className="group relative flex items-center gap-2 px-4 py-2 bg-[#F7F3E9]/30 border border-transparent rounded-full cursor-pointer transition-all hover:bg-white hover:border-[#4A453E]/10 has-[:checked]:bg-[#4A453E] has-[:checked]:text-white overflow-hidden">
                            <input type="checkbox" className="sr-only" checked={checked} onChange={() => toggleAllergy(option.value)} />
                            <span className={`text-xs font-bold transition-colors truncate ${checked ? 'text-white' : 'text-[#4A453E]/60'}`}>{option.label}</span>
                            {checked && <span className="material-symbols-outlined text-sm font-bold text-white shrink-0">close</span>}
                          </label>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>
      </fieldset>

      <div className="mx-auto mb-24 max-w-3xl rounded-[32px] border border-[#4A453E]/05 bg-[#F7F3E9]/40 p-9 text-center lg:p-10">
        <h5 className="mb-3 flex items-center justify-center gap-2 text-[11px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/60">
          <span className="material-symbols-outlined text-base">info</span>
          说明
        </h5>
        <p className="text-xs text-[#4A453E]/50 leading-relaxed font-medium">
          个人档案用于个性化助手回复，并为你保存的饮食记录提供上下文。它不能替代医疗建议、诊断或治疗。
        </p>
      </div>
    </div>
  );
};

interface FieldProps {
  label: string;
  children: React.ReactNode;
}

const Field: React.FC<FieldProps> = ({ label, children }) => {
  return (
    <div className="flex flex-col gap-2">
      <label className="px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#4A453E]/40">{label}</label>
      {children}
    </div>
  );
};

function cloneProfile(profile: UserProfileForm): UserProfileForm {
  return {
    ...profile,
    allergies: [...profile.allergies],
  };
}

function serializeProfileForm(profile: UserProfileForm): string {
  return JSON.stringify({
    ...profile,
    allergies: [...profile.allergies],
  });
}

function hasProfileRequiredFields(profile: UserProfileForm): boolean {
  return Boolean(
    profile.age &&
      profile.height &&
      profile.weight &&
      profile.sex &&
      profile.activityLevel &&
      profile.goal &&
      profile.pace &&
      profile.kcalTarget &&
      profile.dietStyle,
  );
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ProfileApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return '保存档案失败，请稍后重试。';
}

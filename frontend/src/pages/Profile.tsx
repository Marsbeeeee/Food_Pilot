import React, { useEffect, useRef, useState } from 'react';

import { loadStoredProfile, ProfileApiError, saveProfile, toProfileForm } from '../api/profile';
import { UserProfileForm } from '../types/types';

interface ProfileProps {
  profile: UserProfileForm;
  setProfile: React.Dispatch<React.SetStateAction<UserProfileForm>>;
}

const SEX_OPTIONS = ['男', '女', '不愿透露'];
const ACTIVITY_OPTIONS = [
  { value: '久坐', description: '极少或没有运动' },
  { value: '轻度活动', description: '每周运动 1-3 天' },
  { value: '中度活动', description: '每周运动 3-5 天' },
  { value: '高度活动', description: '每周运动 6-7 天' },
];
const GOAL_OPTIONS = ['减脂', '增肌', '日常健康', '巅峰体能'];
const DIET_STYLE_OPTIONS = [
  { label: '均衡饮食', icon: 'nutrition' },
  { label: '高蛋白饮食', icon: 'fitness_center' },
  { label: '低碳饮食', icon: 'grain' },
  { label: '素食', icon: 'eco' },
];
const ALLERGY_OPTIONS = ['坚果', '乳制品', '海鲜', '麸质', '大豆', '甲壳类'];
const INPUT_CLASSNAME =
  'w-full bg-[#F7F3E9]/30 border border-[#4A453E]/05 rounded-[18px] px-4 py-3 font-bold text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all placeholder:text-[#4A453E]/20';

type TextProfileField =
  | 'age'
  | 'height'
  | 'weight'
  | 'sex'
  | 'activityLevel'
  | 'exerciseType'
  | 'goal'
  | 'pace'
  | 'kcalTarget'
  | 'dietStyle';

export const Profile: React.FC<ProfileProps> = ({ profile, setProfile }) => {
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const initialProfileRef = useRef(profile);
  const [lastSavedProfile, setLastSavedProfile] = useState<UserProfileForm>(profile);

  useEffect(() => {
    let isMounted = true;

    const syncProfile = async () => {
      setIsLoading(true);
      setMessage(null);

      try {
        const storedProfile = await loadStoredProfile();
        if (!isMounted) {
          return;
        }

        if (storedProfile) {
          const nextProfile = toProfileForm(storedProfile);
          setProfile(nextProfile);
          setLastSavedProfile(nextProfile);
        } else {
          setLastSavedProfile(initialProfileRef.current);
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setMessage(getErrorMessage(error));
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    syncProfile();
    return () => {
      isMounted = false;
    };
  }, [setProfile]);

  useEffect(() => {
    if (saveStatus === 'success' || saveStatus === 'error') {
      const timer = window.setTimeout(() => {
        setSaveStatus('idle');
      }, 3000);
      return () => window.clearTimeout(timer);
    }
  }, [saveStatus]);

  const updateField = (key: TextProfileField, value: string) => {
    setProfile((prev) => ({ ...prev, [key]: value }));
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
  };

  const handleSave = async () => {
    if (isLoading || saveStatus === 'saving') {
      return;
    }

    setSaveStatus('saving');
    setMessage(null);

    try {
      const savedProfile = await saveProfile(profile);
      const nextProfile = toProfileForm(savedProfile);
      setProfile(nextProfile);
      setLastSavedProfile(nextProfile);
      setSaveStatus('success');
      setMessage('画像已保存到后端。');
    } catch (error) {
      setSaveStatus('error');
      setMessage(getErrorMessage(error));
    }
  };

  const handleCancel = () => {
    setProfile(lastSavedProfile);
    setMessage(null);
    setSaveStatus('idle');
  };

  return (
    <div className="flex-1 flex flex-col px-8 py-10 max-w-[1200px] mx-auto w-full overflow-y-auto custom-scrollbar relative">
      {(saveStatus === 'success' || saveStatus === 'error') && message && (
        <div
          className={`fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 animate-in slide-in-from-bottom-4 duration-300 ${
            saveStatus === 'success' ? 'bg-[#81C784] text-white' : 'bg-red-400 text-white'
          }`}
        >
          <span className="material-symbols-outlined text-sm font-bold">
            {saveStatus === 'success' ? 'check_circle' : 'error'}
          </span>
          <span className="text-sm font-bold tracking-wide">{message}</span>
        </div>
      )}

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-serif-brand font-bold text-[#4A453E]">个人档案</h1>
          <p className="text-[#4A453E]/60 text-base max-w-2xl">
            Food Pilot 会根据你的画像提供更贴近目标的热量估算和饮食建议。
          </p>
          {isLoading && (
            <p className="text-sm font-bold text-[#FF8A65]">正在同步已保存的画像...</p>
          )}
          {!isLoading && saveStatus === 'idle' && message && (
            <p className="text-sm text-red-500">{message}</p>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleCancel}
            disabled={isLoading || saveStatus === 'saving'}
            className="px-6 py-3 bg-white text-[#4A453E]/40 font-bold text-sm rounded-full border border-[#4A453E]/10 hover:bg-[#F7F3E9] transition-all disabled:cursor-not-allowed disabled:opacity-60"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={isLoading || saveStatus === 'saving'}
            className={`flex items-center gap-2 px-8 py-3 font-bold text-sm rounded-full shadow-lg transition-all min-w-[160px] justify-center ${
              isLoading || saveStatus === 'saving'
                ? 'bg-[#4A453E]/10 text-[#4A453E]/40 cursor-wait shadow-none'
                : 'bg-[#FF8A65] text-white shadow-[#FF8A65]/20 hover:translate-y-[-1px]'
            }`}
          >
            {saveStatus === 'saving' ? (
              <>
                <span className="material-symbols-outlined text-sm font-bold animate-spin">progress_activity</span>
                <span>保存中...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-sm font-bold">check</span>
                <span>{profile.id ? '更新画像' : '创建画像'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        <div className="space-y-8">
          <section className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <div className="size-10 rounded-2xl bg-[#FF8A65]/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-[#FF8A65]">person</span>
              </div>
              <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">身体数据</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
              <Field label="年龄">
                <input type="number" value={profile.age} onChange={(event) => updateField('age', event.target.value)} placeholder="岁" className={INPUT_CLASSNAME} />
              </Field>
              <Field label="身高 (cm)">
                <input type="number" value={profile.height} onChange={(event) => updateField('height', event.target.value)} placeholder="厘米" className={INPUT_CLASSNAME} />
              </Field>
              <Field label="体重 (kg)">
                <input type="number" value={profile.weight} onChange={(event) => updateField('weight', event.target.value)} placeholder="公斤" className={INPUT_CLASSNAME} />
              </Field>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-2">
                生理性别
              </label>
              <div className="flex flex-wrap gap-2">
                {SEX_OPTIONS.map((option) => (
                  <label key={option} className="flex-1 min-w-[120px] group relative flex items-center justify-center p-3 bg-[#F7F3E9]/30 border border-transparent rounded-[18px] cursor-pointer transition-all hover:bg-white hover:border-[#FF8A65]/10 has-[:checked]:border-[#FF8A65] has-[:checked]:bg-white">
                    <input type="radio" name="sex" className="sr-only" checked={profile.sex === option} onChange={() => updateField('sex', option)} />
                    <span className="text-xs font-bold text-[#4A453E]/60 group-has-[:checked]:text-[#FF8A65]">{option}</span>
                  </label>
                ))}
              </div>
            </div>
          </section>

          <section className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <div className="size-10 rounded-2xl bg-[#81C784]/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-[#81C784]">directions_run</span>
              </div>
              <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">生活方式与运动</h3>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">
                  日常活动水平
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {ACTIVITY_OPTIONS.map((option) => (
                    <label key={option.value} className="group flex flex-col p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#81C784]/20 has-[:checked]:border-[#81C784] has-[:checked]:bg-white overflow-hidden">
                      <input type="radio" name="activity" className="sr-only" checked={profile.activityLevel === option.value} onChange={() => updateField('activityLevel', option.value)} />
                      <span className="text-sm font-bold text-[#4A453E] group-has-[:checked]:text-[#81C784] truncate">{option.value}</span>
                      <span className="text-[10px] text-[#4A453E]/40 font-bold uppercase mt-1 truncate">{option.description}</span>
                    </label>
                  ))}
                </div>
              </div>

              <Field label="运动类型">
                <input type="text" value={profile.exerciseType} onChange={(event) => updateField('exerciseType', event.target.value)} placeholder="例如：力量训练、跑步、瑜伽" className={INPUT_CLASSNAME} />
              </Field>
            </div>
          </section>
        </div>

        <div className="space-y-8">
          <section className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <div className="size-10 rounded-2xl bg-[#FF8A65]/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-[#FF8A65]">flag</span>
              </div>
              <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">目标与节奏</h3>
            </div>

            <div className="space-y-8">
              <div>
                <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">
                  主要目标
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {GOAL_OPTIONS.map((option) => (
                    <label key={option} className="group p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#FF8A65]/20 has-[:checked]:border-[#FF8A65] has-[:checked]:bg-white overflow-hidden">
                      <input type="radio" name="goal" className="sr-only" checked={profile.goal === option} onChange={() => updateField('goal', option)} />
                      <span className="text-sm font-bold text-[#4A453E] group-has-[:checked]:text-[#FF8A65] truncate">{option}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <Field label="每日热量目标">
                  <div className="relative group">
                    <input type="number" value={profile.kcalTarget} onChange={(event) => updateField('kcalTarget', event.target.value)} className={INPUT_CLASSNAME} />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[9px] font-bold text-[#4A453E]/20 uppercase">kcal</span>
                  </div>
                </Field>
                <Field label="执行节奏">
                  <input type="text" value={profile.pace} onChange={(event) => updateField('pace', event.target.value)} placeholder="例如：适中、积极、保守" className={INPUT_CLASSNAME} />
                </Field>
              </div>
            </div>
          </section>

          <section className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <div className="size-10 rounded-2xl bg-[#81C784]/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-[#81C784]">restaurant</span>
              </div>
              <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">饮食习惯</h3>
            </div>

            <div className="space-y-8">
              <div>
                <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">
                  饮食偏好
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {DIET_STYLE_OPTIONS.map((option) => (
                    <label key={option.label} className="group flex items-center gap-3 p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#81C784]/20 has-[:checked]:border-[#81C784] has-[:checked]:bg-white overflow-hidden min-h-[64px]">
                      <input type="radio" name="diet-style" className="sr-only" checked={profile.dietStyle === option.label} onChange={() => updateField('dietStyle', option.label)} />
                      <span className="material-symbols-outlined text-[#4A453E]/20 group-has-[:checked]:text-[#81C784] transition-colors shrink-0 w-6 flex justify-center">{option.icon}</span>
                      <span className="text-sm font-bold text-[#4A453E]/70 group-has-[:checked]:text-[#4A453E] truncate">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">
                  过敏原与忌口
                </label>
                <div className="flex flex-wrap gap-2">
                  {ALLERGY_OPTIONS.map((option) => {
                    const checked = profile.allergies.includes(option);
                    return (
                      <label key={option} className="group relative flex items-center gap-2 px-4 py-2 bg-[#F7F3E9]/30 border border-transparent rounded-full cursor-pointer transition-all hover:bg-white hover:border-[#4A453E]/10 has-[:checked]:bg-[#4A453E] has-[:checked]:text-white overflow-hidden">
                        <input type="checkbox" className="sr-only" checked={checked} onChange={() => toggleAllergy(option)} />
                        <span className={`text-xs font-bold transition-colors truncate ${checked ? 'text-white' : 'text-[#4A453E]/60'}`}>{option}</span>
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

      <div className="bg-[#F7F3E9]/40 border border-[#4A453E]/05 rounded-[32px] p-8 text-center max-w-3xl mx-auto mb-20">
        <h5 className="text-[11px] font-bold text-[#4A453E]/60 uppercase tracking-widest mb-3 flex items-center justify-center gap-2">
          <span className="material-symbols-outlined text-base">info</span>
          重要提示
        </h5>
        <p className="text-xs text-[#4A453E]/50 leading-relaxed font-medium">
          画像信息仅用于个性化热量估算和饮食建议，不构成医疗建议、诊断或治疗方案。
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
      <label className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1">{label}</label>
      {children}
    </div>
  );
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ProfileApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return '画像保存失败，请稍后重试。';
}

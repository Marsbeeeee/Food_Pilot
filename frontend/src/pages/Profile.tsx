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

const SEX_OPTIONS = ['Male', 'Female', 'Prefer not to say'];
const ACTIVITY_OPTIONS = [
  { value: 'Sedentary', description: 'Little or no weekly exercise' },
  { value: 'Lightly active', description: 'Exercise 1-3 days per week' },
  { value: 'Moderately active', description: 'Exercise 3-5 days per week' },
  { value: 'Highly active', description: 'Exercise 6-7 days per week' },
];
const GOAL_OPTIONS = ['Fat loss', 'Muscle gain', 'General health', 'Performance'];
const DIET_STYLE_OPTIONS = [
  { label: 'Balanced', icon: 'nutrition' },
  { label: 'High protein', icon: 'fitness_center' },
  { label: 'Low carb', icon: 'grain' },
  { label: 'Vegetarian', icon: 'eco' },
];
const ALLERGY_OPTIONS = ['Nuts', 'Dairy', 'Seafood', 'Gluten', 'Soy', 'Shellfish'];

const INPUT_CLASSNAME =
  'w-full bg-[#F7F3E9]/30 border border-[#4A453E]/05 rounded-[18px] px-4 py-3 font-bold text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all placeholder:text-[#4A453E]/20 disabled:cursor-not-allowed disabled:opacity-70';

type FormStatus = 'loading' | 'idle' | 'saving' | 'success' | 'error';
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
  const [status, setStatus] = useState<FormStatus>('loading');
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [lastSavedProfile, setLastSavedProfile] = useState<UserProfileForm>(cloneProfile(profile));

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
      setBannerMessage('Profile saved.');
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
    <div className="flex-1 flex flex-col px-8 py-10 max-w-[1200px] mx-auto w-full overflow-y-auto custom-scrollbar relative">
      {(status === 'success' || status === 'error') && bannerMessage && (
        <div
          className={`fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 animate-in slide-in-from-bottom-4 duration-300 ${
            status === 'success' ? 'bg-[#81C784] text-white' : 'bg-red-400 text-white'
          }`}
        >
          <span className="material-symbols-outlined text-sm font-bold">
            {status === 'success' ? 'check_circle' : 'error'}
          </span>
          <span className="text-sm font-bold tracking-wide">{bannerMessage}</span>
        </div>
      )}

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-serif-brand font-bold text-[#4A453E]">Profile</h1>
          <p className="text-[#4A453E]/60 text-base max-w-2xl">
            Profile tells the Assistant who it is answering for and keeps saved Food Log entries
            grounded in the same goals, preferences, and constraints.
          </p>
          {status === 'loading' && (
            <p className="text-sm font-bold text-[#FF8A65]">Loading your Profile...</p>
          )}
          {inlineError && (
            <p className="text-sm font-medium text-red-500">{inlineError}</p>
          )}
          {!inlineError && isDirty && !hasRequiredFields && (
            <p className="text-sm font-medium text-[#FF8A65]">
              Complete the required profile fields before saving.
            </p>
          )}
          {!inlineError && isDirty && status !== 'saving' && (
            <p className="text-sm font-medium text-[#FF8A65]">You have unsaved changes.</p>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#4A453E]/35">
            {status === 'saving'
              ? 'Saving'
              : status === 'loading'
                ? 'Loading'
                : isDirty
                  ? 'Dirty'
                  : 'Saved'}
          </span>
          <button
            onClick={handleCancel}
            disabled={cancelDisabled}
            className="px-6 py-3 bg-white text-[#4A453E]/40 font-bold text-sm rounded-full border border-[#4A453E]/10 hover:bg-[#F7F3E9] transition-all disabled:cursor-not-allowed disabled:opacity-60"
          >
            Cancel
          </button>
          <button
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
                <span>Saving...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-sm font-bold">check</span>
                <span>{profile.id ? 'Save changes' : 'Create Profile'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      <fieldset disabled={isBusy} className="contents">
        <div className={`transition-opacity ${isBusy ? 'opacity-80' : 'opacity-100'}`}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
            <div className="space-y-8">
              <section className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
                <div className="flex items-center gap-3 mb-8">
                  <div className="size-10 rounded-2xl bg-[#FF8A65]/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#FF8A65]">person</span>
                  </div>
                  <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">Body metrics</h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
                  <Field label="Age">
                    <input type="number" value={profile.age} onChange={(event) => updateField('age', event.target.value)} placeholder="Years" className={INPUT_CLASSNAME} />
                  </Field>
                  <Field label="Height (cm)">
                    <input type="number" value={profile.height} onChange={(event) => updateField('height', event.target.value)} placeholder="Centimeters" className={INPUT_CLASSNAME} />
                  </Field>
                  <Field label="Weight (kg)">
                    <input type="number" value={profile.weight} onChange={(event) => updateField('weight', event.target.value)} placeholder="Kilograms" className={INPUT_CLASSNAME} />
                  </Field>
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-2">
                    Sex
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
                  <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">Lifestyle and training</h3>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">
                      Activity level
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

                  <Field label="Exercise type">
                    <input type="text" value={profile.exerciseType} onChange={(event) => updateField('exerciseType', event.target.value)} placeholder="Strength, running, yoga..." className={INPUT_CLASSNAME} />
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
                  <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">Goals and pace</h3>
                </div>

                <div className="space-y-8">
                  <div>
                    <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">
                      Primary goal
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

                  <div>
                    <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">
                      Pace
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

                  <Field label="Daily calorie">
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
                          BMR: {rec.bmr} · TDEE: {rec.tdee} kcal · Recommended: {rec.recommendedKcal} kcal
                        </p>
                      ) : null;
                    })()}
                  </Field>
                </div>
              </section>

              <section className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
                <div className="flex items-center gap-3 mb-8">
                  <div className="size-10 rounded-2xl bg-[#81C784]/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#81C784]">restaurant</span>
                  </div>
                  <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">Eating preferences</h3>
                </div>

                <div className="space-y-8">
                  <div>
                    <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">
                      Diet style
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
                      Allergies and avoidances
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
        </div>
      </fieldset>

      <div className="bg-[#F7F3E9]/40 border border-[#4A453E]/05 rounded-[32px] p-8 text-center max-w-3xl mx-auto mb-20">
        <h5 className="text-[11px] font-bold text-[#4A453E]/60 uppercase tracking-widest mb-3 flex items-center justify-center gap-2">
          <span className="material-symbols-outlined text-base">info</span>
          Note
        </h5>
        <p className="text-xs text-[#4A453E]/50 leading-relaxed font-medium">
          Profile is used to personalize Assistant replies and add context around the entries you
          save to Food Log. It does not replace medical advice, diagnosis, or treatment.
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
      profile.exerciseType &&
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

  return 'Failed to save profile. Please try again.';
}

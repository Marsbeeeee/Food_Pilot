import { UserProfile, UserProfileForm, UserProfileInput } from '../types/types';

const PROFILE_ENDPOINT = 'http://localhost:8000/profile';
const PROFILE_STORAGE_KEY = 'foodpilot.profileId';

export class ProfileApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'ProfileApiError';
    this.status = status;
  }
}

export async function loadStoredProfile(): Promise<UserProfile | null> {
  const profileId = getStoredProfileId();
  if (profileId === null) {
    return null;
  }

  try {
    return await getProfile(profileId);
  } catch (error) {
    if (error instanceof ProfileApiError && error.status === 404) {
      clearStoredProfileId();
      return null;
    }
    throw error;
  }
}

export async function saveProfile(form: UserProfileForm): Promise<UserProfile> {
  const profileId = form.id ?? getStoredProfileId();
  const method = profileId ? 'PUT' : 'POST';
  const endpoint = profileId ? `${PROFILE_ENDPOINT}/${profileId}` : PROFILE_ENDPOINT;
  const payload = toProfileInput(form);

  const response = await fetch(endpoint, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await parseJson(response);
  if (!response.ok) {
    throw new ProfileApiError(getErrorMessage(data, response.status), response.status);
  }

  const savedProfile = data as UserProfile;
  setStoredProfileId(savedProfile.id);
  return savedProfile;
}

export function toProfileForm(profile: UserProfile): UserProfileForm {
  return {
    id: profile.id,
    age: String(profile.age),
    height: String(profile.height),
    weight: String(profile.weight),
    sex: profile.sex,
    activityLevel: profile.activityLevel,
    exerciseType: profile.exerciseType,
    goal: profile.goal,
    pace: profile.pace,
    kcalTarget: String(profile.kcalTarget),
    dietStyle: profile.dietStyle,
    allergies: profile.allergies,
  };
}

function getStoredProfileId(): number | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const rawValue = window.localStorage.getItem(PROFILE_STORAGE_KEY);
  if (!rawValue) {
    return null;
  }

  const profileId = Number(rawValue);
  if (!Number.isInteger(profileId) || profileId <= 0) {
    window.localStorage.removeItem(PROFILE_STORAGE_KEY);
    return null;
  }

  return profileId;
}

function setStoredProfileId(profileId: number): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(PROFILE_STORAGE_KEY, String(profileId));
}

function clearStoredProfileId(): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.removeItem(PROFILE_STORAGE_KEY);
}

async function getProfile(profileId: number): Promise<UserProfile> {
  const response = await fetch(`${PROFILE_ENDPOINT}/${profileId}`);
  const data = await parseJson(response);

  if (!response.ok) {
    throw new ProfileApiError(getErrorMessage(data, response.status), response.status);
  }

  return data as UserProfile;
}

async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function getErrorMessage(payload: unknown, status: number): string {
  if (payload && typeof payload === 'object') {
    if ('detail' in payload && typeof payload.detail === 'string') {
      return payload.detail;
    }

    if ('error' in payload && payload.error && typeof payload.error === 'object') {
      const errorPayload = payload.error as { message?: unknown };
      if (typeof errorPayload.message === 'string') {
        return errorPayload.message;
      }
    }
  }

  if (status === 404) {
    return '未找到画像记录。';
  }

  if (status === 422) {
    return '画像字段不合法，请检查输入内容。';
  }

  return '画像服务暂时不可用，请稍后重试。';
}

function toProfileInput(form: UserProfileForm): UserProfileInput {
  return {
    age: parseRequiredNumber(form.age, '年龄', true),
    height: parseRequiredNumber(form.height, '身高'),
    weight: parseRequiredNumber(form.weight, '体重'),
    sex: form.sex.trim(),
    activityLevel: form.activityLevel.trim(),
    exerciseType: form.exerciseType.trim(),
    goal: form.goal.trim(),
    pace: form.pace.trim(),
    kcalTarget: parseRequiredNumber(form.kcalTarget, '热量目标', true),
    dietStyle: form.dietStyle.trim(),
    allergies: form.allergies.map((item) => item.trim()).filter(Boolean),
  };
}

function parseRequiredNumber(value: string, label: string, integer = false): number {
  const normalized = value.trim();
  if (!normalized) {
    throw new ProfileApiError(`请填写${label}。`);
  }

  const parsed = integer ? Number.parseInt(normalized, 10) : Number.parseFloat(normalized);
  if (!Number.isFinite(parsed)) {
    throw new ProfileApiError(`${label}格式不正确。`);
  }

  return parsed;
}

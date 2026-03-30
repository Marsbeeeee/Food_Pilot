import { getStoredToken } from './auth';
import { UserProfile, UserProfileForm, UserProfileInput } from '../types/types';
import { API_BASE_URL } from '../config/api';

const PROFILE_ENDPOINT = `${API_BASE_URL}/profile`;
const MY_PROFILE_ENDPOINT = `${PROFILE_ENDPOINT}/me`;
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
  const token = requireAuthToken();
  const profileId = getStoredProfileId();
  if (profileId !== null) {
    try {
      return await getProfile(profileId, token);
    } catch (error) {
      if (error instanceof ProfileApiError && error.status === 404) {
        clearStoredProfileId();
      } else {
        throw error;
      }
    }
  }

  try {
    const profile = await getMyProfile(token);
    setStoredProfileId(profile.id);
    return profile;
  } catch (error) {
    if (error instanceof ProfileApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function clearStoredProfile(): void {
  clearStoredProfileId();
}

export async function saveProfile(form: UserProfileForm): Promise<UserProfile> {
  const token = requireAuthToken();
  const profileId = form.id ?? getStoredProfileId();
  const method = profileId ? 'PUT' : 'POST';
  const endpoint = profileId ? `${PROFILE_ENDPOINT}/${profileId}` : PROFILE_ENDPOINT;
  const payload = toProfileInput(form);

  const response = await fetch(endpoint, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
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
    height: normalizeNumericText(String(profile.height)),
    weight: normalizeNumericText(String(profile.weight)),
    sex: profile.sex,
    activityLevel: profile.activityLevel,
    exerciseType: profile.exerciseType,
    goal: profile.goal,
    pace: profile.pace,
    kcalTarget: String(profile.kcalTarget),
    dietStyle: profile.dietStyle,
    allergies: [...profile.allergies],
  };
}

export function normalizeProfileForm(form: UserProfileForm): UserProfileForm {
  return {
    id: form.id,
    age: normalizeNumericText(form.age),
    height: normalizeNumericText(form.height),
    weight: normalizeNumericText(form.weight),
    sex: form.sex.trim(),
    activityLevel: form.activityLevel.trim(),
    exerciseType: form.exerciseType
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
      .join(', '),
    goal: form.goal.trim(),
    pace: form.pace.trim(),
    kcalTarget: normalizeNumericText(form.kcalTarget),
    dietStyle: form.dietStyle.trim(),
    allergies: uniqueStrings(form.allergies),
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

async function getProfile(profileId: number, token: string): Promise<UserProfile> {
  const response = await fetch(`${PROFILE_ENDPOINT}/${profileId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await parseJson(response);

  if (!response.ok) {
    throw new ProfileApiError(getErrorMessage(data, response.status), response.status);
  }

  return data as UserProfile;
}

async function getMyProfile(token: string): Promise<UserProfile> {
  const response = await fetch(MY_PROFILE_ENDPOINT, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
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
    return '未找到个人档案。';
  }

  if (status === 422) {
    return '档案字段不合法，请检查输入。';
  }

  if (status === 401) {
    return '登录状态已失效，请重新登录。';
  }

  if (status === 409) {
    return '该账号已存在个人档案。';
  }

  return '档案服务暂时不可用，请稍后重试。';
}

function toProfileInput(form: UserProfileForm): UserProfileInput {
  const normalized = normalizeProfileForm(form);

  return {
    age: parseRequiredNumber(normalized.age, '年龄', true),
    height: parseRequiredNumber(normalized.height, '身高'),
    weight: parseRequiredNumber(normalized.weight, '体重'),
    sex: requireText(normalized.sex, '性别'),
    activityLevel: requireText(normalized.activityLevel, '活动水平'),
    exerciseType: normalized.exerciseType.trim(),
    goal: requireText(normalized.goal, '目标'),
    pace: requireText(normalized.pace, '节奏'),
    kcalTarget: parseRequiredNumber(normalized.kcalTarget, '热量目标', true),
    dietStyle: requireText(normalized.dietStyle, '饮食风格'),
    allergies: normalized.allergies,
  };
}

function parseRequiredNumber(value: string, label: string, integer = false): number {
  const normalized = value.trim();
  if (!normalized) {
    throw new ProfileApiError(`${label}为必填项。`);
  }

  const parsed = integer ? Number.parseInt(normalized, 10) : Number.parseFloat(normalized);
  if (!Number.isFinite(parsed)) {
    throw new ProfileApiError(`${label}必须是有效数字。`);
  }

  return parsed;
}

function requireText(value: string, label: string): string {
  const normalized = value.trim();
  if (!normalized) {
    throw new ProfileApiError(`${label}为必填项。`);
  }
  return normalized;
}

function uniqueStrings(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const value of values) {
    const normalized = value.trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    result.push(normalized);
  }

  return result;
}

function normalizeNumericText(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return '';
  }

  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? String(parsed) : trimmed;
}

function requireAuthToken(): string {
  const token = getStoredToken();
  if (!token) {
    throw new ProfileApiError('登录状态已失效，请重新登录。', 401);
  }
  return token;
}

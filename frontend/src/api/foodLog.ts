import { clearSession, getStoredToken } from './auth';
import {
  FoodLogEntry,
  FoodLogFromEstimateInput,
  FoodLogFromEstimateResponse,
  FoodLogListParams,
  FoodLogPatchInput,
  FoodLogSaveInput,
} from '../types/types';
import { API_BASE_URL } from '../config/api';

const FOOD_LOG_BASE_URL = `${API_BASE_URL}/food-logs`;

export class FoodLogApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'FoodLogApiError';
    this.status = status;
  }
}

export async function listFoodLogs(params?: FoodLogListParams): Promise<FoodLogEntry[]> {
  const query = buildQueryString(params);
  return requestJson<FoodLogEntry[]>(query ? `?${query}` : '');
}

export async function getFoodLogEntry(entryId: string): Promise<FoodLogEntry> {
  return requestJson<FoodLogEntry>(`/${entryId}`);
}

export async function saveFoodLogEntry(payload: FoodLogSaveInput): Promise<FoodLogEntry> {
  return requestJson<FoodLogEntry>('', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateFoodLogEntry(
  entryId: string,
  payload: FoodLogPatchInput,
): Promise<FoodLogEntry> {
  return requestJson<FoodLogEntry>(`/${entryId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function saveFoodLogFromEstimate(
  payload: FoodLogFromEstimateInput,
): Promise<FoodLogFromEstimateResponse> {
  return requestJson<FoodLogFromEstimateResponse>('/from-estimate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function deleteFoodLogEntry(entryId: string): Promise<void> {
  await requestJson(`/${entryId}`, {
    method: 'DELETE',
  });
}

export async function restoreFoodLogEntry(entryId: string): Promise<FoodLogEntry> {
  return requestJson<FoodLogEntry>(`/${entryId}/restore`, {
    method: 'POST',
  });
}

async function requestJson<T = unknown>(endpoint: string, init?: RequestInit): Promise<T> {
  const token = requireAuthToken();
  const response = await fetch(`${FOOD_LOG_BASE_URL}${endpoint}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...init?.headers,
    },
  });

  if (response.status === 401) {
    clearSession();
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await parseJson(response);
  if (!response.ok) {
    throw new FoodLogApiError(getErrorMessage(data, response.status), response.status);
  }

  return data as T;
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
  if (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string') {
    return payload.detail;
  }

  if (status === 401) {
    return '登录状态已失效，请重新登录。';
  }

  if (status === 404) {
    return '未找到对应的 Food Log 记录。';
  }

  return 'Food Log 暂时不可用，请稍后重试。';
}

function requireAuthToken(): string {
  const token = getStoredToken();
  if (!token) {
    throw new FoodLogApiError('登录状态已失效，请重新登录。', 401);
  }
  return token;
}

function buildQueryString(params?: FoodLogListParams): string {
  if (!params) {
    return '';
  }

  const searchParams = new URLSearchParams();
  if (params.sessionId !== undefined && params.sessionId !== null && params.sessionId !== '') {
    searchParams.set('sessionId', String(params.sessionId));
  }
  if (params.limit !== undefined) {
    searchParams.set('limit', String(params.limit));
  }
  if (params.dateFrom) {
    searchParams.set('dateFrom', params.dateFrom);
  }
  if (params.dateTo) {
    searchParams.set('dateTo', params.dateTo);
  }
  const query = params.query ?? params.meal;
  if (query) {
    searchParams.set('query', query);
  }
  if (params.sort) {
    searchParams.set('sort', params.sort);
  }
  return searchParams.toString();
}

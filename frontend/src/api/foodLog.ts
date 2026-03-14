import { clearSession, getStoredToken } from './auth';
import { FoodLogEntry } from '../types/types';

const FOOD_LOG_BASE_URL = 'http://localhost:8000/food-logs';

export class FoodLogApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'FoodLogApiError';
    this.status = status;
  }
}

export async function listFoodLogEntries(): Promise<FoodLogEntry[]> {
  return requestJson<FoodLogEntry[]>('');
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
    return 'Please sign in again.';
  }

  return 'Food log is temporarily unavailable. Please try again later.';
}

function requireAuthToken(): string {
  const token = getStoredToken();
  if (!token) {
    throw new FoodLogApiError('Please sign in again.', 401);
  }
  return token;
}

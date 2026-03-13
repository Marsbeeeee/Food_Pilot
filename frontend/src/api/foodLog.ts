import { clearSession, getStoredToken } from './auth';
import { FoodLogEntry, IngredientResult } from '../types/types';

const FOOD_LOG_BASE_URL = 'http://localhost:8000/food-log';

interface FoodLogEntryResponse {
  id: number;
  sourceType: 'estimate_api' | 'chat_message';
  sessionId: number | null;
  messageId: number | null;
  title: string;
  confidence: string | null;
  description: string;
  items: IngredientResult[];
  total: string;
  suggestion: string | null;
  createdAt: string;
}

export class FoodLogApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'FoodLogApiError';
    this.status = status;
  }
}

export async function listFoodLogEntries(): Promise<FoodLogEntry[]> {
  const data = await requestJson<FoodLogEntryResponse[]>('');
  return data.map((entry) => mapFoodLogEntry(entry));
}

function mapFoodLogEntry(entry: FoodLogEntryResponse): FoodLogEntry {
  const createdAt = new Date(entry.createdAt);
  const timestamp = Number.isNaN(createdAt.getTime()) ? new Date() : createdAt;

  return {
    id: String(entry.id),
    name: entry.title,
    description: entry.description,
    calories: entry.total.replace(/\s*kcal/i, '').trim(),
    date: timestamp.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    time: timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    image: `https://picsum.photos/seed/foodpilot-log-${entry.id}/640/480`,
    breakdown: entry.items.map((item) => ({ ...item })),
    protein: '--',
    carbs: '--',
    fat: '--',
    sessionId: entry.sessionId !== null ? String(entry.sessionId) : undefined,
  };
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

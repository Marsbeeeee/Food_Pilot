import { ChatSession, FoodLogEntry } from '../types/types';

const SESSIONS_STORAGE_PREFIX = 'foodpilot.sessions';
const FOOD_LOG_STORAGE_PREFIX = 'foodpilot.foodLog';

interface StoredChatSession {
  id: string;
  title: string;
  messages: ChatSession['messages'];
  timestamp: string;
  icon: string;
}

export function loadUserSessions(userId: number): ChatSession[] {
  const rawValue = getStoredValue(SESSIONS_STORAGE_PREFIX, userId);
  if (!rawValue) {
    return [];
  }

  try {
    const parsed = JSON.parse(rawValue) as StoredChatSession[];
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.map((session) => ({
      ...session,
      timestamp: new Date(session.timestamp),
      messages: session.messages.map((message) => ({ ...message })),
    }));
  } catch {
    return [];
  }
}

export function saveUserSessions(userId: number, sessions: ChatSession[]): void {
  setStoredValue(
    SESSIONS_STORAGE_PREFIX,
    userId,
    JSON.stringify(
      sessions.map((session) => ({
        ...session,
        timestamp: session.timestamp.toISOString(),
        messages: session.messages.map((message) => ({ ...message })),
      })),
    ),
  );
}

export function loadUserFoodLog(userId: number): FoodLogEntry[] {
  const rawValue = getStoredValue(FOOD_LOG_STORAGE_PREFIX, userId);
  if (!rawValue) {
    return [];
  }

  try {
    const parsed = JSON.parse(rawValue) as FoodLogEntry[];
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.map((entry) => ({
      ...entry,
      breakdown: entry.breakdown.map((item) => ({ ...item })),
    }));
  } catch {
    return [];
  }
}

export function saveUserFoodLog(userId: number, foodLog: FoodLogEntry[]): void {
  setStoredValue(
    FOOD_LOG_STORAGE_PREFIX,
    userId,
    JSON.stringify(
      foodLog.map((entry) => ({
        ...entry,
        breakdown: entry.breakdown.map((item) => ({ ...item })),
      })),
    ),
  );
}

function getStoredValue(prefix: string, userId: number): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.localStorage.getItem(buildStorageKey(prefix, userId));
}

function setStoredValue(prefix: string, userId: number, value: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(buildStorageKey(prefix, userId), value);
}

function buildStorageKey(prefix: string, userId: number): string {
  return `${prefix}.${userId}`;
}

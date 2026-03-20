import { clearSession, getStoredToken } from './auth';
import {
  InsightsAnalyzeRequest,
  InsightsAnalyzeResponse,
  InsightsAnalyzeData,
  InsightsBasketItem,
  InsightsBasketResponse,
  InsightsHistoryResponse,
} from '../types/types';
import { API_BASE_URL } from '../config/api';

const INSIGHTS_BASE_URL = `${API_BASE_URL}/api/insights`;

export class InsightsApiError extends Error {
  status: number;
  retryable: boolean;

  constructor(message: string, status = 0, retryable = true) {
    super(message);
    this.name = 'InsightsApiError';
    this.status = status;
    this.retryable = retryable;
  }
}

export async function analyzeInsights(
  payload: InsightsAnalyzeRequest,
  signal?: AbortSignal,
): Promise<InsightsAnalyzeResponse> {
  const token = getStoredToken();
  if (!token) {
    throw new InsightsApiError('请先登录。', 401, false);
  }

  let response: Response;
  try {
    response = await fetch(`${INSIGHTS_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw err;
    }
    throw new InsightsApiError(
      '无法连接到分析服务，请检查网络后重试。',
      0,
      true,
    );
  }

  if (response.status === 401) {
    clearSession();
    throw new InsightsApiError('登录已过期，请重新登录。', 401, false);
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new InsightsApiError(
      `分析服务返回了无法解析的响应（HTTP ${response.status}）。`,
      response.status,
      true,
    );
  }

  if (!response.ok) {
    const message = extractErrorMessage(body) ?? `分析服务异常（HTTP ${response.status}），请稍后重试。`;
    throw new InsightsApiError(message, response.status, true);
  }

  const result = body as InsightsAnalyzeResponse;

  if (!result.success) {
    const errMsg = result.error?.message ?? '分析失败，请稍后重试。';
    const retryable = result.error?.retryable ?? true;
    throw new InsightsApiError(errMsg, response.status, retryable);
  }

  if (!result.data) {
    throw new InsightsApiError('分析服务返回了空数据，请稍后重试。', response.status, true);
  }

  return result;
}

export async function fetchInsightsHistory(): Promise<InsightsHistoryResponse> {
  const token = getStoredToken();
  if (!token) {
    return { items: [] };
  }

  let response: Response;
  try {
    response = await fetch(`${INSIGHTS_BASE_URL}/history`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  } catch {
    return { items: [] };
  }

  if (response.status === 401) {
    clearSession();
    return { items: [] };
  }

  if (!response.ok) {
    return { items: [] };
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return { items: [] };
  }

  return normalizeInsightsHistoryResponse(body);
}

export async function fetchInsightsBasket(): Promise<InsightsBasketResponse> {
  const token = getStoredToken();
  if (!token) {
    return { items: [] };
  }

  let response: Response;
  try {
    response = await fetch(`${INSIGHTS_BASE_URL}/basket`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  } catch {
    return { items: [] };
  }

  if (response.status === 401) {
    clearSession();
    return { items: [] };
  }

  if (!response.ok) {
    return { items: [] };
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return { items: [] };
  }

  const result = body as InsightsBasketResponse;
  if (!result || !Array.isArray(result.items)) {
    return { items: [] };
  }
  return result;
}

export async function syncInsightsBasket(items: InsightsBasketItem[]): Promise<boolean> {
  const token = getStoredToken();
  if (!token) {
    return false;
  }

  let response: Response;
  try {
    response = await fetch(`${INSIGHTS_BASE_URL}/basket`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ items }),
    });
  } catch {
    return false;
  }

  if (response.status === 401) {
    clearSession();
    return false;
  }

  return response.ok;
}

function extractErrorMessage(payload: unknown): string | null {
  if (payload && typeof payload === 'object') {
    if ('error' in payload) {
      const err = (payload as { error: unknown }).error;
      if (err && typeof err === 'object' && 'message' in err) {
        const msg = (err as { message: unknown }).message;
        if (typeof msg === 'string') return msg;
      }
    }
    if ('detail' in payload) {
      const detail = (payload as { detail: unknown }).detail;
      if (typeof detail === 'string') return detail;
    }
  }
  return null;
}

function normalizeInsightsHistoryResponse(payload: unknown): InsightsHistoryResponse {
  if (!payload || typeof payload !== 'object') {
    return { items: [] };
  }
  const rawItems = (payload as { items?: unknown }).items;
  if (!Array.isArray(rawItems)) {
    return { items: [] };
  }
  const items = rawItems
    .map((item) => normalizeInsightsHistoryItem(item))
    .filter((item): item is InsightsHistoryResponse['items'][number] => item != null);
  return { items };
}

function normalizeInsightsHistoryItem(
  payload: unknown,
): InsightsHistoryResponse['items'][number] | null {
  if (!payload || typeof payload !== 'object') {
    return null;
  }

  const record = payload as {
    cacheKey?: unknown;
    cache_key?: unknown;
    mode?: unknown;
    dateRange?: unknown;
    date_range?: unknown;
    data?: unknown;
  };
  const cacheKey = typeof record.cacheKey === 'string'
    ? record.cacheKey.trim()
    : typeof record.cache_key === 'string'
      ? record.cache_key.trim()
      : '';
  if (!record.data || typeof record.data !== 'object') {
    return null;
  }

  const rawDateRange = (
    record.dateRange && typeof record.dateRange === 'object'
      ? record.dateRange
      : record.date_range && typeof record.date_range === 'object'
        ? record.date_range
        : null
  ) as { start?: unknown; end?: unknown } | null;
  const dateRange = rawDateRange
    && typeof rawDateRange.start === 'string'
    && typeof rawDateRange.end === 'string'
    ? { start: rawDateRange.start, end: rawDateRange.end }
    : undefined;
  const mode = record.mode === 'day' || record.mode === 'week' ? record.mode : undefined;
  const fallbackCacheKey = mode && dateRange ? `${mode}_${dateRange.start}_${dateRange.end}` : '';
  const resolvedCacheKey = cacheKey || fallbackCacheKey;
  if (!resolvedCacheKey) {
    return null;
  }

  return {
    cacheKey: resolvedCacheKey,
    mode,
    dateRange,
    data: record.data as InsightsAnalyzeData,
  };
}

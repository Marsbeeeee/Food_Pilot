import { clearSession, getStoredToken } from './auth';
import { InsightsAnalyzeRequest, InsightsAnalyzeResponse } from '../types/types';

const INSIGHTS_BASE_URL = 'http://localhost:8000/api/insights';

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
    });
  } catch {
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

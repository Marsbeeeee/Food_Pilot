import { clearSession, getStoredToken } from './auth';
import { EstimateApiResponse, EstimateRequestInput } from '../types/types';

const ESTIMATE_BASE_URL = 'http://localhost:8000/estimate';

export class EstimateApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'EstimateApiError';
    this.status = status;
  }
}

export async function estimateMeal(payload: EstimateRequestInput): Promise<EstimateApiResponse> {
  return requestJson<EstimateApiResponse>('', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function requestJson<T = unknown>(endpoint: string, init?: RequestInit): Promise<T> {
  const token = requireAuthToken();
  const response = await fetch(`${ESTIMATE_BASE_URL}${endpoint}`, {
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
    throw new EstimateApiError(getErrorMessage(data, response.status), response.status);
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
  if (payload && typeof payload === 'object' && 'error' in payload) {
    const errorPayload = payload.error;
    if (errorPayload && typeof errorPayload === 'object' && 'message' in errorPayload) {
      const message = errorPayload.message;
      if (typeof message === 'string') {
        return message;
      }
    }
  }

  if (status === 401) {
    return 'Please sign in again.';
  }

  if (status === 422) {
    return 'Please check the estimate input and try again.';
  }

  return 'Estimate service is temporarily unavailable. Please try again later.';
}

function requireAuthToken(): string {
  const token = getStoredToken();
  if (!token) {
    throw new EstimateApiError('Please sign in again.', 401);
  }
  return token;
}

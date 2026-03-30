import { clearSession, getStoredToken } from './auth';
import { API_BASE_URL } from '../config/api';
import {
  AdminDishImageCandidateDetail,
  AdminDishImageGenerationJobListItem,
  AdminDishImageCandidateListItem,
  AdminDishImageCandidateListParams,
} from '../types/types';

const ADMIN_DISH_IMAGES_BASE_URL = `${API_BASE_URL}/admin/dish-images`;

export class AdminDishImagesApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'AdminDishImagesApiError';
    this.status = status;
  }
}

export async function listAdminDishImageCandidates(
  params?: AdminDishImageCandidateListParams,
): Promise<AdminDishImageCandidateListItem[]> {
  const query = buildQueryString(params);
  return requestJson<AdminDishImageCandidateListItem[]>(query ? `?${query}` : '');
}

export async function getAdminDishImageCandidate(
  dishImageId: number | string,
): Promise<AdminDishImageCandidateDetail> {
  return requestJson<AdminDishImageCandidateDetail>(`/${dishImageId}`);
}

export async function listAdminDishImageGenerationJobs(
  limit = 100,
): Promise<AdminDishImageGenerationJobListItem[]> {
  const query = new URLSearchParams({ limit: String(limit) });
  return requestJson<AdminDishImageGenerationJobListItem[]>(`/generation-jobs?${query.toString()}`);
}

export async function approveAdminDishImageCandidate(
  dishImageId: number | string,
  note?: string,
): Promise<AdminDishImageCandidateDetail> {
  return requestJson<AdminDishImageCandidateDetail>(`/${dishImageId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  });
}

export async function rejectAdminDishImageCandidate(
  dishImageId: number | string,
  note?: string,
): Promise<AdminDishImageCandidateDetail> {
  return requestJson<AdminDishImageCandidateDetail>(`/${dishImageId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  });
}

export async function regenerateAdminDishImageCandidate(
  dishImageId: number | string,
  note?: string,
): Promise<AdminDishImageCandidateDetail> {
  return requestJson<AdminDishImageCandidateDetail>(`/${dishImageId}/regenerate`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  });
}

export async function rejectAndRegenerateAdminDishImageCandidate(
  dishImageId: number | string,
  note?: string,
): Promise<AdminDishImageCandidateDetail> {
  return requestJson<AdminDishImageCandidateDetail>(`/${dishImageId}/reject-and-regenerate`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  });
}

async function requestJson<T = unknown>(endpoint: string, init?: RequestInit): Promise<T> {
  const token = requireAuthToken();
  const response = await fetch(`${ADMIN_DISH_IMAGES_BASE_URL}${endpoint}`, {
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
    throw new AdminDishImagesApiError(getErrorMessage(data, response.status), response.status);
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
  if (status === 403) {
    return 'Admin access required.';
  }
  if (status === 404) {
    return 'Dish image candidate not found.';
  }
  return 'Dish image review is temporarily unavailable.';
}

function requireAuthToken(): string {
  const token = getStoredToken();
  if (!token) {
    throw new AdminDishImagesApiError('Please sign in again.', 401);
  }
  return token;
}

function buildQueryString(params?: AdminDishImageCandidateListParams): string {
  if (!params) {
    return '';
  }

  const searchParams = new URLSearchParams();
  if (params.status) {
    searchParams.set('status', params.status);
  }
  if (params.query) {
    searchParams.set('query', params.query);
  }
  if (params.createdFrom) {
    searchParams.set('createdFrom', params.createdFrom);
  }
  if (params.createdTo) {
    searchParams.set('createdTo', params.createdTo);
  }
  if (params.limit !== undefined) {
    searchParams.set('limit', String(params.limit));
  }
  return searchParams.toString();
}

import { AuthSession, AuthUser } from '../types/types';

const AUTH_BASE_URL = 'http://localhost:8000/auth';
const AUTH_TOKEN_STORAGE_KEY = 'foodpilot.authToken';
const AUTH_USER_STORAGE_KEY = 'foodpilot.authUser';

export class AuthApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'AuthApiError';
    this.status = status;
  }
}

interface AuthRequest {
  email: string;
  password: string;
  displayName?: string;
}

export async function login(request: AuthRequest): Promise<AuthSession> {
  return submitAuthRequest('/login', {
    email: request.email.trim(),
    password: request.password,
  });
}

export async function register(request: AuthRequest): Promise<AuthSession> {
  return submitAuthRequest('/register', {
    email: request.email.trim(),
    password: request.password,
    displayName: request.displayName?.trim(),
  });
}

export async function restoreSession(): Promise<AuthSession | null> {
  const token = getStoredToken();
  if (!token) {
    return null;
  }

  try {
    const user = await fetchCurrentUser(token);
    const session = {
      accessToken: token,
      tokenType: 'bearer',
      user,
    };
    persistSession(session);
    return session;
  } catch (error) {
    if (error instanceof AuthApiError && error.status === 401) {
      clearSession();
      return null;
    }
    throw error;
  }
}

export function persistSession(session: AuthSession): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, session.accessToken);
  window.localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(session.user));
}

export function clearSession(): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_USER_STORAGE_KEY);
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const rawValue = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
  return rawValue && rawValue.trim() ? rawValue : null;
}

async function fetchCurrentUser(token: string): Promise<AuthUser> {
  const response = await fetch(`${AUTH_BASE_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await parseJson(response);

  if (!response.ok) {
    throw new AuthApiError(getErrorMessage(data, response.status), response.status);
  }

  return data as AuthUser;
}

async function submitAuthRequest(
  endpoint: string,
  payload: Record<string, string | undefined>,
): Promise<AuthSession> {
  const response = await fetch(`${AUTH_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  const data = await parseJson(response);

  if (!response.ok) {
    throw new AuthApiError(getErrorMessage(data, response.status), response.status);
  }

  const session = data as AuthSession;
  persistSession(session);
  return session;
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
    return 'Invalid email or password.';
  }

  if (status === 409) {
    return 'This email is already registered.';
  }

  if (status === 422) {
    return 'Please check your email, password, and display name.';
  }

  return 'Authentication is temporarily unavailable. Please try again later.';
}

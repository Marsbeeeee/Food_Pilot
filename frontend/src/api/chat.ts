import { clearSession, getStoredToken } from './auth';
import { ChatSession, FoodLogEntry, IngredientResult, Message } from '../types/types';

const CHAT_BASE_URL = 'http://localhost:8000/chat';

export class ChatApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'ChatApiError';
    this.status = status;
  }
}

interface ChatSessionSummaryResponse {
  id: number;
  title: string;
  createdAt: string;
  updatedAt: string;
  lastMessageAt: string;
}

interface ChatMessageResponse {
  id: number;
  sessionId: number;
  role: 'user' | 'assistant';
  messageType: 'text' | 'estimate_result';
  content: string | null;
  resultTitle: string | null;
  resultConfidence: string | null;
  resultDescription: string | null;
  resultItems: IngredientResult[] | null;
  resultTotal: string | null;
  createdAt: string;
}

interface ChatSessionDetailResponse extends ChatSessionSummaryResponse {
  messages: ChatMessageResponse[];
}

interface ChatMessageExchangeResponse {
  session: ChatSessionSummaryResponse;
  userMessage: ChatMessageResponse;
  assistantMessage: ChatMessageResponse;
}

export interface ChatExchange {
  session: ChatSession;
  userMessage: Message;
  assistantMessage: Message;
}

export async function listChatSessions(): Promise<ChatSession[]> {
  const data = await requestJson<ChatSessionSummaryResponse[]>('/sessions');
  return data.map((session) => mapSessionSummary(session));
}

export async function getChatSession(sessionId: string): Promise<ChatSession> {
  const data = await requestJson<ChatSessionDetailResponse>(`/sessions/${sessionId}`);
  return mapSessionDetail(data);
}

export async function createChatSession(): Promise<ChatSession> {
  const data = await requestJson<ChatSessionSummaryResponse>('/sessions', {
    method: 'POST',
  });
  return mapSessionSummary(data);
}

export async function renameChatSession(
  sessionId: string,
  title: string,
): Promise<ChatSession> {
  const data = await requestJson<ChatSessionSummaryResponse>(`/sessions/${sessionId}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  });
  return mapSessionSummary(data);
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await requestJson(`/sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

export async function createChatMessage(
  content: string,
  profileId?: number,
): Promise<ChatExchange> {
  const data = await requestJson<ChatMessageExchangeResponse>('/messages', {
    method: 'POST',
    body: JSON.stringify(buildMessagePayload(content, profileId)),
  });
  return mapChatExchange(data);
}

export async function sendChatMessage(
  sessionId: string,
  content: string,
  profileId?: number,
): Promise<ChatExchange> {
  const data = await requestJson<ChatMessageExchangeResponse>(`/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify(buildMessagePayload(content, profileId)),
  });
  return mapChatExchange(data);
}

export function mergeSessionIntoList(
  sessions: ChatSession[],
  incomingSession: ChatSession,
): ChatSession[] {
  const nextSessions = sessions.filter((session) => session.id !== incomingSession.id);
  return [incomingSession, ...nextSessions].sort(
    (left, right) => right.timestamp.getTime() - left.timestamp.getTime(),
  );
}

export function applyChatExchange(
  sessions: ChatSession[],
  exchange: ChatExchange,
): ChatSession[] {
  const existingSession = sessions.find((session) => session.id === exchange.session.id);
  const nextMessages = existingSession?.hasLoadedMessages
    ? [...existingSession.messages, exchange.userMessage, exchange.assistantMessage]
    : [exchange.userMessage, exchange.assistantMessage];

  return mergeSessionIntoList(sessions, {
    ...exchange.session,
    messages: nextMessages,
    hasLoadedMessages: true,
  });
}

export function buildFoodLogFromSessions(sessions: ChatSession[]): FoodLogEntry[] {
  const entries: FoodLogEntry[] = [];

  for (const session of sessions) {
    for (const message of session.messages) {
      if (!message.isResult || !message.title || !message.description || !message.items || !message.total) {
        continue;
      }

      const createdAt = message.createdAt ? new Date(message.createdAt) : session.timestamp;
      const timestamp = Number.isNaN(createdAt.getTime()) ? session.timestamp : createdAt;

      entries.push({
        id: message.id ?? `${session.id}-${message.createdAt ?? message.time}`,
        name: message.title,
        description: message.description,
        calories: message.total.replace(/\s*kcal/i, '').trim(),
        date: timestamp.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        time: timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        image: `https://picsum.photos/seed/foodpilot-${session.id}-${message.id ?? 'result'}/640/480`,
        breakdown: message.items.map((item) => ({ ...item })),
        protein: '--',
        carbs: '--',
        fat: '--',
        sessionId: session.id,
      });
    }
  }

  return entries.sort((left, right) => {
    const leftValue = new Date(`${left.date} ${left.time}`).getTime();
    const rightValue = new Date(`${right.date} ${right.time}`).getTime();
    return rightValue - leftValue;
  });
}

function mapSessionSummary(session: ChatSessionSummaryResponse): ChatSession {
  return {
    id: String(session.id),
    title: session.title,
    messages: [],
    timestamp: new Date(session.lastMessageAt),
    icon: 'chat_bubble',
    hasLoadedMessages: false,
  };
}

function mapSessionDetail(session: ChatSessionDetailResponse): ChatSession {
  return {
    id: String(session.id),
    title: session.title,
    messages: session.messages.map((message) => mapMessage(message)),
    timestamp: new Date(session.lastMessageAt),
    icon: 'chat_bubble',
    hasLoadedMessages: true,
  };
}

function mapChatExchange(exchange: ChatMessageExchangeResponse): ChatExchange {
  return {
    session: mapSessionSummary(exchange.session),
    userMessage: mapMessage(exchange.userMessage),
    assistantMessage: mapMessage(exchange.assistantMessage),
  };
}

function mapMessage(message: ChatMessageResponse): Message {
  const createdAt = message.createdAt;
  const createdDate = new Date(createdAt);

  return {
    id: String(message.id),
    role: message.role,
    content: message.content ?? undefined,
    time: Number.isNaN(createdDate.getTime())
      ? '--:--'
      : createdDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    createdAt,
    isResult: message.messageType === 'estimate_result',
    title: message.resultTitle ?? undefined,
    confidence: message.resultConfidence ?? undefined,
    description: message.resultDescription ?? undefined,
    items: message.resultItems ? message.resultItems.map((item) => ({ ...item })) : undefined,
    total: message.resultTotal ?? undefined,
  };
}

function buildMessagePayload(content: string, profileId?: number): Record<string, number | string> {
  return profileId ? { content, profileId } : { content };
}

async function requestJson<T = unknown>(
  endpoint: string,
  init?: RequestInit,
): Promise<T> {
  const token = requireAuthToken();
  const response = await fetch(`${CHAT_BASE_URL}${endpoint}`, {
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
    throw new ChatApiError(getErrorMessage(data, response.status), response.status);
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

  if (status === 401) {
    return 'Please sign in again.';
  }

  if (status === 404) {
    return 'Chat session not found.';
  }

  if (status === 422) {
    return 'Please check your message or session title.';
  }

  return 'Chat service is temporarily unavailable. Please try again later.';
}

function requireAuthToken(): string {
  const token = getStoredToken();
  if (!token) {
    throw new ChatApiError('Please sign in again.', 401);
  }
  return token;
}

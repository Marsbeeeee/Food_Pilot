import { clearSession, getStoredToken } from './auth';
import {
  ChatMessagePayload,
  ChatMessageType,
  ChatSession,
  IngredientResult,
  Message,
} from '../types/types';
import { API_BASE_URL } from './config';

const CHAT_BASE_URL = `${API_BASE_URL}/chat`;

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
  messageType: ChatMessageType | 'estimate_result';
  content: string | null;
  payload: ChatMessagePayload | null;
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
  const messageType = normalizeMessageType(message.messageType);
  const payload = normalizePayload(message, messageType);

  return {
    id: String(message.id),
    role: message.role,
    messageType,
    content: message.content ?? payload?.text ?? undefined,
    payload,
    time: Number.isNaN(createdDate.getTime())
      ? '--:--'
      : createdDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    createdAt,
    isResult: messageType === 'meal_estimate',
    title: payload?.title ?? message.resultTitle ?? undefined,
    confidence: payload?.confidence ?? message.resultConfidence ?? undefined,
    description: payload?.description ?? message.resultDescription ?? undefined,
    items: payload?.items ? payload.items.map((item) => ({ ...item })) : undefined,
    total: payload?.total ?? message.resultTotal ?? undefined,
  };
}

function normalizeMessageType(messageType: ChatMessageResponse['messageType']): ChatMessageType {
  if (messageType === 'estimate_result') {
    return 'meal_estimate';
  }

  return messageType;
}

function normalizePayload(
  message: ChatMessageResponse,
  messageType: ChatMessageType,
): ChatMessagePayload | null {
  const payload: ChatMessagePayload = {};

  if (message.payload?.text) {
    payload.text = message.payload.text;
  } else if (messageType === 'text' && message.content) {
    payload.text = message.content;
  }

  if (message.payload?.title) {
    payload.title = message.payload.title;
  } else if (message.resultTitle) {
    payload.title = message.resultTitle;
  }

  if (message.payload?.confidence) {
    payload.confidence = message.payload.confidence;
  } else if (message.resultConfidence) {
    payload.confidence = message.resultConfidence;
  }

  if (message.payload?.description) {
    payload.description = message.payload.description;
  } else if (message.resultDescription) {
    payload.description = message.resultDescription;
  }

  if (message.payload?.items?.length) {
    payload.items = message.payload.items.map((item) => ({ ...item }));
  } else if (message.resultItems?.length) {
    payload.items = message.resultItems.map((item) => ({ ...item }));
  }

  if (message.payload?.total) {
    payload.total = message.payload.total;
  } else if (message.resultTotal) {
    payload.total = message.resultTotal;
  }

  return Object.keys(payload).length > 0 ? payload : null;
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
    return '登录状态已失效，请重新登录。';
  }

  if (status === 404) {
    return '未找到对应的聊天会话。';
  }

  if (status === 422) {
    return '请检查消息内容或会话标题。';
  }

  return '聊天服务暂时不可用，请稍后重试。';
}

function requireAuthToken(): string {
  const token = getStoredToken();
  if (!token) {
    throw new ChatApiError('登录状态已失效，请重新登录。', 401);
  }
  return token;
}


export enum AppView {
  WORKSPACE = 'WORKSPACE',
  EXPLORER = 'EXPLORER',
  INSIGHTS = 'INSIGHTS',
  PROFILE = 'PROFILE',
}

export type AuthScreenMode = 'login' | 'register';

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

export interface AuthUser {
  id: number;
  email: string;
  displayName: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthSession {
  accessToken: string;
  tokenType: string;
  user: AuthUser;
}

export interface IngredientResult {
  name: string;
  portion: string;
  energy: string;
}

export interface EstimateResult {
  title: string;
  description: string;
  confidence: string;
  items: IngredientResult[];
  total_calories: string;
  suggestion: string;
}

export type EstimateSaveStatus = 'saved' | 'not_saved';

export interface ApiErrorField {
  field: string;
  message: string;
}

export interface ApiError {
  code: string;
  message: string;
  fields?: ApiErrorField[];
  retryable: boolean;
}

export interface EstimateApiResponse {
  success: boolean;
  data: EstimateResult | null;
  error: ApiError | null;
  clientRequestId: string | null;
  foodLogId: string | null;
  saveStatus: EstimateSaveStatus;
}

export interface EstimateRequestInput {
  query: string;
  clientRequestId: string;
  profileId?: number;
  sessionId?: number;
}

export interface UserProfile {
  id: number;
  age: number;
  height: number;
  weight: number;
  sex: string;
  activityLevel: string;
  exerciseType: string;
  goal: string;
  pace: string;
  kcalTarget: number;
  dietStyle: string;
  allergies: string[];
}

export type UserProfileInput = Omit<UserProfile, 'id'>;

export interface UserProfileForm {
  id?: number;
  age: string;
  height: string;
  weight: string;
  sex: string;
  activityLevel: string;
  exerciseType: string;
  goal: string;
  pace: string;
  kcalTarget: string;
  dietStyle: string;
  allergies: string[];
}

export type ChatMessageType = 'text' | 'meal_estimate' | 'meal_recommendation';

export interface ChatMessagePayload {
  text?: string;
  title?: string;
  confidence?: string;
  description?: string;
  items?: IngredientResult[];
  total?: string;
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant';
  messageType: ChatMessageType;
  content?: string;
  payload?: ChatMessagePayload | null;
  time: string;
  createdAt?: string;
  isResult?: boolean;
  title?: string;
  confidence?: string;
  description?: string;
  items?: IngredientResult[];
  total?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  timestamp: Date;
  icon: string;
  hasLoadedMessages?: boolean;
}

export interface FoodLogEntry {
  id: string;
  name: string;
  description: string;
  calories: string;
  date: string;
  time: string;
  savedAt: string;
  mealOccurredAt: string;
  status: 'active' | 'deleted';
  sourceType: 'estimate_api' | 'chat_message' | 'manual';
  isManual: boolean;
  idempotencyKey?: string;
  breakdown: IngredientResult[];
  image?: string;
  protein?: string;
  carbs?: string;
  fat?: string;
  sessionId?: string;
  sourceMessageId?: string;
}

export interface FoodLogListParams {
  sessionId?: string | number;
  limit?: number;
  dateFrom?: string;
  dateTo?: string;
  meal?: string;
}

export interface FoodLogSaveInput {
  foodLogId?: string | number;
  sourceType: 'estimate_api' | 'chat_message' | 'manual';
  mealDescription: string;
  resultTitle: string;
  resultConfidence?: string;
  resultDescription: string;
  totalCalories: string;
  ingredients: IngredientResult[];
  sessionId?: string | number;
  sourceMessageId?: string | number;
  assistantSuggestion?: string;
  mealOccurredAt?: string;
  status?: 'active' | 'deleted';
  idempotencyKey?: string;
  isManual?: boolean;
}

export interface FoodLogFromEstimateInput {
  mealDescription: string;
  estimate: EstimateResult;
  clientRequestId: string;
  mealOccurredAt?: string;
}

export interface FoodLogFromEstimateResponse {
  clientRequestId: string;
  foodLogId: string;
  saveStatus: 'saved';
  foodLog: FoodLogEntry;
}

export interface FoodLogPatchInput {
  mealDescription?: string;
  resultTitle?: string;
  resultConfidence?: string;
  resultDescription?: string;
  totalCalories?: string;
  ingredients?: IngredientResult[];
  assistantSuggestion?: string;
  mealOccurredAt?: string;
}

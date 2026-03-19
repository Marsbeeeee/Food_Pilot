
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
  protein?: string;
  carbs?: string;
  fat?: string;
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

export interface EstimateBlock {
  title: string;
  confidence?: string;
  description?: string;
  items: IngredientResult[];
  total: string;
}

export interface ChatMessagePayload {
  text?: string;
  title?: string;
  confidence?: string;
  description?: string;
  items?: IngredientResult[];
  total?: string;
  /** When multiple foods: each food as a separate estimate block */
  estimates?: EstimateBlock[];
  suggestion?: string;
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
  /** When multiple foods: each food as a separate estimate block */
  estimates?: EstimateBlock[];
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
  imageSource?: string;
  imageLicense?: string;
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
  image?: string;
  imageSource?: string;
  imageLicense?: string;
}

export interface FoodLogFromEstimateInput {
  mealDescription: string;
  estimate: EstimateResult;
  clientRequestId: string;
  mealOccurredAt?: string;
  image?: string;
  imageSource?: string;
  imageLicense?: string;
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
  image?: string;
  imageSource?: string;
  imageLicense?: string;
}

export interface InsightsDateRange {
  start: string;
  end: string;
}

export interface InsightsAnalyzeRequest {
  mode: 'day' | 'week';
  selectedLogIds?: number[];
  dateRange: InsightsDateRange;
  cacheKey?: string;
}

export interface InsightsHistoryItem {
  cacheKey: string;
  data: InsightsAnalyzeData;
}

export interface InsightsHistoryResponse {
  items: InsightsHistoryItem[];
}

export interface NutritionAggregation {
  totalCalories: number;
  totalProtein: number;
  totalCarbs: number;
  totalFat: number;
  proteinRatio: number;
  carbsRatio: number;
  fatRatio: number;
  entryCount: number;
}

export interface InsightsEntryBrief {
  id: string;
  name: string;
  calories: string;
  date: string;
  time: string;
}

export interface AIInsights {
  summary: string;
  risks: string[];
  actions: string[];
}

export interface InsightsAnalyzeData {
  aggregation: NutritionAggregation;
  entries: InsightsEntryBrief[];
  ai: AIInsights;
}

export interface InsightsError {
  code: string;
  message: string;
  retryable: boolean;
}

export interface InsightsAnalyzeResponse {
  success: boolean;
  data: InsightsAnalyzeData | null;
  error: InsightsError | null;
}

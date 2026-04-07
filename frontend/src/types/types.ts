
export enum AppView {
  WORKSPACE = 'WORKSPACE',
  EXPLORER = 'EXPLORER',
  INSIGHTS = 'INSIGHTS',
  PROFILE = 'PROFILE',
  ADMIN_DISH_IMAGES = 'ADMIN_DISH_IMAGES',
}

export type AuthScreenMode = 'login' | 'register';

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

export interface AuthUser {
  id: number;
  email: string;
  displayName: string;
  isAdmin: boolean;
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

export interface DecisionCardNormalizedProduct {
  categoryId?: string;
  categoryName?: string;
  brandId?: string;
  brandName?: string;
  productId?: string;
  productName: string;
  normalizedName?: string;
  productScope: string;
  itemRole: string;
  sizeOrSpec?: string;
  addons?: string[];
  sugarLevel?: string;
  milkBase?: string;
  temperature?: string;
  quantity?: string;
  comboItems?: DecisionCardProductComponent[];
  missingFields?: string[];
  matchLevel?: string;
}

export interface DecisionCardProductComponent {
  productName: string;
  normalizedName?: string;
  categoryName?: string;
  brandName?: string;
  itemRole: string;
  quantity?: string;
}

export interface DecisionCardNutritionEstimate {
  items: IngredientResult[];
  totalCalories: string;
}

export interface DecisionCardEstimationMeta {
  sourceType: 'brand_template' | 'category_template' | 'generic_template';
  sourceLabel: string;
  templateId: string;
  hitLevel: 'brand' | 'category' | 'generic' | string;
  fallbackPath: Array<'brand_template' | 'category_template' | 'generic_template' | string>;
  confidenceReasons: string[];
  appliedRules: string[];
  missingConfiguration: string[];
}

export interface DecisionCard {
  inputSummary: string;
  normalizedProduct: DecisionCardNormalizedProduct;
  nutritionEstimate: DecisionCardNutritionEstimate;
  estimationMeta?: DecisionCardEstimationMeta | null;
  confidenceLevel: 'high' | 'medium' | 'low' | 'unknown';
  recommendationLevel: string;
  riskTags: string[];
  adaptationNote?: string;
  adjustments: string[];
  alternatives: string[];
  needsClarification: boolean;
  saveContainerKey: string;
  containerType: string;
  analysisEligible: boolean;
  saveEligible: boolean;
}

export interface EstimateResult {
  title: string;
  description: string;
  confidence: string;
  items: IngredientResult[];
  total_calories: string;
  suggestion: string;
  decisionCard?: DecisionCard;
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

export type WorkspaceInputMode = 'chat' | 'decision';

export interface ChatMessagePayload {
  text?: string;
  mode?: WorkspaceInputMode;
  title?: string;
  confidence?: string;
  description?: string;
  items?: IngredientResult[];
  total?: string;
  /** When multiple foods: each food as a separate estimate block */
  estimates?: EstimateBlock[];
  suggestion?: string;
  decisionCard?: DecisionCard;
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant';
  messageType: ChatMessageType;
  content?: string;
  payload?: ChatMessagePayload | null;
  decisionCard?: DecisionCard;
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

export interface WorkspaceTextPresentation {
  variant: 'text';
  content: string;
  decisionCard: DecisionCard | null;
}

export interface WorkspaceMealEstimatePresentation {
  variant: 'meal_estimate';
  title?: string;
  confidence?: string;
  description?: string;
  items: IngredientResult[];
  total?: string;
  estimates: EstimateBlock[] | null;
  suggestion: string | null;
  decisionCard: DecisionCard | null;
  normalizedProduct: DecisionCardNormalizedProduct | null;
  estimationMeta: DecisionCardEstimationMeta | null;
  summaryBadges: string[];
  templateHitLabel: string | null;
  templateSourceLabel: string | null;
  fallbackPathLabels: string[];
  confidenceReasons: string[];
  appliedRules: string[];
  needsClarification: false;
  analysisEligible: boolean | null;
  saveEligible: boolean | null;
  ingredientColumnLabel: string;
  portionColumnLabel: string;
  energyColumnLabel: string;
  proteinColumnLabel: string;
  carbsColumnLabel: string;
  fatColumnLabel: string;
  totalLabel: string;
}

export interface WorkspaceClarificationPresentation {
  variant: 'clarification';
  title: string;
  content: string;
  description: string | null;
  confidence: string;
  inputSummary: string;
  recommendationLevel: string;
  riskTags: string[];
  adjustments: string[];
  decisionCard: DecisionCard | null;
  normalizedProduct: DecisionCardNormalizedProduct | null;
  summaryBadges: string[];
  missingFields: string[];
  comboItems: string[];
  matchLevelLabel: string | null;
  needsClarification: true;
  analysisEligible: boolean | null;
  saveEligible: boolean | null;
  eyebrow: string;
  fallbackTitle: string;
  badgeLabel: string;
  riskLabel: string;
  actionLabel: string;
  missingFieldLabel: string;
  comboLabel: string;
}

export interface WorkspaceRecommendationPresentation {
  variant: 'meal_recommendation';
  title: string;
  description?: string;
  content?: string;
  decisionCard?: DecisionCard | null;
  eyebrow: string;
  fallbackTitle: string;
  badgeLabel: string;
  reasonLabel: string;
  contentLabel: string;
}

export type WorkspaceMessagePresentation =
  | WorkspaceTextPresentation
  | WorkspaceMealEstimatePresentation
  | WorkspaceClarificationPresentation
  | WorkspaceRecommendationPresentation;

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
  standardDishId?: string;
  standardDishName?: string;
  protein?: string;
  carbs?: string;
  fat?: string;
  sessionId?: string;
  sourceMessageId?: string;
  decisionCard?: DecisionCard;
}

export interface FoodLogListParams {
  sessionId?: string | number;
  limit?: number;
  dateFrom?: string;
  dateTo?: string;
  query?: string;
  sourceType?: 'estimate_api' | 'chat_message' | 'manual';
  hasImage?: boolean;
  sort?: 'created_desc' | 'created_asc';
  // Deprecated: kept for backward compatibility, mapped to `query`.
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
  decisionCard?: DecisionCard;
}

export interface FoodLogFromEstimateInput {
  mealDescription: string;
  estimate: EstimateResult;
  clientRequestId: string;
  mealOccurredAt?: string;
  image?: string;
  imageSource?: string;
  imageLicense?: string;
  decisionCard?: DecisionCard;
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

export interface InsightsBasketItem {
  basketId: string;
  analysisDate: string;
  snapshot: FoodLogEntry;
}

export interface InsightsBasketResponse {
  items: InsightsBasketItem[];
}

export interface InsightsHistoryItem {
  cacheKey: string;
  mode?: 'day' | 'week';
  dateRange?: InsightsDateRange;
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

export type AdminDishImageStatus = 'pending' | 'approved' | 'rejected';
export type AdminDishImageGenerationJobStatus = 'queued' | 'running';

export interface AdminDishImageActiveGenerationJob {
  id: number;
  status: AdminDishImageGenerationJobStatus;
  createdAt: string;
  startedAt?: string;
}

export interface AdminDishImageGenerationJobListItem {
  id: number;
  standardDishId: number;
  standardDishName: string;
  status: AdminDishImageGenerationJobStatus;
  createdAt: string;
  startedAt?: string;
}

export interface AdminDishImageCandidateListParams {
  status?: AdminDishImageStatus;
  query?: string;
  createdFrom?: string;
  createdTo?: string;
  limit?: number;
}

export interface AdminDishImageCandidateListItem {
  id: number;
  standardDishId: number;
  standardDishName: string;
  imageUrl: string;
  status: AdminDishImageStatus;
  promptVersion?: string;
  reviewNote?: string;
  createdAt: string;
  reviewedAt?: string;
  officialImageUrl?: string;
  officialImageStatus?: AdminDishImageStatus;
  isCurrentOfficial: boolean;
  activeGenerationJob?: AdminDishImageActiveGenerationJob;
}

export interface AdminDishImageOperation {
  id: number;
  dishImageId?: number;
  action: 'approve' | 'reject' | 'regenerate';
  resultStatus: string;
  note?: string;
  createdAt: string;
  actor: {
    id: number;
    displayName: string;
    email: string;
  };
}

export interface AdminDishImageCandidateDetail extends AdminDishImageCandidateListItem {
  officialImagePromptVersion?: string;
  officialImageUpdatedAt?: string;
  canApprove: boolean;
  canReject: boolean;
  canRegenerate: boolean;
  recentOperations: AdminDishImageOperation[];
}

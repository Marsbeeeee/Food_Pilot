
export enum AppView {
  WORKSPACE = 'WORKSPACE',
  EXPLORER = 'EXPLORER',
  PROFILE = 'PROFILE'
}

export interface IngredientResult {
  name: string;
  portion: string;
  energy: string;
}

export interface UserProfile {
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

export interface Message {
  role: 'user' | 'assistant';
  content?: string;
  time: string;
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
}

export interface FoodLogEntry {
  id: string;
  name: string;
  description: string;
  calories: string;
  date: string;
  time: string;
  image: string;
  breakdown: IngredientResult[];
  protein: string;
  carbs: string;
  fat: string;
}

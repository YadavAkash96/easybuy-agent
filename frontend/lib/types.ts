export interface ShoppingSpec {
  intent: string;
  budget: number;
  deadline_days: number;
  size: string;
  must_haves: string[];
  nice_to_haves: string[];
}

export interface ProductVariant {
  size: string;
  color?: string | null;
}

export interface Product {
  id: string;
  name: string;
  category: string;
  price: number;
  delivery_days: number;
  retailer: string;
  variants: ProductVariant[];
  tags: string[];
  url?: string;
  rating?: number;
  rating_count?: number;
  description?: string;
  image_url?: string | null;
}

export interface ScoreBreakdown {
  price_score: number;
  delivery_score: number;
  rating_score: number;
  match_score: number;
  return_score: number;
  penalty: number;
  reason: string;
}

export interface RankedProduct {
  product: Product;
  rank: number;
  score: number;
  score_breakdown: ScoreBreakdown;
  reasons: string[];
}

export interface CartItem {
  product: Product;
  quantity: number;
  selected_variant?: ProductVariant | null;
  missing_variant: boolean;
}

export interface Cart {
  items: CartItem[];
  total_cost: number;
}

export interface CheckoutStep {
  retailer: string;
  steps: string[];
}

export interface CheckoutPlan {
  retailer_steps: CheckoutStep[];
  summary: string;
}

export interface SuggestedArticle {
  name: string;
  category: string;
  selected: boolean;
}

export interface ExtractedConstraints {
  budget: number | null;
  deadline_days: number | null;
  size: string | null;
  preferences: string[];
  brand_preferences?: string[];
  budget_ranges?: Record<string, BudgetRange>;
}

export interface BudgetRange {
  min: number;
  max: number;
  enabled: boolean;
  current_min?: number | null;
  current_max?: number | null;
}

export interface BreakdownResponse {
  articles: SuggestedArticle[];
  constraints: ExtractedConstraints;
}

export interface TradeoffVariant {
  key: string;
  label: string;
  summary: string;
  constraints: ExtractedConstraints;
}

export interface TradeoffResponse {
  variants: TradeoffVariant[];
}

export interface ArticleSearchRequest {
  article: SuggestedArticle;
  constraints: ExtractedConstraints;
  intent: string;
  num_articles: number;
  tradeoff_key?: string | null;
  budget_range?: BudgetRange | null;
}

export interface ArticleSearchResponse {
  article: SuggestedArticle;
  ranked_products: RankedProduct[];
}

export interface ConfirmedItem {
  article: SuggestedArticle;
  product: Product;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface IntentChatResponse {
  reply: string;
  ready: boolean;
  intent_summary: string | null;
}

export type WizardStep = "intent" | "breakdown" | "search" | "cart" | "checkout";

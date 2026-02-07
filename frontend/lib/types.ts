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
}

export interface RankedProduct {
  product: Product;
  score: number;
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
}

export interface BreakdownResponse {
  articles: SuggestedArticle[];
  constraints: ExtractedConstraints;
}

export type WizardStep = "intent" | "breakdown";

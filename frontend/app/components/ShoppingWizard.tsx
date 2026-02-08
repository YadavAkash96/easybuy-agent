"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type {
  BreakdownResponse,
  ConfirmedItem,
  ExtractedConstraints,
  SuggestedArticle,
  TradeoffResponse,
  TradeoffVariant,
  WizardStep,
} from "@/lib/types";
import { postJSON } from "@/lib/api";
import StepIndicator from "./ui/StepIndicator";
import IntentStep from "./steps/IntentStep";
import BreakdownStep from "./steps/BreakdownStep";
import SearchStep from "./steps/SearchStep";

export default function ShoppingWizard() {
  const router = useRouter();
  const [step, setStep] = useState<WizardStep>("intent");
  const [intent, setIntent] = useState("");
  const [articles, setArticles] = useState<SuggestedArticle[]>([]);
  const [constraints, setConstraints] = useState<ExtractedConstraints>({
    budget: null,
    deadline_days: null,
    size: null,
    preferences: [],
    brand_preferences: [],
    budget_ranges: {},
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmedItems, setConfirmedItems] = useState<ConfirmedItem[]>([]);
  const [tradeoffs, setTradeoffs] = useState<TradeoffVariant[]>([]);
  const [selectedTradeoff, setSelectedTradeoff] = useState<string | null>(null);

  async function handleIntentSubmit(text: string) {
    setIntent(text);
    setLoading(true);
    setError(null);

    try {
      const data = await postJSON<BreakdownResponse>("/api/breakdown", {
        intent: text,
      });
      setArticles(data.articles);
      setConstraints(data.constraints);
      setStep("breakdown");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleBreakdownConfirm(
    confirmedArticles: SuggestedArticle[],
    confirmedConstraints: ExtractedConstraints
  ) {
    setArticles(confirmedArticles);
    setConstraints(confirmedConstraints);
    setLoading(true);
    setError(null);

    try {
      const tradeoffData = await postJSON<TradeoffResponse>("/api/tradeoffs", {
        intent,
        constraints: confirmedConstraints,
      });
      setTradeoffs(tradeoffData.variants);
      setSelectedTradeoff(tradeoffData.variants[0]?.key ?? null);
      setStep("search");
    } catch (e) {
      setError((e as Error).message);
      setTradeoffs([]);
      setSelectedTradeoff(null);
      setStep("search");
    } finally {
      setLoading(false);
    }
  }

  function handleSearchComplete(items: ConfirmedItem[]) {
    setConfirmedItems(items);
    setStep("cart");
  }

  function handleCheckout(items: ConfirmedItem[] = confirmedItems) {
    const today = new Date();
    const cartItems = items.map((item, index) => {
      const delivery = new Date(
        today.getTime() + (item.product.delivery_days || 0) * 24 * 60 * 60 * 1000,
      );

      return {
        id: item.product.id || `${item.article.name}-${index}`,
        name: item.product.name,
        price: item.product.price,
        retailer: item.product.retailer,
        deliveryDate: delivery.toISOString(),
        image: item.product.image_url || "https://placehold.co/200x200?text=Item",
        status: "pending" as const,
        url: item.product.url,
        rating: item.product.rating,
        ratingCount: item.product.rating_count,
      };
    });

    localStorage.setItem("agentic_cart", JSON.stringify(cartItems));
    router.push("/checkout");
  }

  return (
    <div className="min-h-screen bg-[var(--bg-100)] text-[var(--text-100)]">
      <div className="mx-auto max-w-4xl px-4 py-6">
        <div className="mb-8">
          <StepIndicator current={step} />
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {step === "intent" && (
          <IntentStep onSubmit={handleIntentSubmit} loading={loading} />
        )}

        {step === "breakdown" && (
          <BreakdownStep
            intent={intent}
            articles={articles}
            constraints={constraints}
            onBack={() => setStep("intent")}
            onConfirm={handleBreakdownConfirm}
          />
        )}

        {step === "search" && (
          <SearchStep
            articles={articles}
            constraints={constraints}
            intent={intent}
            onComplete={handleSearchComplete}
            onCheckout={handleCheckout}
            onBack={() => setStep("breakdown")}
            tradeoffs={tradeoffs}
            selectedTradeoff={selectedTradeoff}
            onSelectTradeoff={setSelectedTradeoff}
            onUpdateConstraints={setConstraints}
          />
        )}

        {step === "cart" && (
          <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-900/60">
              <svg className="h-8 w-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-slate-100">Search complete!</h2>
            <p className="text-sm text-slate-400">
              {confirmedItems.length} items selected — total ${confirmedItems.reduce((s, i) => s + i.product.price, 0).toFixed(2)}
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {confirmedItems.map((item, i) => (
                <span
                  key={i}
                  className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300"
                >
                  {item.article.name}: ${item.product.price.toFixed(2)} ({item.product.retailer})
                </span>
              ))}
            </div>
            <button
              onClick={() => handleCheckout()}
              className="rounded-xl bg-blue-600 px-6 py-2 text-sm font-semibold text-white"
            >
              Continue to unified checkout
            </button>
            <button
              onClick={() => setStep("search")}
              className="mt-2 rounded-xl border border-slate-700 px-6 py-2 text-sm text-slate-300 hover:text-slate-100"
            >
              &larr; Re-do search
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

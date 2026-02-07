"use client";

import { useState, useEffect, useCallback } from "react";
import type {
  SuggestedArticle,
  ExtractedConstraints,
  RankedProduct,
  ArticleSearchResponse,
  ConfirmedItem,
} from "@/lib/types";
import { postJSON } from "@/lib/api";

interface SearchStepProps {
  articles: SuggestedArticle[];
  constraints: ExtractedConstraints;
  intent: string;
  onComplete: (confirmedItems: ConfirmedItem[]) => void;
  onBack: () => void;
}

export default function SearchStep({
  articles,
  constraints,
  intent,
  onComplete,
  onBack,
}: SearchStepProps) {
  const selected = articles.filter((a) => a.selected);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [searchResults, setSearchResults] = useState<RankedProduct[]>([]);
  const [loading, setLoading] = useState(false);
  const [confirmedItems, setConfirmedItems] = useState<ConfirmedItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showRefinement, setShowRefinement] = useState(false);
  const [refinement, setRefinement] = useState("");

  const currentArticle = selected[currentIndex];

  const doSearch = useCallback(
    async (article: SuggestedArticle, extraInstructions?: string) => {
      setLoading(true);
      setError(null);
      setSearchResults([]);
      setShowRefinement(false);

      try {
        const searchIntent = extraInstructions
          ? `${intent} — ${extraInstructions}`
          : intent;
        const data = await postJSON<ArticleSearchResponse>("/api/search", {
          article,
          constraints,
          intent: searchIntent,
          num_articles: selected.length,
        });
        setSearchResults(data.ranked_products);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    },
    [intent, constraints, selected.length]
  );

  useEffect(() => {
    if (currentArticle) {
      doSearch(currentArticle);
    }
  }, [currentIndex, currentArticle, doSearch]);

  function handleSelect(ranked: RankedProduct) {
    const newItems = [
      ...confirmedItems,
      { article: currentArticle, product: ranked.product },
    ];
    setConfirmedItems(newItems);

    if (currentIndex + 1 < selected.length) {
      setCurrentIndex(currentIndex + 1);
    } else {
      onComplete(newItems);
    }
  }

  function handleReject() {
    setShowRefinement(true);
  }

  function handleRefineSearch() {
    if (refinement.trim()) {
      doSearch(currentArticle, refinement.trim());
      setRefinement("");
    }
  }

  const runningTotal = confirmedItems.reduce(
    (sum, item) => sum + item.product.price,
    0
  );

  return (
    <div className="space-y-6">
      {/* Progress bar */}
      <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3">
        <span className="text-sm text-slate-400">
          Article {currentIndex + 1} of {selected.length}
        </span>
        <span className="text-sm font-medium text-slate-200">
          {currentArticle?.name}
        </span>
        <div className="flex items-center gap-2">
          <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-blue-600 transition-all"
              style={{
                width: `${((currentIndex) / selected.length) * 100}%`,
              }}
            />
          </div>
          <span className="text-xs text-slate-500">
            {currentIndex}/{selected.length}
          </span>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
          {error}
          <button
            onClick={() => doSearch(currentArticle)}
            className="ml-3 underline hover:text-red-200"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center gap-3 py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          <p className="text-sm text-slate-400">
            Searching for {currentArticle?.name}...
          </p>
        </div>
      )}

      {/* Results */}
      {!loading && searchResults.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-100">
            Top results for {currentArticle?.name}
          </h3>

          <div className="grid gap-4">
            {searchResults.map((ranked) => (
              <div
                key={ranked.product.id}
                className="relative rounded-xl border border-slate-800 bg-slate-900/50 p-4 transition hover:border-slate-700"
              >
                {/* Rank badge */}
                <div className="absolute -left-2 -top-2 flex h-7 w-7 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
                  #{ranked.rank}
                </div>

                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-slate-100">
                        {ranked.product.name}
                      </h4>
                      {ranked.product.url && (
                        <a
                          href={ranked.product.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-400 hover:text-blue-300"
                        >
                          View
                        </a>
                      )}
                    </div>

                    {ranked.product.description && (
                      <p className="text-sm text-slate-400">
                        {ranked.product.description}
                      </p>
                    )}

                    <div className="flex flex-wrap gap-3 text-sm">
                      <span className="text-emerald-400 font-semibold">
                        ${ranked.product.price.toFixed(2)}
                      </span>
                      <span className="text-slate-400">
                        {ranked.product.retailer}
                      </span>
                      <span className="text-slate-400">
                        {ranked.product.delivery_days}d delivery
                      </span>
                      {ranked.product.rating ? (
                        <span className="text-yellow-400">
                          {"★".repeat(Math.round(ranked.product.rating))}{" "}
                          {ranked.product.rating.toFixed(1)}
                        </span>
                      ) : null}
                    </div>

                    {/* Score breakdown */}
                    <div className="flex flex-wrap gap-2 pt-1">
                      <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        Score: {(ranked.score * 100).toFixed(0)}%
                      </span>
                      <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        Price: {(ranked.score_breakdown.price_score * 100).toFixed(0)}%
                      </span>
                      <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        Delivery: {(ranked.score_breakdown.delivery_score * 100).toFixed(0)}%
                      </span>
                      <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        Rating: {(ranked.score_breakdown.rating_score * 100).toFixed(0)}%
                      </span>
                      <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        Match: {(ranked.score_breakdown.match_score * 100).toFixed(0)}%
                      </span>
                      {ranked.score_breakdown.reason && (
                        <span className="rounded-md bg-red-900/50 px-2 py-0.5 text-xs text-red-300">
                          {ranked.score_breakdown.reason}
                        </span>
                      )}
                    </div>

                    {ranked.reasons.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {ranked.reasons.map((r, i) => (
                          <span
                            key={i}
                            className="rounded-full bg-blue-900/40 px-2 py-0.5 text-xs text-blue-300"
                          >
                            {r}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleSelect(ranked)}
                    className="shrink-0 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
                  >
                    Select
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Reject all */}
          {!showRefinement && (
            <button
              onClick={handleReject}
              className="w-full rounded-xl border border-slate-700 py-2 text-sm text-slate-400 hover:text-slate-200"
            >
              None of these — refine search
            </button>
          )}

          {/* Refinement input */}
          {showRefinement && (
            <div className="flex gap-2">
              <input
                type="text"
                value={refinement}
                onChange={(e) => setRefinement(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRefineSearch()}
                placeholder="e.g. cheaper options, different brand..."
                className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-600 focus:outline-none"
              />
              <button
                onClick={handleRefineSearch}
                disabled={!refinement.trim()}
                className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-40"
              >
                Search again
              </button>
            </div>
          )}
        </div>
      )}

      {/* No results */}
      {!loading && !error && searchResults.length === 0 && !loading && (
        <div className="py-12 text-center text-sm text-slate-500">
          No products found. Try adjusting your requirements.
        </div>
      )}

      {/* Running cart footer */}
      {confirmedItems.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-slate-300">
              Cart ({confirmedItems.length} item{confirmedItems.length !== 1 ? "s" : ""})
            </span>
            <span className="text-sm font-semibold text-emerald-400">
              ${runningTotal.toFixed(2)}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {confirmedItems.map((item, i) => (
              <span
                key={i}
                className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300"
              >
                {item.article.name}: ${item.product.price.toFixed(2)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Back button */}
      <div className="flex justify-start">
        <button
          onClick={onBack}
          className="rounded-xl border border-slate-700 px-6 py-2 text-sm text-slate-300 hover:text-slate-100"
        >
          &larr; Back to selection
        </button>
      </div>
    </div>
  );
}

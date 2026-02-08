"use client";

import { useState } from "react";
import type { BudgetRange, ExtractedConstraints, SuggestedArticle } from "@/lib/types";
import ToggleCard from "../ui/ToggleCard";

interface BreakdownStepProps {
  intent: string;
  articles: SuggestedArticle[];
  constraints: ExtractedConstraints;
  onBack: () => void;
  onConfirm: (articles: SuggestedArticle[], constraints: ExtractedConstraints) => void;
}

export default function BreakdownStep({
  intent,
  articles: initialArticles,
  constraints: initialConstraints,
  onBack,
  onConfirm,
}: BreakdownStepProps) {
  const [articles, setArticles] = useState<SuggestedArticle[]>(initialArticles);
  const [constraints, setConstraints] = useState<ExtractedConstraints>(initialConstraints);
  const [newItem, setNewItem] = useState("");
  const [brandInput, setBrandInput] = useState(
    (initialConstraints.brand_preferences || []).join(", ")
  );

  function toggleArticle(index: number) {
    setArticles((prev) =>
      prev.map((a, i) => (i === index ? { ...a, selected: !a.selected } : a))
    );
  }

  function addArticle() {
    const name = newItem.trim();
    if (!name) return;
    setArticles((prev) => [
      ...prev,
      { name, category: name.toLowerCase().replace(/\s+/g, "-"), selected: true },
    ]);
    setNewItem("");
  }

  function updateBrandPreferences(value: string) {
    setBrandInput(value);
    const parsed = value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    setConstraints((prev) => ({
      ...prev,
      brand_preferences: parsed,
    }));
  }

  function updateBudgetRange(category: string, update: Partial<BudgetRange>) {
    setConstraints((prev) => {
      const fallback = getDefaultRange(category);
      const existing = prev.budget_ranges?.[category] ?? {
        min: fallback.min,
        max: fallback.max,
        enabled: false,
        current_min: fallback.min,
        current_max: fallback.max,
      };
      return {
        ...prev,
        budget_ranges: {
          ...(prev.budget_ranges || {}),
          [category]: {
            ...existing,
            ...update,
            min: existing.min || fallback.min,
            max: existing.max || fallback.max,
          },
        },
      };
    });
  }

  function getDefaultRange(category: string) {
    const key = category.toLowerCase();
    const defaults: Record<string, { min: number; max: number }> = {
      socks: { min: 0, max: 20 },
      pants: { min: 20, max: 90 },
      jacket: { min: 60, max: 250 },
      gloves: { min: 10, max: 60 },
      goggles: { min: 30, max: 140 },
      helmet: { min: 40, max: 200 },
      "base-layer": { min: 15, max: 80 },
      "base layer": { min: 15, max: 80 },
      boots: { min: 80, max: 300 },
    };
    return defaults[key] ?? { min: 10, max: 200 };
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-100">
          Here&apos;s what we think you need
        </h2>
        <blockquote className="mt-2 border-l-2 border-slate-700 pl-3 text-sm italic text-slate-400">
          &ldquo;{intent}&rdquo;
        </blockquote>
      </div>

      {/* Constraint badges */}
      <div className="flex flex-wrap gap-2">
        {constraints.budget != null && (
          <span className="rounded-full bg-emerald-900/60 px-3 py-1 text-sm font-medium text-emerald-300">
            ${constraints.budget}
          </span>
        )}
        {constraints.deadline_days != null && (
          <span className="rounded-full bg-sky-900/60 px-3 py-1 text-sm font-medium text-sky-300">
            {constraints.deadline_days} days
          </span>
        )}
        {constraints.size != null ? (
          <span className="rounded-full bg-purple-900/60 px-3 py-1 text-sm font-medium text-purple-300">
            Size {constraints.size}
          </span>
        ) : (
          <span className="rounded-full bg-amber-900/60 px-3 py-1 text-sm font-medium text-amber-300">
            Size not detected
          </span>
        )}
        {constraints.preferences.map((pref) => (
          <span
            key={pref}
            className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300"
          >
            {pref}
          </span>
        ))}
        {(constraints.brand_preferences || []).map((brand) => (
          <span
            key={brand}
            className="rounded-full bg-blue-900/50 px-3 py-1 text-sm text-blue-200"
          >
            {brand}
          </span>
        ))}
      </div>

      {/* Brand preferences */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <p className="text-sm font-semibold text-slate-100">Brand preferences (soft)</p>
        <p className="text-xs text-slate-400">
          Optional. Use commas to separate brands (e.g., Adidas, Puma).
        </p>
        <input
          value={brandInput}
          onChange={(e) => updateBrandPreferences(e.target.value)}
          placeholder="Adidas, Puma, The North Face"
          className="mt-3 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-600 focus:outline-none"
        />
      </div>

      {/* Article toggle grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {articles.map((article, i) => {
          const fallback = getDefaultRange(article.category);
          const range = constraints.budget_ranges?.[article.category] ?? {
            min: fallback.min,
            max: fallback.max,
            enabled: false,
            current_min: fallback.min,
            current_max: fallback.max,
          };
          const enabled = range.enabled;
          const currentMin = range.current_min ?? range.min ?? fallback.min;
          const currentMax = range.current_max ?? range.max ?? fallback.max;
          return (
            <div
              key={`${article.category}-${i}`}
              className="rounded-2xl border border-slate-800 bg-slate-950/40 p-3"
            >
            <ToggleCard
              name={article.name}
              category={article.category}
              active={article.selected}
              onToggle={() => toggleArticle(i)}
            />
            <div className="mt-3 rounded-xl border border-slate-800 bg-slate-900/40 p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-200">Item budget range</p>
                  <p className="text-[11px] text-slate-500">
                    Default off. When on, boosts items inside range.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    updateBudgetRange(article.category, {
                      enabled: !enabled,
                    })
                  }
                  className={`rounded-full px-3 py-1 text-xs ${
                    enabled ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-300"
                  }`}
                >
                  {enabled ? "On" : "Off"}
                </button>
              </div>
              <div
                className={`mt-3 overflow-hidden transition-all duration-200 ease-out ${
                  enabled ? "max-h-24 opacity-100" : "max-h-0 opacity-0"
                }`}
              >
                <div className="relative mt-2 h-10">
                  <div className="absolute left-0 right-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-slate-700/80" />
                  <input
                    type="range"
                    min={range.min}
                    max={range.max}
                    step={1}
                    value={currentMin}
                    onChange={(e) => {
                      const nextMin = Number(e.target.value);
                      updateBudgetRange(article.category, {
                        current_min: nextMin,
                        current_max: Math.max(nextMin, currentMax),
                      });
                    }}
                    className="range-dual absolute inset-0 w-full"
                    style={{ zIndex: currentMin >= currentMax - 2 ? 5 : 3 }}
                  />
                  <input
                    type="range"
                    min={range.min}
                    max={range.max}
                    step={1}
                    value={currentMax}
                    onChange={(e) => {
                      const nextMax = Number(e.target.value);
                      updateBudgetRange(article.category, {
                        current_min: Math.min(currentMin, nextMax),
                        current_max: nextMax,
                      });
                    }}
                    className="range-dual absolute inset-0 w-full"
                    style={{ zIndex: 4 }}
                  />
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-slate-400">
                  <span>${currentMin}</span>
                  <span>${currentMax}</span>
                </div>
              </div>
            </div>
          </div>
          );
        })}
      </div>

      {/* Add extra item */}
      <div className="flex gap-2">
        <input
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addArticle()}
          placeholder="Need anything else? Type and press Enter"
          className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-600 focus:outline-none"
        />
        <button
          onClick={addArticle}
          disabled={!newItem.trim()}
          className="rounded-xl bg-slate-800 px-4 py-2 text-sm text-slate-200 transition-colors hover:bg-slate-700 disabled:opacity-50"
        >
          Add
        </button>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={onBack}
          className="rounded-xl px-6 py-2 text-sm text-slate-400 transition-colors hover:text-slate-200"
        >
          &larr; Back
        </button>
        <button
          onClick={() => onConfirm(articles, constraints)}
          className="rounded-xl bg-blue-600 px-8 py-3 text-base font-semibold text-white transition-colors hover:bg-blue-500"
        >
          Continue &rarr;
        </button>
      </div>
    </div>
  );
}

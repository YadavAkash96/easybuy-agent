"use client";

import { useState } from "react";
import type { ExtractedConstraints, SuggestedArticle } from "@/lib/types";
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
      </div>

      {/* Article toggle grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {articles.map((article, i) => (
          <ToggleCard
            key={`${article.category}-${i}`}
            name={article.name}
            category={article.category}
            active={article.selected}
            onToggle={() => toggleArticle(i)}
          />
        ))}
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

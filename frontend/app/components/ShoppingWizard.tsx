"use client";

import { useState } from "react";
import type {
  BreakdownResponse,
  ExtractedConstraints,
  SuggestedArticle,
  WizardStep,
} from "@/lib/types";
import { postJSON } from "@/lib/api";
import StepIndicator from "./ui/StepIndicator";
import IntentStep from "./steps/IntentStep";
import BreakdownStep from "./steps/BreakdownStep";

export default function ShoppingWizard() {
  const [step, setStep] = useState<WizardStep>("intent");
  const [intent, setIntent] = useState("");
  const [articles, setArticles] = useState<SuggestedArticle[]>([]);
  const [constraints, setConstraints] = useState<ExtractedConstraints>({
    budget: null,
    deadline_days: null,
    size: null,
    preferences: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

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

  function handleBreakdownConfirm(
    confirmedArticles: SuggestedArticle[],
    confirmedConstraints: ExtractedConstraints
  ) {
    setArticles(confirmedArticles);
    setConstraints(confirmedConstraints);
    setConfirmed(true);
    // GOAL 2 will replace this with setStep("search")
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
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

        {step === "breakdown" && !confirmed && (
          <BreakdownStep
            intent={intent}
            articles={articles}
            constraints={constraints}
            onBack={() => setStep("intent")}
            onConfirm={handleBreakdownConfirm}
          />
        )}

        {step === "breakdown" && confirmed && (
          <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-900/60">
              <svg className="h-8 w-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-slate-100">Selection confirmed!</h2>
            <p className="text-sm text-slate-400">
              {articles.filter((a) => a.selected).length} items selected — search &amp; cart coming in GOAL 2
            </p>
            <button
              onClick={() => setConfirmed(false)}
              className="mt-2 rounded-xl border border-slate-700 px-6 py-2 text-sm text-slate-300 hover:text-slate-100"
            >
              &larr; Edit selection
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

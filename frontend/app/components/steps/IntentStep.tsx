"use client";

import { useState } from "react";

const DEFAULT_INTENT =
  "Downhill skiing outfit, warm and waterproof, size M, budget $400, delivery within 5 days.";

interface IntentStepProps {
  onSubmit: (intent: string) => void;
  loading: boolean;
}

export default function IntentStep({ onSubmit, loading }: IntentStepProps) {
  const [intent, setIntent] = useState(DEFAULT_INTENT);

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-4">
      <div className="w-full max-w-2xl space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-slate-100">
            What would you like to purchase today?
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Describe what you need — we&apos;ll break it down into the right pieces.
          </p>
        </div>

        <textarea
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          rows={4}
          autoFocus
          placeholder="e.g. Downhill skiing outfit, size M, budget $400, 5-day delivery"
          className="w-full resize-none rounded-xl border border-slate-700 bg-slate-900 p-4 text-base text-slate-100 placeholder:text-slate-500 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
        />

        <div className="flex justify-center">
          <button
            onClick={() => onSubmit(intent)}
            disabled={loading || !intent.trim()}
            className="flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-3 text-base font-semibold text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
          >
            {loading ? (
              <>
                <svg
                  className="h-5 w-5 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Analyzing...
              </>
            ) : (
              <>Break it down &rarr;</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

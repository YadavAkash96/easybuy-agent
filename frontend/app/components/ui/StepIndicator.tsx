"use client";

import type { WizardStep } from "@/lib/types";

const STEPS: { key: WizardStep | string; label: string }[] = [
  { key: "intent", label: "Intent" },
  { key: "breakdown", label: "Review" },
  { key: "search", label: "Search" },
  { key: "cart", label: "Cart" },
  { key: "checkout", label: "Checkout" },
];

export default function StepIndicator({ current }: { current: WizardStep }) {
  const currentIdx = STEPS.findIndex((s) => s.key === current);

  return (
    <div className="flex items-center justify-center gap-0">
      {STEPS.map((step, i) => (
        <div key={step.key} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold ${
                i <= currentIdx
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-slate-500"
              }`}
            >
              {i + 1}
            </div>
            <span
              className={`mt-1 text-xs ${
                i <= currentIdx ? "text-slate-200" : "text-slate-600"
              }`}
            >
              {step.label}
            </span>
          </div>
          {i < STEPS.length - 1 && (
            <div
              className={`mx-2 h-0.5 w-8 ${
                i < currentIdx ? "bg-blue-600" : "bg-slate-800"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

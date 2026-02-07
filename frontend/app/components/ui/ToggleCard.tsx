"use client";

interface ToggleCardProps {
  name: string;
  category: string;
  active: boolean;
  onToggle: () => void;
}

export default function ToggleCard({ name, category, active, onToggle }: ToggleCardProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`flex w-full items-center justify-between rounded-xl border p-4 text-left transition-all ${
        active
          ? "border-l-4 border-blue-600 bg-slate-900"
          : "border-slate-700 bg-slate-900/50 opacity-50"
      }`}
    >
      <div>
        <p className="text-sm font-semibold text-slate-100">{name}</p>
        <p className="text-xs text-slate-400">{category}</p>
      </div>
      <div
        className={`flex h-6 w-11 items-center rounded-full px-0.5 transition-colors ${
          active ? "bg-blue-600" : "bg-slate-700"
        }`}
      >
        <div
          className={`h-5 w-5 rounded-full bg-white shadow transition-transform ${
            active ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </div>
    </button>
  );
}

"use client";

import { useState, useRef, useEffect } from "react";
import type { ChatMessage, IntentChatResponse } from "@/lib/types";
import { postJSON } from "@/lib/api";

const GREETING: ChatMessage = {
  role: "assistant",
  content: "Hey, this is EasyBuy, your super smart shopping assistant! What do you want to shop?",
};

interface IntentStepProps {
  onSubmit: (intent: string) => void;
  loading: boolean;
}

export default function IntentStep({ onSubmit, loading }: IntentStepProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [ready, setReady] = useState(false);
  const [intentSummary, setIntentSummary] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  async function send() {
    const text = input.trim();
    if (!text || thinking || ready) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setThinking(true);

    try {
      const data = await postJSON<IntentChatResponse>("/api/intent-chat", {
        messages: updated.slice(1), // skip hardcoded greeting
      });

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.reply,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (data.ready && data.intent_summary) {
        setReady(true);
        setIntentSummary(data.intent_summary);
      }
    } catch {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: "Sorry, something went wrong. Could you try again?",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setThinking(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="flex min-h-[70vh] flex-col items-center px-4">
      <div className="flex w-full max-w-2xl flex-1 flex-col">
        {/* Chat messages */}
        <div className="flex-1 space-y-3 overflow-y-auto py-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-slate-800 text-slate-200"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {thinking && (
            <div className="flex justify-start">
              <div className="flex gap-1.5 rounded-2xl bg-slate-800 px-4 py-3">
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:0ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:150ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:300ms]" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Continue button when ready */}
        {ready && (
          <div className="mb-3 flex justify-center">
            <button
              onClick={() => onSubmit(intentSummary)}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <svg
                    className="h-4 w-4 animate-spin"
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
                  Breaking down...
                </>
              ) : (
                <>Continue to breakdown &rarr;</>
              )}
            </button>
          </div>
        )}

        {/* Input area */}
        <div className="border-t border-slate-800 pb-4 pt-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={ready || thinking}
              autoFocus
              placeholder={
                ready
                  ? "All set! Click Continue above."
                  : "Type a message..."
              }
              className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 disabled:opacity-50"
            />
            <button
              onClick={send}
              disabled={!input.trim() || thinking || ready}
              className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

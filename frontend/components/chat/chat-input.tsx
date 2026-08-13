"use client";

import React, { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  accessScope?: string;
}

export function ChatInput({ onSend, disabled, accessScope = "Public + Student" }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        160
      )}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-3 sm:p-4 bg-hit-surface border-t border-hit-border shadow-lg"
    >
      <div className="max-w-4xl mx-auto flex items-end gap-2 bg-hit-bg border border-hit-border rounded-xl px-3 py-2 focus-within:border-hit-amber focus-within:ring-1 focus-within:ring-hit-amber transition-all">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about registration, fees, exams, or your department's requirements…"
          disabled={disabled}
          className="flex-1 bg-transparent border-0 resize-none text-sm text-hit-text-primary placeholder:text-hit-text-secondary/70 focus:outline-none focus:ring-0 max-h-40 min-h-[36px] py-1"
        />

        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className={cn(
            "p-2 rounded-lg bg-hit-blue text-white transition-all cursor-pointer flex items-center justify-center shrink-0",
            !input.trim() || disabled
              ? "opacity-50 cursor-not-allowed"
              : "hover:bg-hit-blue-dark shadow-sm"
          )}
          title="Send query"
        >
          {/* Send Icon in Navy with Amber Accent */}
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M5 12H19M19 12L12 5M19 12L12 19"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle cx="19" cy="12" r="2" fill="#E8A33D" />
          </svg>
        </button>
      </div>
      <div className="max-w-4xl mx-auto mt-2 flex items-center justify-between font-mono text-[10px] text-hit-text-secondary px-1 gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span>Press Enter to send, Shift+Enter for new line</span>
        </div>
        
        {/* Transparency Feature Scope Indicator */}
        <div
          className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-hit-bg border border-hit-border text-hit-text-secondary"
          title="Active retrieval permissions for this session (transparency view)"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-hit-amber animate-pulse" />
          <span>Active Retrieval Scope:</span>
          <span className="font-semibold text-hit-blue">{accessScope}</span>
        </div>
      </div>
    </form>
  );
}

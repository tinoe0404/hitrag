import React from "react";
import { cn } from "@/lib/utils";

interface HITRAGWordmarkProps {
  variant?: "navy" | "light";
  className?: string;
}

export function HITRAGWordmark({
  variant = "navy",
  className,
}: HITRAGWordmarkProps) {
  const isLight = variant === "light";

  return (
    <div className={cn("flex items-center gap-2.5 select-none", className)}>
      {/* Institutional Document Glyph with Amber Dot */}
      <div className="relative flex items-center justify-center">
        <svg
          width="28"
          height="32"
          viewBox="0 0 28 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={isLight ? "text-white" : "text-hit-blue"}
        >
          {/* Document Fold Icon */}
          <path
            d="M4 2C2.89543 2 2 2.89543 2 4V28C2 29.1046 2.89543 30 4 30H24C25.1046 30 26 29.1046 26 28V10L18 2H4Z"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M18 2V10H26"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Document Content Lines */}
          <path
            d="M7 15H21M7 20H17M7 25H14"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
        {/* Innovation Amber Accent Dot */}
        <span
          className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-hit-amber border-2 border-hit-surface"
          aria-hidden="true"
        />
      </div>

      {/* Typography Wordmark */}
      <div className="flex flex-col">
        <div className="flex items-center">
          <span
            className={cn(
              "font-display text-xl font-bold tracking-tight",
              isLight ? "text-white" : "text-hit-blue"
            )}
          >
            HITRAG
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-hit-amber ml-1 self-baseline mt-1.5" />
        </div>
        <span
          className={cn(
            "font-mono text-[9px] uppercase tracking-wider font-semibold -mt-1",
            isLight ? "text-hit-border" : "text-hit-text-secondary"
          )}
        >
          HIT Knowledge Assistant
        </span>
      </div>
    </div>
  );
}

import React from "react";
import { cn } from "@/lib/utils";

interface CitationTagProps {
  index: number;
  label?: string;
  onSelect?: (index: number) => void;
  className?: string;
}

export function CitationTag({
  index,
  label,
  onSelect,
  className,
}: CitationTagProps) {
  const displayText = label ? `[${index}: ${label}]` : `[${index}]`;

  return (
    <button
      type="button"
      onClick={() => onSelect?.(index)}
      className={cn(
        "inline-flex items-center gap-1 font-mono text-xs font-semibold px-1.5 py-0.5 rounded transition-colors",
        "text-hit-amber bg-hit-amber/10 hover:bg-hit-blue hover:text-white cursor-pointer",
        className
      )}
      title={label ? `Source ${index}: ${label}` : `Source ${index}`}
    >
      {displayText}
    </button>
  );
}

export type AccessTier = "Public" | "Student" | "Lecturer" | "Admin";

interface TierPillProps {
  tier: AccessTier | string;
  className?: string;
}

export function TierPill({ tier, className }: TierPillProps) {
  const isPublic = tier.toLowerCase() === "public";

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium uppercase tracking-wider",
        isPublic
          ? "bg-hit-border/60 text-hit-text-secondary"
          : "bg-hit-blue text-white",
        className
      )}
    >
      {tier}
    </span>
  );
}

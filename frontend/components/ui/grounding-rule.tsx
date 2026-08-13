import React from "react";
import { cn } from "@/lib/utils";

export type GroundingState = "grounded" | "ungrounded" | "restricted";

interface GroundingRuleProps {
  state?: GroundingState;
  className?: string;
}

export function GroundingRule({
  state = "grounded",
  className,
}: GroundingRuleProps) {
  const isGrounded = state === "grounded";
  const isRestricted = state === "restricted";

  return (
    <span
      data-testid="grounding-rule"
      aria-hidden="true"
      className={cn(
        "absolute left-0 top-0 bottom-0 w-[3px] rounded-l-full transition-colors",
        isGrounded && "bg-hit-amber",
        (isRestricted || state === "ungrounded") && "bg-hit-warning",
        className
      )}
    />
  );
}

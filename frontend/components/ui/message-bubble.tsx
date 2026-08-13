import React from "react";
import { cn } from "@/lib/utils";
import { GroundingRule, GroundingState } from "./grounding-rule";

interface MessageBubbleProps {
  role: "user" | "assistant";
  groundingState?: GroundingState;
  children: React.ReactNode;
  className?: string;
  timestamp?: string;
}

export function MessageBubble({
  role,
  groundingState,
  children,
  className,
  timestamp,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex flex-col mb-4 max-w-[85%] sm:max-w-[75%]",
        isUser ? "ml-auto items-end" : "mr-auto items-start",
        className
      )}
    >
      <div
        className={cn(
          "relative px-4 py-3 text-sm shadow-sm overflow-hidden",
          isUser
            ? "bg-hit-border/40 text-hit-text-primary rounded-2xl rounded-tr-sm"
            : "bg-hit-surface text-hit-text-primary border border-hit-border rounded-2xl rounded-tl-sm pl-5"
        )}
      >
        {!isUser && groundingState && (
          <GroundingRule state={groundingState} />
        )}
        <div className="space-y-2">{children}</div>
      </div>

      {timestamp && (
        <span className="text-[10px] text-hit-text-secondary mt-1 px-1 font-mono">
          {timestamp}
        </span>
      )}
    </div>
  );
}

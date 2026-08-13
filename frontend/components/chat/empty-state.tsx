import React from "react";
import { HITRAGWordmark } from "@/components/ui/hitrag-wordmark";
import { AccessTier } from "@/components/ui/citation-tag";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  userRole?: AccessTier;
  onSelectPrompt: (promptText: string) => void;
  className?: string;
}

const studentPrompts = [
  "When does registration close?",
  "What happens if I fail a module?",
  "What do I need before starting industrial attachment?",
  "Where can I find the library loan and fee policy?",
];

const lecturerPrompts = [
  "What are the Part II continuous assessment grade submission deadlines?",
  "What is the procedure for requesting a supplementary examination paper review?",
  "Where are the industrial attachment academic supervision rubrics specified?",
  "What is the policy on student academic appeals for semester results?",
];

export function EmptyState({
  userRole = "Student",
  onSelectPrompt,
  className,
}: EmptyStateProps) {
  const isLecturerOrAdmin = userRole === "Lecturer" || userRole === "Admin";
  const prompts = isLecturerOrAdmin ? lecturerPrompts : studentPrompts;

  return (
    <div
      className={cn(
        "flex-1 flex flex-col items-center justify-center p-6 text-center max-w-xl mx-auto my-auto animate-fadeIn",
        className
      )}
    >
      {/* Quiet Brand Seal */}
      <div className="mb-6 opacity-90 scale-105">
        <HITRAGWordmark variant="navy" />
      </div>

      {/* Subdued Invitation Prompt */}
      <h2 className="font-display font-bold text-lg text-hit-blue mb-1">
        Search HIT Academic Regulations & Documents
      </h2>
      <p className="font-body text-xs text-hit-text-secondary mb-8 leading-relaxed max-w-md">
        Ask a question about university procedures, departmental handbooks, or examination policies.
      </p>

      {/* Plain Tappable Text Rows (No gradient cards) */}
      <div className="w-full space-y-2 text-left mb-8">
        <span className="block font-mono text-[10px] uppercase tracking-wider text-hit-text-secondary mb-2 px-1">
          Suggested Queries for {userRole} Access Scope
        </span>

        {prompts.map((promptText, index) => (
          <button
            key={index}
            type="button"
            onClick={() => onSelectPrompt(promptText)}
            className="w-full px-4 py-3 rounded-lg bg-hit-surface border border-hit-border hover:border-hit-amber/60 hover:bg-hit-bg/70 text-hit-text-primary text-xs font-body leading-normal transition-colors flex items-center justify-between group cursor-pointer shadow-2xs"
          >
            <span className="truncate pr-2">{promptText}</span>
            <span className="font-mono text-hit-text-secondary/60 group-hover:text-hit-amber text-xs transition-colors shrink-0">
              ↳
            </span>
          </button>
        ))}
      </div>

      {/* Grounding Reinforcement Footer */}
      <div className="flex items-center gap-1.5 font-mono text-[11px] text-hit-text-secondary bg-hit-bg border border-hit-border px-3 py-1.5 rounded-full">
        <span className="w-1.5 h-1.5 rounded-full bg-hit-amber" />
        <span>Answers are drawn from official HIT documents and always cited.</span>
      </div>
    </div>
  );
}

import React from "react";
import { TierPill, AccessTier } from "@/components/ui/citation-tag";
import { cn } from "@/lib/utils";

export interface CitationDetail {
  index: number;
  documentTitle: string;
  excerpt: string;
  department: string;
  documentType: string;
  lastUpdated: string;
  accessTier: AccessTier;
  documentUrl?: string;
}

interface CitationDetailPanelProps {
  citation: CitationDetail | null;
  onClose: () => void;
  className?: string;
}

export function CitationDetailPanel({
  citation,
  onClose,
  className,
}: CitationDetailPanelProps) {
  if (!citation) return null;

  return (
    <>
      {/* Mobile Overlay / Backdrop */}
      <div
        className="fixed inset-0 bg-hit-blue-dark/40 backdrop-blur-xs z-40 md:hidden animate-fadeIn"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-in Panel (Desktop: Right panel, Mobile: Bottom sheet) */}
      <aside
        role="dialog"
        aria-label={`Citation details for document ${citation.documentTitle}`}
        className={cn(
          "fixed md:relative z-50 md:z-auto bg-hit-surface border-hit-border flex flex-col justify-between shadow-2xl md:shadow-none transition-all duration-300 ease-in-out",
          // Mobile Bottom Sheet styling
          "inset-x-0 bottom-0 max-h-[85vh] rounded-t-2xl border-t p-5",
          // Desktop Right Slide-in Panel styling (doesn't cover conversation)
          "md:inset-auto md:w-96 md:h-full md:max-h-none md:rounded-none md:border-t-0 md:border-l md:p-6 shrink-0",
          className
        )}
      >
        {/* Mobile handle indicator */}
        <div className="md:hidden flex justify-center mb-3">
          <div className="w-10 h-1 rounded-full bg-hit-border" />
        </div>

        <div className="space-y-5 overflow-y-auto pr-1">
          {/* Top Header Row */}
          <div className="flex items-center justify-between border-b border-hit-border pb-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-hit-amber bg-hit-amber/10 border border-hit-amber/30 px-2 py-0.5 rounded">
                [{citation.index}]
              </span>
              <h3 className="font-display font-bold text-xs uppercase tracking-wider text-hit-text-secondary">
                Citation Footnote
              </h3>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-hit-text-secondary hover:text-hit-blue p-1 rounded-md hover:bg-hit-bg transition-colors font-mono text-xs flex items-center gap-1"
              aria-label="Close citation details"
            >
              <span>✕</span>
              <span className="hidden sm:inline">Close</span>
            </button>
          </div>

          {/* Source Document Title */}
          <div className="space-y-1.5">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-hit-text-secondary">
              Source Document Title
            </span>
            <h4 className="font-mono font-bold text-sm text-hit-blue leading-snug break-words">
              {citation.documentTitle}
            </h4>
          </div>

          {/* Grounded Excerpt */}
          <div className="space-y-2">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-hit-amber">
              Grounded Text Excerpt
            </span>
            <blockquote className="relative p-3.5 rounded-r-lg bg-hit-bg border-l-4 border-l-hit-amber text-xs text-hit-text-primary leading-relaxed font-body italic border-y border-r border-hit-border/60">
              &ldquo;{citation.excerpt}&rdquo;
            </blockquote>
          </div>

          {/* Metadata Row */}
          <div className="space-y-3 pt-1 border-t border-hit-border/60">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-hit-text-secondary">
              Document Metadata
            </span>
            
            <div className="grid grid-cols-2 gap-3 font-mono text-xs text-hit-text-secondary bg-hit-bg/60 p-3 rounded-lg border border-hit-border/60">
              <div>
                <span className="block text-[10px] uppercase text-hit-text-secondary/70">Department</span>
                <span className="font-medium text-hit-text-primary">{citation.department}</span>
              </div>
              <div>
                <span className="block text-[10px] uppercase text-hit-text-secondary/70">Document Type</span>
                <span className="font-medium text-hit-text-primary">{citation.documentType}</span>
              </div>
              <div>
                <span className="block text-[10px] uppercase text-hit-text-secondary/70">Last Updated</span>
                <span className="font-medium text-hit-text-primary">{citation.lastUpdated}</span>
              </div>
              <div>
                <span className="block text-[10px] uppercase text-hit-text-secondary/70">Access Level</span>
                <div className="mt-0.5">
                  <TierPill tier={citation.accessTier} />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Footer */}
        <div className="pt-4 mt-4 border-t border-hit-border flex items-center justify-between">
          <a
            href={citation.documentUrl || "#"}
            onClick={(e) => {
              if (!citation.documentUrl) e.preventDefault();
            }}
            className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-hit-blue hover:text-hit-amber transition-colors group"
          >
            <span>View full document</span>
            <span className="group-hover:translate-x-0.5 transition-transform">→</span>
          </a>
          <span className="font-mono text-[10px] text-hit-text-secondary">
            Verified ground source
          </span>
        </div>
      </aside>
    </>
  );
}

// Keep export default compatibility alias if referenced elsewhere
export const CitationDrawer = CitationDetailPanel;

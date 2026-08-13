import React from "react";
import { TierPill, AccessTier } from "@/components/ui/citation-tag";
import { cn } from "@/lib/utils";

export interface RestrictedBoundaryNoticeProps {
  requiredTier?: AccessTier | string;
  targetOffice?: string;
  officeContact?: string;
  className?: string;
}

export function RestrictedBoundaryNotice({
  requiredTier = "Staff / Admin",
  targetOffice = "HIT Human Resources & Registrar's Office",
  officeContact = "hr-enquiries@hit.ac.zw",
  className,
}: RestrictedBoundaryNoticeProps) {
  return (
    <div className={cn("space-y-3 py-0.5", className)}>
      {/* Calm Header indicator */}
      <div className="flex items-center justify-between border-b border-hit-border/60 pb-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] font-bold tracking-wider text-hit-warning uppercase bg-hit-warning/10 px-2 py-0.5 rounded border border-hit-warning/20">
            Access Tier Boundary
          </span>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[11px] text-hit-text-secondary">
          <span>Required Level:</span>
          <TierPill tier={requiredTier} />
        </div>
      </div>

      {/* Neutral Matter-of-Fact Explanation */}
      <p className="text-sm text-hit-text-primary leading-relaxed">
        This query pertains to institutional records outside the access permissions of student accounts.
      </p>

      {/* Institutional Office Recommendation Card */}
      <div className="p-3.5 rounded-lg bg-hit-bg border border-hit-border/80 space-y-1.5 font-mono text-xs text-hit-text-secondary">
        <div className="flex items-center justify-between text-hit-text-primary font-semibold">
          <span>Suggested Contact Office</span>
          <span className="text-[10px] text-hit-blue font-normal uppercase">Direct Enquiry</span>
        </div>
        <p className="text-hit-blue font-medium">{targetOffice}</p>
        {officeContact && (
          <p className="text-[11px] text-hit-text-secondary">
            Official channel: <span className="text-hit-text-primary select-all">{officeContact}</span>
          </p>
        )}
      </div>
    </div>
  );
}

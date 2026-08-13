"use client";

import React, { useState, useEffect } from "react";
import { AccessTier } from "@/components/ui/citation-tag";
import { getCurrentUserRole, setCurrentUserRole } from "@/lib/api";

export function DevRoleSwitcher() {
  const [role, setRole] = useState<AccessTier>("Student");

  useEffect(() => {
    setRole(getCurrentUserRole());
  }, []);

  const handleRoleChange = (newRole: AccessTier) => {
    setRole(newRole);
    setCurrentUserRole(newRole);
    // Dispatch custom event to notify open pages of role switch
    window.dispatchEvent(new Event("hitrag_role_changed"));
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 bg-hit-blue-dark text-white border border-hit-amber/50 rounded-xl p-2 shadow-2xl font-mono text-xs flex items-center gap-2">
      <div className="flex flex-col">
        <span className="text-[9px] uppercase tracking-wider text-hit-amber font-bold">
          DEV ONLY — remove before backend integration
        </span>
        <span className="text-[11px] text-hit-border">Mock Role Switcher</span>
      </div>

      <select
        value={role}
        onChange={(e) => handleRoleChange(e.target.value as AccessTier)}
        className="bg-hit-blue text-white border border-hit-border rounded px-2 py-1 text-xs focus:outline-none focus:border-hit-amber cursor-pointer"
      >
        <option value="Student">Student</option>
        <option value="Lecturer">Lecturer</option>
        <option value="Admin">Admin</option>
        <option value="Public">Public</option>
      </select>
    </div>
  );
}

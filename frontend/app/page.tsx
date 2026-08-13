"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUserRole } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const role = getCurrentUserRole();
    if (!role) {
      router.replace("/login");
    } else {
      router.replace("/chat");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-hit-bg flex items-center justify-center font-mono text-xs text-hit-text-secondary">
      <span>Redirecting to HITRAG application...</span>
    </div>
  );
}

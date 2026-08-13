"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    async function checkAuth() {
      const user = await getCurrentUser();
      if (!user) {
        router.replace("/login");
      } else {
        router.replace("/chat");
      }
    }
    checkAuth();
  }, [router]);

  return (
    <div className="min-h-screen bg-hit-bg flex items-center justify-center font-mono text-xs text-hit-text-secondary">
      <span>Redirecting to HITRAG application...</span>
    </div>
  );
}

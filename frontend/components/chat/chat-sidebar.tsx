"use client";

import React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { HITRAGWordmark } from "@/components/ui/hitrag-wordmark";
import { cn } from "@/lib/utils";
import { TierPill, AccessTier } from "@/components/ui/citation-tag";

export interface ConversationItem {
  id: string;
  title: string;
  timestamp: string;
  group: "Today" | "Earlier this week";
}

export interface UserProfile {
  name: string;
  role: AccessTier;
  department: string;
  title: string;
}

interface ChatSidebarProps {
  conversations: ConversationItem[];
  isOpen: boolean;
  onClose: () => void;
  userProfile?: UserProfile;
}

export function ChatSidebar({
  conversations,
  isOpen,
  onClose,
  userProfile = {
    name: "Tendai M.",
    role: "Student",
    department: "Software Eng",
    title: "Year 2",
  },
}: ChatSidebarProps) {
  const params = useParams();
  const router = useRouter();
  const activeId = (params?.conversationId as string) || "conv-101";

  const todayConvs = conversations.filter((c) => c.group === "Today");
  const earlierConvs = conversations.filter((c) => c.group === "Earlier this week");

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-hit-blue-dark/50 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      {/* Sidebar Container: Slide-over drawer on mobile, static sidebar on desktop */}
      <aside
        className={cn(
          "fixed lg:static top-0 bottom-0 left-0 z-50 w-72 bg-hit-blue text-white flex flex-col justify-between border-r border-hit-blue-dark transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Top Header */}
        <div className="p-4 border-b border-white/10 space-y-4">
          <div className="flex items-center justify-between">
            <HITRAGWordmark variant="light" />
            <button
              onClick={onClose}
              className="lg:hidden text-hit-border hover:text-white p-1"
              aria-label="Close sidebar"
            >
              ✕
            </button>
          </div>

          {/* New Conversation Action */}
          <button
            onClick={() => {
              router.push("/chat");
              onClose();
            }}
            className="w-full py-2.5 px-3 rounded-lg bg-hit-amber hover:bg-hit-amber/90 text-hit-blue-dark font-display font-semibold text-xs tracking-wide shadow-sm flex items-center justify-center gap-2 cursor-pointer transition-colors"
          >
            <span className="font-bold text-sm">+</span>
            <span>New Conversation</span>
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-6">
          {/* Today Group */}
          {todayConvs.length > 0 && (
            <div className="space-y-1.5">
              <span className="font-mono text-[10px] uppercase tracking-wider text-hit-amber px-2 font-semibold">
                Today
              </span>
              <div className="space-y-1">
                {todayConvs.map((conv) => {
                  const isActive = conv.id === activeId;
                  return (
                    <Link
                      key={conv.id}
                      href={`/chat/${conv.id}`}
                      onClick={onClose}
                      className={cn(
                        "block px-3 py-2 rounded-lg text-xs font-body transition-colors truncate",
                        isActive
                          ? "bg-white/15 text-white font-medium border-l-2 border-hit-amber"
                          : "text-hit-border hover:bg-white/5 hover:text-white"
                      )}
                    >
                      {conv.title}
                    </Link>
                  );
                })}
              </div>
            </div>
          )}

          {/* Earlier Group */}
          {earlierConvs.length > 0 && (
            <div className="space-y-1.5">
              <span className="font-mono text-[10px] uppercase tracking-wider text-hit-amber px-2 font-semibold">
                Earlier this week
              </span>
              <div className="space-y-1">
                {earlierConvs.map((conv) => {
                  const isActive = conv.id === activeId;
                  return (
                    <Link
                      key={conv.id}
                      href={`/chat/${conv.id}`}
                      onClick={onClose}
                      className={cn(
                        "block px-3 py-2 rounded-lg text-xs font-body transition-colors truncate",
                        isActive
                          ? "bg-white/15 text-white font-medium border-l-2 border-hit-amber"
                          : "text-hit-border hover:bg-white/5 hover:text-white"
                      )}
                    >
                      {conv.title}
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Signed-in User Badge */}
        <div className="p-3.5 border-t border-white/10 bg-hit-blue-dark/50 flex items-center justify-between">
          <div className="flex flex-col min-w-0 pr-2">
            <span className="font-display font-semibold text-xs text-white truncate">
              {userProfile.name}
            </span>
            <span className="font-mono text-[10px] text-hit-border truncate" title={`${userProfile.department} · ${userProfile.title}`}>
              {userProfile.department} · {userProfile.title}
            </span>
          </div>
          <TierPill tier={userProfile.role} className="shrink-0 scale-90" />
        </div>
      </aside>
    </>
  );
}

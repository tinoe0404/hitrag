"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { CitationDrawer, CitationDetail } from "@/components/chat/citation-drawer";
import { ChatInput } from "@/components/chat/chat-input";
import { EmptyState } from "@/components/chat/empty-state";
import { GroundingRule } from "@/components/ui/grounding-rule";
import { RestrictedBoundaryNotice } from "@/components/ui/restricted-boundary-notice";
import { CitationTag, TierPill, AccessTier } from "@/components/ui/citation-tag";
import { HITRAGWordmark } from "@/components/ui/hitrag-wordmark";
import { DevRoleSwitcher } from "@/components/ui/dev-role-switcher";
import { cn } from "@/lib/utils";
import {
  getConversations,
  getConversationById,
  getCurrentUserRole,
  getCurrentUserProfile,
  sendMessage,
} from "@/lib/api";
import { MockMessage } from "@/lib/mock-data";

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const activeConversationId = (params?.conversationId as string) || null;

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<CitationDetail | null>(null);
  
  // User Profile & Role State
  const [userRole, setUserRole] = useState<AccessTier>("Student");
  const [messages, setMessages] = useState<MockMessage[]>([]);
  const [isSending, setIsSending] = useState(false);

  // Sync role and active conversation messages
  const loadConversationData = useCallback(async () => {
    const { getCurrentUser, mapRoleToAccessTier } = await import("@/lib/api");
    const activeUser = await getCurrentUser();

    if (!activeUser) {
      router.replace("/login");
      return;
    }

    const tier = mapRoleToAccessTier(activeUser.role);
    setUserRole(tier);

    if (activeConversationId) {
      const conv = getConversationById(activeConversationId);
      if (conv) {
        setMessages(conv.messages);
      } else {
        setMessages([]);
      }
    } else {
      setMessages([]);
    }
  }, [activeConversationId, router]);

  useEffect(() => {
    loadConversationData();

    // Listen to role changes from DevRoleSwitcher
    const handleRoleChanged = () => {
      loadConversationData();
    };

    window.addEventListener("hitrag_role_changed", handleRoleChanged);
    return () => {
      window.removeEventListener("hitrag_role_changed", handleRoleChanged);
    };
  }, [loadConversationData]);

  const conversations = getConversations();
  const currentProfile = getCurrentUserProfile(userRole);

  const activeAccessScope =
    userRole === "Lecturer"
      ? "Public + Lecturer"
      : userRole === "Admin"
      ? "Public + Admin"
      : "Public + Student";

  // Handle sending new queries
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isSending) return;

    setIsSending(true);

    const tempTimestamp = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMsg: MockMessage = {
      id: `m-user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: tempTimestamp,
    };

    setMessages((prev) => [...prev, userMsg]);

    const targetConvId = activeConversationId || "conv-101";

    const { assistantMessage } = await sendMessage(targetConvId, text);

    setMessages((prev) => [...prev, assistantMessage]);
    setIsSending(false);
  };

  // Helper to render message content with clickable citations
  const renderMessageContent = (msg: MockMessage) => {
    if (msg.role === "user") {
      return <p className="leading-relaxed">{msg.content}</p>;
    }

    if (msg.groundingState === "restricted" && msg.restrictedData) {
      return (
        <RestrictedBoundaryNotice
          requiredTier={msg.restrictedData.requiredTier}
          targetOffice={msg.restrictedData.targetOffice}
          officeContact={msg.restrictedData.officeContact}
        />
      );
    }

    // Process citations [1], [2] in text content
    const parts = msg.content.split(/(\[\d+\])/g);

    return (
      <div className="space-y-3">
        <div className="leading-relaxed whitespace-pre-wrap">
          {parts.map((part, idx) => {
            const match = part.match(/^\[(\d+)\]$/);
            if (match && msg.citations) {
              const citationIdx = parseInt(match[1], 10);
              const cit = msg.citations[citationIdx];
              if (cit) {
                return (
                  <CitationTag
                    key={idx}
                    index={citationIdx}
                    label={cit.documentTitle}
                    onSelect={() => setSelectedCitation(cit)}
                    className="mx-0.5"
                  />
                );
              }
            }
            return <span key={idx}>{part}</span>;
          })}
        </div>

        {msg.citations && Object.keys(msg.citations).length > 0 && (
          <div className="mt-3 pt-2.5 border-t border-hit-border/50 flex items-center gap-1.5 flex-wrap text-xs font-mono text-hit-text-secondary">
            <span className="font-semibold text-[10px] uppercase tracking-wider text-hit-amber">
              Verified Sources:
            </span>
            {Object.values(msg.citations).map((cit) => (
              <button
                key={cit.index}
                type="button"
                onClick={() => setSelectedCitation(cit)}
                className="inline-flex items-center gap-1 bg-hit-bg hover:bg-hit-border/50 border border-hit-border px-2 py-0.5 rounded text-[11px] text-hit-text-primary transition-colors"
              >
                <span className="text-hit-amber font-bold">[{cit.index}]</span>
                <span className="truncate max-w-[180px]">{cit.documentTitle}</span>
                <TierPill tier={cit.accessTier} className="scale-75 origin-right" />
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-hit-bg text-hit-text-primary overflow-hidden relative">
      {/* Dev Only Role Switcher */}
      <DevRoleSwitcher />

      {/* Left Sidebar */}
      <ChatSidebar
        conversations={conversations}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        userProfile={currentProfile}
      />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        {/* Top Navbar */}
        <header className="h-14 bg-hit-surface border-b border-hit-border px-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-1.5 text-hit-blue hover:bg-hit-bg rounded-lg"
              aria-label="Open sidebar"
            >
              ☰
            </button>
            <div className="flex items-center gap-2">
              <HITRAGWordmark variant="navy" className="scale-90" />
              <span className="hidden sm:inline-block font-mono text-[10px] text-hit-text-secondary border-l border-hit-border pl-2">
                Knowledge Canvas
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <TierPill tier={currentProfile.role} />
          </div>
        </header>

        {/* Message Document Canvas & Optional Citation Side Panel */}
        <div className="flex-1 flex min-h-0 overflow-hidden">
          {/* Messages Feed or Empty Canvas State */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 flex flex-col">
            {messages.length === 0 ? (
              <EmptyState
                userRole={currentProfile.role}
                onSelectPrompt={handleSendMessage}
              />
            ) : (
              <div className="max-w-4xl mx-auto space-y-6 w-full my-auto">
                {messages.map((msg) => {
                  const isUser = msg.role === "user";
                  return (
                    <div
                      key={msg.id}
                      className={cn(
                        "flex flex-col",
                        isUser ? "items-end" : "items-start"
                      )}
                    >
                      {/* Assistant Document Block / User Bubble */}
                      <div
                        className={cn(
                          "relative w-full max-w-3xl text-sm transition-all",
                          isUser
                            ? "bg-hit-border/40 text-hit-text-primary px-4 py-3 rounded-2xl rounded-tr-sm self-end max-w-xl"
                            : "bg-hit-surface text-hit-text-primary border border-hit-border rounded-xl p-5 pl-6 shadow-sm"
                        )}
                      >
                        {!isUser && msg.groundingState && (
                          <GroundingRule state={msg.groundingState} />
                        )}

                        {!isUser && (
                          <div className="flex items-center justify-between border-b border-hit-border/60 pb-2.5 mb-3">
                            <span className="font-display font-semibold text-xs text-hit-blue">
                              HIT Knowledge Assistant Response
                            </span>
                            <span
                              className={cn(
                                "font-mono text-[10px] font-semibold px-2 py-0.5 rounded",
                                msg.groundingState === "grounded"
                                  ? "bg-hit-amber/15 text-hit-blue"
                                  : "bg-hit-warning/15 text-hit-warning"
                              )}
                            >
                              {msg.groundingState === "grounded"
                                ? "✓ Grounded in HIT Records"
                                : "[!] Restricted Access Boundary"}
                            </span>
                          </div>
                        )}

                        {renderMessageContent(msg)}
                      </div>

                      <span className="font-mono text-[10px] text-hit-text-secondary mt-1 px-1">
                        {msg.timestamp}
                      </span>
                    </div>
                  );
                })}

                {/* Loading indicator when waiting for assistant message */}
                {isSending && (
                  <div className="flex flex-col items-start">
                    <div className="relative w-full max-w-3xl bg-hit-surface border border-hit-border rounded-xl p-5 pl-6 shadow-sm">
                      <GroundingRule state="grounded" />
                      <div className="flex items-center gap-2 font-mono text-xs text-hit-text-secondary">
                        <span className="w-3 h-3 rounded-full border-2 border-hit-amber border-t-transparent animate-spin" />
                        <span>Scanning HIT Document Repository...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Citation Side Drawer / Bottom Sheet */}
          {selectedCitation && (
            <CitationDrawer
              citation={selectedCitation}
              onClose={() => setSelectedCitation(null)}
            />
          )}
        </div>

        {/* Query Input with Scope Transparency Indicator */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={isSending}
          accessScope={activeAccessScope}
        />
      </div>
    </div>
  );
}

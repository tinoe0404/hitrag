import {
  MOCK_CONVERSATIONS,
  MOCK_USER_PROFILES,
  MockConversation,
  MockMessage,
} from "./mock-data";
import { AccessTier } from "@/components/ui/citation-tag";
import { UserProfile } from "@/components/chat/chat-sidebar";

// Local storage session key simulation
const SESSION_ROLE_KEY = "hitrag_mock_user_role";

export function getCurrentUserRole(): AccessTier {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem(SESSION_ROLE_KEY) as AccessTier;
    if (saved && MOCK_USER_PROFILES[saved]) {
      return saved;
    }
  }
  return "Student";
}

export function setCurrentUserRole(role: AccessTier): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(SESSION_ROLE_KEY, role);
  }
}

export function getCurrentUserProfile(role?: AccessTier): UserProfile {
  const activeRole = role || getCurrentUserRole();
  return MOCK_USER_PROFILES[activeRole] || MOCK_USER_PROFILES.Student;
}

export function getConversations(): MockConversation[] {
  return MOCK_CONVERSATIONS;
}

export function getConversationById(id: string): MockConversation | undefined {
  return MOCK_CONVERSATIONS.find((conv) => conv.id === id);
}

export async function sendMessage(
  conversationId: string,
  userMessageText: string
): Promise<{ userMessage: MockMessage; assistantMessage: MockMessage }> {
  const timestamp = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const userMessage: MockMessage = {
    id: `m-usr-${Date.now()}`,
    role: "user",
    content: userMessageText,
    timestamp,
  };

  // Simulate network latency (800ms)
  await new Promise((resolve) => setTimeout(resolve, 800));

  // Determine response based on query keywords or fallback
  const lowerQuery = userMessageText.toLowerCase();

  let assistantMessage: MockMessage;

  if (lowerQuery.includes("salary") || lowerQuery.includes("hr") || lowerQuery.includes("appraisal")) {
    assistantMessage = {
      id: `m-ast-${Date.now()}`,
      role: "assistant",
      groundingState: "restricted",
      timestamp,
      content: "RESTRICTED_ACCESS",
      restrictedData: {
        requiredTier: "Staff / Admin",
        targetOffice: "HIT Human Resources & Staff Relations Office",
        officeContact: "hr-enquiries@hit.ac.zw",
      },
    };
  } else {
    assistantMessage = {
      id: `m-ast-${Date.now()}`,
      role: "assistant",
      groundingState: "grounded",
      timestamp,
      content: `Your query regarding "${userMessageText}" has been processed against the official HIT Document Repository. \n\n• Information retrieved from HIT General Academic Regulations (2026) confirms compliance with institutional standards [1].\n\n• For further guidance or formal submission, consult your Department Chairperson [2].`,
      citations: {
        1: {
          index: 1,
          documentTitle: "HIT Academic Regulations & Guidelines 2026",
          department: "Academic Affairs",
          documentType: "Institutional Policy",
          lastUpdated: "10 Feb 2026",
          accessTier: "Public",
          excerpt: "All registered students and academic staff are bound by the general academic and administrative regulations published in the university charter.",
          documentUrl: "#",
        },
        2: {
          index: 2,
          documentTitle: "HIT Student Code of Conduct and Administration",
          department: "Student Affairs",
          documentType: "Student Handbook",
          lastUpdated: "15 Jan 2026",
          accessTier: "Student",
          excerpt: "Official academic petitions, module adjustments, or special exemptions must be submitted through the department chairperson.",
          documentUrl: "#",
        },
      },
    };
  }

  return { userMessage, assistantMessage };
}

import {
  MOCK_CONVERSATIONS,
  MOCK_USER_PROFILES,
  MockConversation,
  MockMessage,
} from "./mock-data";
import { AccessTier } from "@/components/ui/citation-tag";
import { UserProfile } from "@/components/chat/chat-sidebar";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const AUTH_TOKEN_KEY = "hitrag_access_token";

// Auth Data Structures matching Backend UserOut
export interface BackendUser {
  id: number;
  email: string;
  full_name: string;
  role: "PUBLIC" | "STUDENT" | "LECTURER" | "ADMIN";
  is_active: boolean;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  role?: string;
}

// Convert Backend User Role Enum to UI AccessTier
export function mapRoleToAccessTier(roleStr?: string): AccessTier {
  switch (roleStr?.toUpperCase()) {
    case "ADMIN":
    case "STAFF / ADMIN":
      return "Admin";
    case "LECTURER":
      return "Lecturer";
    case "PUBLIC":
      return "Public";
    case "STUDENT":
    default:
      return "Student";
  }
}

// Store & Retrieve JWT token from localStorage
export function getStoredToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }
  return null;
}

export function setStoredToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  }
}

export function removeStoredToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

// Real Backend Register API Call
export async function registerUser(payload: RegisterPayload): Promise<BackendUser> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: payload.email,
      password: payload.password,
      full_name: payload.full_name,
      role: payload.role || "STUDENT",
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Registration failed (${res.status})`);
  }

  return res.json();
}

// Real Backend Login API Call (OAuth2 form-data)
export async function loginUser(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Invalid email or password.");
  }

  const tokenData = await res.json();
  setStoredToken(tokenData.access_token);
  return tokenData;
}

// Real Backend Get Current User / Session Check Call (GET /api/v1/auth/me)
export async function getCurrentUser(): Promise<BackendUser | null> {
  const token = getStoredToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      removeStoredToken();
      return null;
    }

    return await res.json();
  } catch {
    return null;
  }
}

// Real Backend Stateless Logout Call
export async function logoutUser(): Promise<void> {
  const token = getStoredToken();
  if (token) {
    fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).catch(() => {});
  }
  removeStoredToken();
}

// Compatibility helper functions for UI components
export function getCurrentUserRole(): AccessTier {
  return "Student";
}

export function setCurrentUserRole(role: AccessTier): void {
  // Legacy role switcher helper
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

  await new Promise((resolve) => setTimeout(resolve, 800));

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

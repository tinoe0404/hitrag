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

export async function getConversations(): Promise<MockConversation[]> {
  const token = getStoredToken();
  if (!token) return [];
  const res = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  if (res.status === 401) {
    removeStoredToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`Failed to fetch conversations (${res.status})`);
  }
  const convList = await res.json();
  return convList.map((c: any) => ({
    id: String(c.id),
    title: c.title,
    timestamp: new Date(c.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    group: "Today" as const,
    messages: [],
  }));
}

export async function getConversationById(id: string): Promise<MockConversation | undefined> {
  const token = getStoredToken();
  if (!token) return undefined;
  
  const cleanId = parseInt(id, 10);
  if (isNaN(cleanId)) return undefined;

  const [convRes, msgRes] = await Promise.all([
    fetch(`${API_BASE_URL}/api/v1/conversations/${cleanId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }),
    fetch(`${API_BASE_URL}/api/v1/conversations/${cleanId}/messages`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    })
  ]);

  if (convRes.status === 401 || msgRes.status === 401) {
    removeStoredToken();
    throw new Error("Unauthorized");
  }
  if (convRes.status === 404) {
    return undefined;
  }
  if (!convRes.ok || !msgRes.ok) {
    throw new Error("Failed to fetch conversation or messages");
  }

  const convData = await convRes.json();
  const msgData = await msgRes.json();

  const messages: MockMessage[] = msgData.map((m: any) => {
    let status: "ANSWERED" | "NOT_ENOUGH_INFORMATION" | "PARSE_ERROR" = "ANSWERED";
    let content = m.content;
    let groundingState: "grounded" | "restricted" = "grounded";

    if (m.role === "assistant") {
      if (m.content.startsWith("[System Parse Error]")) {
        status = "PARSE_ERROR";
        content = "Something went wrong generating a response, please try again.";
        groundingState = "restricted";
      } else if (m.content === "I don't have enough information in the available documents to answer that.") {
        status = "NOT_ENOUGH_INFORMATION";
        groundingState = "restricted";
      }
    }

    return {
      id: `m-${m.id}`,
      role: m.role as "user" | "assistant",
      content: content,
      groundingState,
      status,
      timestamp: new Date(m.created_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
  });

  return {
    id: String(convData.id),
    title: convData.title,
    timestamp: new Date(convData.created_at).toLocaleDateString(),
    group: "Today" as const,
    messages,
  };
}

// Document API Helpers
export interface Document {
  id: string;
  title: string;
  accessTier: string;
  // Add other fields as needed
}

export async function listDocuments(): Promise<Document[]> {
  const token = getStoredToken();
  if (!token) return [];
  const res = await fetch(`${API_BASE_URL}/api/v1/documents`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  if (res.status === 401) {
    removeStoredToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`Failed to list documents (${res.status})`);
  }
  return await res.json();
}

export async function uploadDocument(file: File): Promise<Document> {
  const token = getStoredToken();
  if (!token) throw new Error("Not authenticated");
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE_URL}/api/v1/documents`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: form,
  });
  if (res.status === 401) {
    removeStoredToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`Upload failed (${res.status})`);
  }
  return await res.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
  const token = getStoredToken();
  if (!token) throw new Error("Not authenticated");
  const res = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  if (res.status === 401) {
    removeStoredToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`Delete failed (${res.status})`);
  }
}

export async function sendMessage(
  conversationId: string,
  userMessageText: string
): Promise<{
  userMessage: MockMessage;
  assistantMessage: MockMessage;
  conversationId: string;
}> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

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

  const cleanConversationId = parseInt(conversationId, 10);
  const bodyPayload: any = {
    question: userMessageText,
  };
  if (!isNaN(cleanConversationId)) {
    bodyPayload.conversation_id = cleanConversationId;
  }

  const res = await fetch(`${API_BASE_URL}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(bodyPayload),
  });

  if (res.status === 401) {
    removeStoredToken();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`Chat request failed (${res.status})`);
  }

  const data = await res.json();

  const citationsMap: { [key: number]: any } = {};
  if (data.citations && Array.isArray(data.citations)) {
    data.citations.forEach((cit: any, idx: number) => {
      const citationIndex = idx + 1;
      citationsMap[citationIndex] = {
        index: citationIndex,
        documentTitle: cit.document_title || "Unknown Document",
        excerpt: cit.excerpt || "",
        department: "HIT Document Repository",
        documentType: "Institutional Document",
        lastUpdated: cit.created_at ? new Date(cit.created_at).toLocaleDateString() : "Recent",
        accessTier: mapRoleToAccessTier(cit.access_tier),
        documentUrl: "#",
      };
    });
  }

  let groundingState: "grounded" | "restricted" = "grounded";
  let content = data.answer || "";
  const status = data.status || "ANSWERED";

  if (status === "NOT_ENOUGH_INFORMATION") {
    content = "I don't have enough information in the available documents to answer that.";
    groundingState = "restricted";
  } else if (status === "PARSE_ERROR") {
    content = "Something went wrong generating a response, please try again.";
    groundingState = "restricted";
  }

  const assistantMessage: MockMessage = {
    id: `m-ast-${data.message_id || Date.now()}`,
    role: "assistant",
    timestamp,
    groundingState,
    status,
    content,
    ...(Object.keys(citationsMap).length > 0 ? { citations: citationsMap } : {}),
  };

  return { userMessage, assistantMessage, conversationId: String(data.conversation_id) };
}

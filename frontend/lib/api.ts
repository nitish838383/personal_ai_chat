/**
 * API client for Personal AI OS backend.
 * Tokens are stored in localStorage (acceptable for SPA; use httpOnly cookies in stricter deployments).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearTokens();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Auth
export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  me: () => request<{ id: string; email: string; full_name?: string }>("/auth/me"),
};

// Chat
export const chatApi = {
  listConversations: () => request<any[]>("/chat/conversations"),
  createConversation: (title?: string) =>
    request("/chat/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  getConversation: (id: string) => request<any>(`/chat/conversations/${id}`),
  deleteConversation: (id: string) =>
    request(`/chat/conversations/${id}`, { method: "DELETE" }),
  sendMessage: (message: string, conversationId?: string) =>
    request<any>("/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
};

// Memory
export const memoryApi = {
  list: (params?: { category?: string; q?: string }) => {
    const q = new URLSearchParams(params as any).toString();
    return request<any[]>(`/memories${q ? `?${q}` : ""}`);
  },
  create: (data: { category: string; content: string; importance?: number }) =>
    request("/memories", { method: "POST", body: JSON.stringify(data) }),
  delete: (id: string) => request(`/memories/${id}`, { method: "DELETE" }),
};

// Tasks
export const tasksApi = {
  list: (status?: string) =>
    request<any[]>(`/tasks${status ? `?status=${status}` : ""}`),
  create: (data: { title: string; description?: string; priority?: string }) =>
    request("/tasks", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: any) =>
    request(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) => request(`/tasks/${id}`, { method: "DELETE" }),
};

// Integrations
export const integrationsApi = {
  list: () => request<any[]>("/integrations"),
  connect: (provider: string) =>
    request<any>(`/integrations/${provider}/connect`, { method: "POST" }),
  disconnect: (provider: string) =>
    request(`/integrations/${provider}`, { method: "DELETE" }),
};

// Activity
export const activityApi = {
  list: () => request<any[]>("/activity"),
};

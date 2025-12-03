const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204 || res.status === 205) {
    return null;
  }

  const text = await res.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = {
  auth: {
    login(email: string, password: string) {
      return request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
    },

    logout() {
      return request("/auth/logout", { method: "POST" });
    },

    me() {
      return request("/auth/me", { method: "GET" });
    },

    register(email: string, password: string) {
      return request("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
    },

    setup2fa() {
      return request("/auth/2fa/setup", { method: "POST" });
    },

    verify2fa(token: string) {
      return request("/auth/2fa/verify", {
        method: "POST",
        body: JSON.stringify({ totp_token: token }),
      });
    },
  },

  conversations: {
    list() {
      return request("/conversations", { method: "GET" });
    },

    get(id: number) {
      return request(`/conversations/${id}`, { method: "GET" });
    },

    create(title: string) {
      return request("/conversations", {
        method: "POST",
        body: JSON.stringify({ title }),
      });
    },

    delete(id: number) {
      return request(`/conversations/${id}`, { method: "DELETE" });
    },

    messages(id: number, limit: number = 100, offset: number = 0) {
      return request(
        `/conversations/${id}/messages?limit=${limit}&offset=${offset}`,
        { method: "GET" }
      );
    },
  },

  chat: {
    send(conversationId: number | null, prompt: string, system?: string) {
      return fetch(`${BASE_URL}/chat`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          prompt,
          system: system || "Eres un asistente útil.",
        }),
      });
    },
  },

  admin: {
    users(limit: number = 50, offset: number = 0) {
      return request(
        `/admin/users?limit=${limit}&offset=${offset}`,
        { method: "GET" }
      );
    },

    conversations(userId?: number, limit: number = 50, offset: number = 0) {
      const query = new URLSearchParams();
      if (userId) query.append("user_id", String(userId));
      query.append("limit", String(limit));
      query.append("offset", String(offset));

      return request(`/admin/conversations?${query}`, { method: "GET" });
    },

    messages(conversationId: number, limit: number = 100, offset: number = 0) {
      return request(
        `/admin/conversations/${conversationId}/messages?limit=${limit}&offset=${offset}`,
        { method: "GET" }
      );
    },

    reassignConversation(conversationId: number, targetUserId: number) {
      return request(`/admin/conversations/${conversationId}/reassign`, {
        method: "POST",
        body: JSON.stringify({ target_user_id: targetUserId }),
      });
    },
  },

  config: {
    pingOllama() {
      return request("/config/ollama", { method: "GET" });
    },
  },

  prompts: {
    list(limit: number = 50, offset: number = 0) {
      return request(`/prompts?limit=${limit}&offset=${offset}`, {
        method: "GET",
      });
    },

    get(id: number) {
      return request(`/prompts/${id}`, { method: "GET" });
    },

    create(payload: {
      name: string;
      description?: string;
      content: string;
      is_default?: boolean;
    }) {
      return request("/prompts", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },

    update(id: number, payload: Record<string, any>) {
      return request(`/prompts/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    },

    delete(id: number) {
      return request(`/prompts/${id}`, { method: "DELETE" });
    },
  },
};

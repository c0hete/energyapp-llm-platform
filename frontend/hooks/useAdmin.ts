import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface AdminUser {
  id: number;
  email: string;
  role: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminConversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface AdminMessage {
  id: number;
  conversation_id: number;
  user_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export function useAdminUsers(limit: number = 50, offset: number = 0) {
  return useQuery({
    queryKey: ["admin", "users", limit, offset],
    queryFn: () => api.admin.users(limit, offset),
    staleTime: 1000 * 60 * 5,
  });
}

export function useAdminConversations(userId?: number, limit: number = 50, offset: number = 0) {
  return useQuery({
    queryKey: ["admin", "conversations", userId, limit, offset],
    queryFn: () => api.admin.conversations(userId, limit, offset),
    enabled: !!userId,
    staleTime: 1000 * 60 * 5,
  });
}

export function useAdminMessages(conversationId: number, limit: number = 100, offset: number = 0) {
  return useQuery({
    queryKey: ["admin", "messages", conversationId, limit, offset],
    queryFn: () => api.admin.messages(conversationId, limit, offset),
    enabled: !!conversationId,
    staleTime: 0,
  });
}

export function useReassignConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conversationId, targetUserId }: { conversationId: number; targetUserId: number }) =>
      api.admin.reassignConversation(conversationId, targetUserId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
  });
}

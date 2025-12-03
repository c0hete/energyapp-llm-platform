import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface Message {
  id: number;
  conversation_id: number;
  user_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: () => api.conversations.list(),
    staleTime: 1000 * 60 * 5,
  });
}

export function useConversation(id: number) {
  return useQuery({
    queryKey: ["conversations", id],
    queryFn: () => api.conversations.get(id),
    staleTime: 1000 * 60 * 5,
  });
}

export function useConversationMessages(id: number, limit: number = 100) {
  return useQuery({
    queryKey: ["conversations", id, "messages"],
    queryFn: () => api.conversations.messages(id, limit),
    staleTime: 0,
    refetchOnWindowFocus: false,
    enabled: id > 0,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (title: string) => api.conversations.create(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.conversations.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

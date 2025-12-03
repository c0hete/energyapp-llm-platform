"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface SystemPrompt {
  id: number;
  name: string;
  description: string | null;
  content: string;
  is_default: boolean;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

interface CreatePromptPayload {
  name: string;
  description?: string;
  content: string;
  is_default?: boolean;
}

interface UpdatePromptPayload {
  name?: string;
  description?: string;
  content?: string;
  is_default?: boolean;
  is_active?: boolean;
}

export function useSystemPrompts(limit = 50, offset = 0) {
  return useQuery<SystemPrompt[]>({
    queryKey: ["systemPrompts", limit, offset],
    queryFn: () => api.prompts.list(limit, offset),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useSystemPrompt(promptId: number) {
  return useQuery<SystemPrompt>({
    queryKey: ["systemPrompt", promptId],
    queryFn: () => api.prompts.get(promptId),
    staleTime: 5 * 60 * 1000,
    enabled: !!promptId,
  });
}

export function useCreatePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreatePromptPayload) =>
      api.prompts.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["systemPrompts"] });
    },
  });
}

export function useUpdatePrompt(promptId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdatePromptPayload) =>
      api.prompts.update(promptId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["systemPrompt", promptId] });
      queryClient.invalidateQueries({ queryKey: ["systemPrompts"] });
    },
  });
}

export function useDeletePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (promptId: number) =>
      api.prompts.delete(promptId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["systemPrompts"] });
    },
  });
}

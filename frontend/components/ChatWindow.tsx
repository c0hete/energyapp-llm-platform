"use client";

import { useConversationMessages } from "@/hooks/useConversations";
import { useChatStream } from "@/hooks/useChatStream";
import { useSystemPrompts } from "@/hooks/useSystemPrompts";
import { useState, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

interface ChatWindowProps {
  conversationId: number | null;
}

export default function ChatWindow({ conversationId }: ChatWindowProps) {
  const queryClient = useQueryClient();

  // Always call the hook (required by React rules)
  // Use 0 as default like before, but it won't make requests
  const { data: messages = [], isLoading, refetch } = useConversationMessages(
    conversationId ?? 0
  );

  const { data: systemPrompts = [] } = useSystemPrompts();
  const { send, loading: isSending } = useChatStream();
  const [input, setInput] = useState("");
  const [streamingContent, setStreamingContent] = useState("");
  const [selectedPromptId, setSelectedPromptId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  async function handleSendMessage() {
    if (!input.trim() || !conversationId || isSending) return;

    const userMessage = input;
    setInput("");
    setStreamingContent("");

    try {
      // Optimistic update: add user message immediately
      const tempUserMessage: Message = {
        id: -1,
        role: "user",
        content: userMessage,
        created_at: new Date().toISOString(),
      };

      // Update React Query cache with the user message
      queryClient.setQueryData(
        ["conversations", conversationId, "messages"],
        (oldData: Message[] | undefined) => [...(oldData || []), tempUserMessage]
      );

      await send(
        conversationId,
        userMessage,
        undefined,
        (chunk) => {
          setStreamingContent((prev) => prev + chunk);
        },
        selectedPromptId
      );

      // Refetch messages after streaming is complete to get the actual message IDs
      await refetch();
      setStreamingContent("");
    } catch (err) {
      console.error("Failed to send message:", err);
      // Refetch to revert optimistic update on error
      await refetch();
    }
  }

  if (!conversationId) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <svg className="w-12 h-12 text-slate-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-slate-400">Selecciona una conversación para empezar</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-slate-400">Cargando mensajes...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col max-h-[600px] overflow-hidden border border-slate-700 rounded-lg">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 min-h-0">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-slate-400 text-sm">Inicia una conversación</p>
          </div>
        ) : (
          (messages as Message[]).map((msg: Message) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-xs px-4 py-2 rounded-lg ${
                  msg.role === "user"
                    ? "bg-sky-600/80 text-white"
                    : "bg-slate-800 text-slate-100"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))
        )}

        {/* Streaming Response */}
        {streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-xs px-4 py-2 rounded-lg bg-slate-800 text-slate-100">
              <p className="text-sm whitespace-pre-wrap">{streamingContent}</p>
              <span className="inline-block w-2 h-4 ml-1 bg-slate-400 animate-pulse" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="shrink-0 border-t border-slate-700 bg-slate-900/50">
        {/* Prompt Selector */}
        {systemPrompts.length > 0 && (
          <div className="border-b border-slate-700 p-3 bg-slate-800/30">
            <label className="text-xs text-slate-400 block mb-2">System Prompt</label>
            <select
              value={selectedPromptId || ""}
              onChange={(e) =>
                setSelectedPromptId(e.target.value ? Number(e.target.value) : null)
              }
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            >
              <option value="">Sin prompt del sistema</option>
              {(systemPrompts as any[]).map((prompt) => (
                <option key={prompt.id} value={prompt.id}>
                  {prompt.name}
                  {prompt.is_default ? " (default)" : ""}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="p-4 space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Escribe tu mensaje..."
              disabled={isSending}
              className="flex-1 px-4 py-2 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 disabled:opacity-50"
            />
            <button
              onClick={handleSendMessage}
              disabled={!input.trim() || isSending}
              className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors flex items-center gap-2"
            >
              {isSending ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Enviando...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  <span>Enviar</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

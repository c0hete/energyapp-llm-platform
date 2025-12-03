"use client";

import { useAdminMessages } from "@/hooks/useAdmin";
import { useRef, useEffect } from "react";

interface AdminMessagesViewerProps {
  conversationId: number | null;
}

export default function AdminMessagesViewer({ conversationId }: AdminMessagesViewerProps) {
  const { data: messages = [], isLoading } = useAdminMessages(conversationId || 0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!conversationId) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <svg className="w-12 h-12 text-slate-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-slate-400">Selecciona una conversación</p>
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

  const typedMessages = messages as any[];

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 p-4">
        {typedMessages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-slate-400 text-sm">Sin mensajes</p>
          </div>
        ) : (
          typedMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-xs px-4 py-2 rounded-lg text-sm ${
                  msg.role === "user"
                    ? "bg-sky-600/80 text-white"
                    : "bg-slate-700 text-slate-100"
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                <p className="text-xs mt-1 opacity-70">
                  {new Date(msg.created_at).toLocaleTimeString("es-ES")}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Info Bar */}
      <div className="border-t border-slate-700 p-3 bg-slate-900/50 text-xs text-slate-400">
        <p>{typedMessages.length} mensajes en esta conversación</p>
      </div>
    </div>
  );
}

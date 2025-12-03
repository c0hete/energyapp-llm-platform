"use client";

import { useConversations, useCreateConversation, useDeleteConversation } from "@/hooks/useConversations";
import { useState } from "react";

interface ConversationsListProps {
  selectedId?: number | null;
  onSelect: (id: number) => void;
}

export default function ConversationsList({ selectedId, onSelect }: ConversationsListProps) {
  const { data: conversations = [], isLoading } = useConversations();
  const { mutate: createConv, isPending: isCreating } = useCreateConversation();
  const { mutate: deleteConv, isPending: isDeleting } = useDeleteConversation();
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  function handleCreate() {
    if (!newTitle.trim()) return;
    createConv(newTitle, {
      onSuccess: () => {
        setNewTitle("");
        setShowNewForm(false);
      },
    });
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-sm text-slate-500">Cargando conversaciones...</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* New Conversation Button */}
      <button
        onClick={() => setShowNewForm(!showNewForm)}
        className="w-full px-3 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-sm font-medium text-white transition-colors flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Nueva
      </button>

      {/* New Conversation Form */}
      {showNewForm && (
        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 space-y-2">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Título de conversación..."
            className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-600 text-sm text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
              if (e.key === "Escape") setShowNewForm(false);
            }}
          />
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={isCreating || !newTitle.trim()}
              className="flex-1 px-2 py-1 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-xs font-medium text-white"
            >
              {isCreating ? "..." : "Crear"}
            </button>
            <button
              onClick={() => setShowNewForm(false)}
              className="flex-1 px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-xs font-medium text-white"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Conversations List */}
      <div className="space-y-1 max-h-96 overflow-y-auto">
        {conversations.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-4">Sin conversaciones</p>
        ) : (
          conversations.map((conv: any) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                selectedId === conv.id
                  ? "bg-sky-600/20 border border-sky-500/30"
                  : "bg-slate-800/20 hover:bg-slate-700/50 border border-transparent"
              }`}
            >
              <button
                onClick={() => onSelect(conv.id)}
                className="flex-1 text-left min-w-0"
              >
                <p className="text-sm text-white truncate font-medium">{conv.title}</p>
                <p className="text-xs text-slate-500">
                  {new Date(conv.updated_at).toLocaleDateString("es-ES")}
                </p>
              </button>
              <button
                onClick={() => deleteConv(conv.id)}
                disabled={isDeleting}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-900/30 rounded text-red-400 transition-all"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

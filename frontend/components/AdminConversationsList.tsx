"use client";

import { useAdminConversations } from "@/hooks/useAdmin";

interface AdminConversationsListProps {
  userId: number | null;
  selectedId?: number | null;
  onSelect: (id: number) => void;
}

export default function AdminConversationsList({
  userId,
  selectedId,
  onSelect
}: AdminConversationsListProps) {
  const { data: conversations = [], isLoading } = useAdminConversations(userId || undefined);

  if (!userId) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-sm text-slate-500">Selecciona un usuario</div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-sm text-slate-500">Cargando conversaciones...</div>
      </div>
    );
  }

  return (
    <div className="space-y-1 max-h-96 overflow-y-auto">
      {conversations.length === 0 ? (
        <p className="text-xs text-slate-500 text-center py-4">Sin conversaciones</p>
      ) : (
        conversations.map((conv: any) => (
          <button
            key={conv.id}
            onClick={() => onSelect(conv.id)}
            className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
              selectedId === conv.id
                ? "bg-sky-600/20 border border-sky-500/30"
                : "bg-slate-800/20 hover:bg-slate-700/50 border border-transparent"
            }`}
          >
            <p className="text-sm text-white truncate font-medium">{conv.title}</p>
            <p className="text-xs text-slate-500 mt-1">
              {new Date(conv.updated_at).toLocaleDateString("es-ES")}
            </p>
          </button>
        ))
      )}
    </div>
  );
}

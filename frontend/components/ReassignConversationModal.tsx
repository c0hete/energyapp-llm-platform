"use client";

import { useState } from "react";
import { useAdminUsers } from "@/hooks/useAdmin";
import { useReassignConversation } from "@/hooks/useAdmin";

interface ReassignConversationModalProps {
  conversationId: number;
  currentUserId: number;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function ReassignConversationModal({
  conversationId,
  currentUserId,
  onClose,
  onSuccess,
}: ReassignConversationModalProps) {
  const { data: users = [] } = useAdminUsers();
  const { mutate: reassign, isPending } = useReassignConversation();
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);

  const handleReassign = () => {
    if (!selectedUserId) return;

    reassign(
      { conversationId, targetUserId: selectedUserId },
      {
        onSuccess: () => {
          onSuccess?.();
          onClose();
        },
      }
    );
  };

  // Filter out current user
  const availableUsers = users.filter((u: any) => u.id !== currentUserId && u.active);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-white mb-4">Mover Conversación</h2>

        <p className="text-sm text-slate-400 mb-4">
          Selecciona el usuario al que deseas trasferir esta conversación:
        </p>

        <div className="space-y-2 mb-6 max-h-64 overflow-y-auto">
          {availableUsers.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">No hay otros usuarios disponibles</p>
          ) : (
            availableUsers.map((user: any) => (
              <button
                key={user.id}
                onClick={() => setSelectedUserId(user.id)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  selectedUserId === user.id
                    ? "bg-sky-600/20 border border-sky-500/30"
                    : "bg-slate-800/20 hover:bg-slate-700/50 border border-slate-700/30"
                }`}
              >
                <p className="text-sm font-medium text-white">{user.email}</p>
                <p className="text-xs text-slate-500">{user.role}</p>
              </button>
            ))
          )}
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={isPending}
            className="flex-1 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleReassign}
            disabled={!selectedUserId || isPending}
            className="flex-1 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-sm font-medium transition-colors disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isPending ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Moviendo...
              </>
            ) : (
              "Mover Conversación"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

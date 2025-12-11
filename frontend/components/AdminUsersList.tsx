"use client";

import { useState } from "react";
import { useAdminUsers, AdminUser } from "@/hooks/useAdmin";
import CreateUserModal from "./CreateUserModal";

interface AdminUsersListProps {
  selectedId?: number | null;
  onSelect: (id: number) => void;
}

export default function AdminUsersList({ selectedId, onSelect }: AdminUsersListProps) {
  const { data: users = [], isLoading, error } = useAdminUsers();
  const [showCreateModal, setShowCreateModal] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-sm text-slate-500">Cargando usuarios...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-sm text-red-400">Error al cargar usuarios</div>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {/* Create User Button */}
        <button
          onClick={() => setShowCreateModal(true)}
          className="w-full px-3 py-2.5 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 rounded-lg text-white font-semibold transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-sky-500/50"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
          Nuevo Usuario
        </button>

        {/* Users List */}
        <div className="space-y-1 max-h-80 overflow-y-auto">
          {users.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-4">Sin usuarios</p>
          ) : (
            users.map((user: AdminUser) => (
              <button
                key={user.id}
                onClick={() => onSelect(user.id)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  selectedId === user.id
                    ? "bg-sky-600/20 border border-sky-500/30"
                    : "bg-slate-800/20 hover:bg-slate-700/50 border border-transparent"
                }`}
              >
                <p className="text-sm text-white truncate font-medium">{user.email}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    user.active ? "bg-green-900/40 text-green-300" : "bg-red-900/40 text-red-300"
                  }`}>
                    {user.active ? "Activo" : "Inactivo"}
                  </span>
                  <span className="text-xs text-slate-500 bg-slate-800/50 px-2 py-0.5 rounded capitalize">
                    {user.role}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
          }}
        />
      )}
    </>
  );
}

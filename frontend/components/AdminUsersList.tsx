"use client";

import { useAdminUsers, AdminUser } from "@/hooks/useAdmin";

interface AdminUsersListProps {
  selectedId?: number | null;
  onSelect: (id: number) => void;
}

export default function AdminUsersList({ selectedId, onSelect }: AdminUsersListProps) {
  const { data: users = [], isLoading, error } = useAdminUsers();

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
    <div className="space-y-1 max-h-96 overflow-y-auto">
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
  );
}

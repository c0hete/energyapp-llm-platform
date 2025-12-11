"use client";

import { useState } from "react";
import { useAuditLogs, AuditLog } from "@/hooks/useAdmin";

export default function AuditLogsViewer() {
  const [filters, setFilters] = useState({
    action: "",
    user_email: "",
    status: "",
    limit: 50,
    offset: 0,
  });

  const { data: logs = [], isLoading, error } = useAuditLogs(filters);

  // Parse meta_data safely
  const parseMetadata = (meta_data: string | null) => {
    if (!meta_data) return null;
    try {
      return JSON.parse(meta_data);
    } catch {
      return null;
    }
  };

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString("es-CL", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-900/40 text-green-300 border-green-800";
      case "failed":
        return "bg-red-900/40 text-red-300 border-red-800";
      case "blocked":
        return "bg-yellow-900/40 text-yellow-300 border-yellow-800";
      default:
        return "bg-slate-800/50 text-slate-300 border-slate-700";
    }
  };

  // Action icon
  const getActionIcon = (action: string) => {
    if (action.includes("login")) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
        </svg>
      );
    }
    if (action.includes("logout")) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
      );
    }
    if (action.includes("user_created") || action.includes("user_updated") || action.includes("user_deleted")) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      );
    }
    if (action.includes("conversation")) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-slate-500">Cargando logs...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-red-400">Error al cargar logs de auditoría</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4 bg-slate-800/30 border border-slate-700 rounded-xl">
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">
            Acción
          </label>
          <input
            type="text"
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value, offset: 0 })}
            placeholder="login_success, user_created..."
            className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">
            Email de usuario
          </label>
          <input
            type="text"
            value={filters.user_email}
            onChange={(e) => setFilters({ ...filters, user_email: e.target.value, offset: 0 })}
            placeholder="usuario@ejemplo.com"
            className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">
            Estado
          </label>
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value, offset: 0 })}
            className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Todos</option>
            <option value="success">Éxito</option>
            <option value="failed">Fallido</option>
            <option value="blocked">Bloqueado</option>
          </select>
        </div>
      </div>

      {/* Logs List */}
      <div className="space-y-2">
        {logs.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-sm text-slate-500">No hay logs que mostrar</p>
          </div>
        ) : (
          logs.map((log: AuditLog) => {
            const metadata = parseMetadata(log.meta_data);
            return (
              <div
                key={log.id}
                className="p-4 bg-slate-800/20 border border-slate-700/50 rounded-xl hover:bg-slate-800/40 transition-colors"
              >
                <div className="flex items-start gap-3">
                  {/* Icon */}
                  <div className="mt-0.5 text-sky-400">
                    {getActionIcon(log.action)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-white">
                        {log.action.replace(/_/g, " ").toUpperCase()}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(log.status)}`}>
                        {log.status}
                      </span>
                      {log.user_role && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800/50 text-slate-400 border border-slate-700">
                          {log.user_role}
                        </span>
                      )}
                    </div>

                    <div className="mt-1 space-y-1">
                      {log.user_email && (
                        <p className="text-xs text-slate-400">
                          <span className="font-medium">Usuario:</span> {log.user_email}
                        </p>
                      )}
                      {log.resource_type && (
                        <p className="text-xs text-slate-400">
                          <span className="font-medium">Recurso:</span> {log.resource_type}
                          {log.resource_id && ` #${log.resource_id}`}
                        </p>
                      )}
                      {log.ip_address && (
                        <p className="text-xs text-slate-400">
                          <span className="font-medium">IP:</span> {log.ip_address}
                        </p>
                      )}
                      {log.error_message && (
                        <p className="text-xs text-red-400">
                          <span className="font-medium">Error:</span> {log.error_message}
                        </p>
                      )}
                      {metadata && (
                        <details className="mt-2">
                          <summary className="text-xs text-sky-400 cursor-pointer hover:text-sky-300">
                            Ver metadata
                          </summary>
                          <pre className="mt-2 p-2 bg-slate-900/50 border border-slate-700 rounded text-xs text-slate-300 overflow-x-auto">
                            {JSON.stringify(metadata, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>

                    <p className="mt-2 text-xs text-slate-500">
                      {formatDate(log.created_at)}
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between p-3 bg-slate-800/20 border border-slate-700 rounded-xl">
        <button
          onClick={() => setFilters({ ...filters, offset: Math.max(0, filters.offset - filters.limit) })}
          disabled={filters.offset === 0}
          className="px-3 py-1.5 text-sm bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
        >
          Anterior
        </button>
        <span className="text-xs text-slate-400">
          Mostrando {filters.offset + 1} - {filters.offset + logs.length}
        </span>
        <button
          onClick={() => setFilters({ ...filters, offset: filters.offset + filters.limit })}
          disabled={logs.length < filters.limit}
          className="px-3 py-1.5 text-sm bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
        >
          Siguiente
        </button>
      </div>
    </div>
  );
}

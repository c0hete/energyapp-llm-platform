"use client";

import { useAuthCheck } from "@/hooks/useAuthCheck";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import ConversationsList from "@/components/ConversationsList";
import ChatWindow from "@/components/ChatWindow";
import EngineStatusBar from "@/components/EngineStatusBar";
import ToolCallingDebugPanel from "@/components/ToolCallingDebugPanel";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, loading } = useAuthCheck();
  const [selectedConvId, setSelectedConvId] = useState<number | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-950">
        <p className="text-slate-400">Cargando...</p>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  async function handleLogout() {
    try {
      // Limpiar todo el cache de React Query PRIMERO
      await queryClient.cancelQueries();
      queryClient.clear();

      // Limpiar las cookies del cliente
      document.cookie.split(";").forEach((c) => {
        const eqPos = c.indexOf("=");
        const name = eqPos > -1 ? c.substring(0, eqPos).trim() : c.trim();
        if (name) {
          document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
        }
      });

      // Luego llamar al logout en el servidor
      await api.auth.logout();
    } catch (error) {
      console.error("Logout error (non-critical):", error);
      // Continuar con redirección incluso si hay error
    } finally {
      // SIEMPRE redirigir a login
      router.push("/login");
    }
  }

  return (
    <main className="h-screen flex flex-col bg-slate-950 overflow-hidden">
      <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between bg-slate-900/50 backdrop-blur">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-1 hover:bg-slate-800 rounded"
          >
            <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <img src="/logo.png" alt="EnergyApp Logo" className="w-8 h-8 rounded-md object-contain" />
            <h1 className="text-lg font-semibold text-white">EnergyApp</h1>
          </button>
        </div>
        <div className="flex items-center gap-4">
          <EngineStatusBar />
          <span className="text-xs text-slate-400 hidden sm:inline">
            {user.email} · {user.role}
          </span>
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2m0 7a1 1 0 110-2 1 1 0 010 2m0 7a1 1 0 110-2 1 1 0 010 2" />
              </svg>
            </button>
            {menuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-50">
                <button
                  onClick={() => {
                    router.push("/settings");
                    setMenuOpen(false);
                  }}
                  className="w-full text-left px-4 py-3 text-sm text-slate-300 hover:bg-slate-700 hover:text-white first:rounded-t-lg transition-colors flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Configuración
                </button>
                {user.role === "admin" && (
                  <button
                    onClick={() => {
                      router.push("/admin");
                      setMenuOpen(false);
                    }}
                    className="w-full text-left px-4 py-3 text-sm text-purple-400 hover:bg-slate-700 hover:text-purple-300 transition-colors flex items-center gap-2 border-t border-slate-700"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Panel Admin
                  </button>
                )}
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-slate-700 hover:text-red-300 last:rounded-b-lg transition-colors flex items-center gap-2 border-t border-slate-700"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Cerrar Sesión
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden h-full">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? "w-72" : "w-0"
          } border-r border-slate-800 p-4 bg-slate-900/30 overflow-hidden flex flex-col transition-all duration-300 lg:w-72`}
        >
          {/* Header sticky */}
          <div className="mb-4 flex items-center justify-between flex-shrink-0 sticky top-0 bg-slate-900/30 backdrop-blur-sm z-10 pb-2">
            <p className="text-sm text-slate-400 font-semibold">Conversaciones</p>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 hover:bg-slate-800 rounded"
            >
              <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Scrollable conversations list */}
          <div className="flex-1 overflow-y-auto mb-4 min-h-0">
            <ConversationsList selectedId={selectedConvId} onSelect={setSelectedConvId} />
          </div>

          {/* Debug panel fixed at bottom */}
          <div className="flex-shrink-0 border-t border-slate-700/50 pt-4">
            <ToolCallingDebugPanel />
          </div>
        </aside>

        {/* Main Chat Area */}
        <section className="flex-1 flex flex-col bg-slate-950/50 overflow-hidden h-full">
          <ChatWindow conversationId={selectedConvId} />
        </section>
      </div>
    </main>
  );
}

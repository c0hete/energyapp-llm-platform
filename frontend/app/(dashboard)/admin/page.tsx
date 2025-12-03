"use client";

import { useAuthCheck } from "@/hooks/useAuthCheck";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import AdminUsersList from "@/components/AdminUsersList";
import AdminConversationsList from "@/components/AdminConversationsList";
import AdminMessagesViewer from "@/components/AdminMessagesViewer";
import SystemPromptsManager from "@/components/SystemPromptsManager";
import { api } from "@/lib/api";

type AdminTab = "users" | "prompts";

export default function AdminPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, loading } = useAuthCheck();
  const [activeTab, setActiveTab] = useState<AdminTab>("users");
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedConvId, setSelectedConvId] = useState<number | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (!loading && user && user.role !== "admin") {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

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

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-950">
        <p className="text-slate-400">Cargando...</p>
      </main>
    );
  }

  if (!user || user.role !== "admin") {
    return null;
  }

  return (
    <main className="min-h-screen flex flex-col bg-slate-950">
      <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between bg-slate-900/50 backdrop-blur">
        <h1 className="text-lg font-semibold text-white">Admin Panel</h1>
        <div className="flex items-center gap-4">
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

      {/* Tabs */}
      <div className="border-b border-slate-800 bg-slate-900/30 px-6 flex gap-2">
        <button
          onClick={() => {
            setActiveTab("users");
            setSelectedUserId(null);
            setSelectedConvId(null);
          }}
          className={`px-6 py-4 text-base font-semibold border-b-2 transition-colors ${
            activeTab === "users"
              ? "border-sky-500 text-sky-300"
              : "border-transparent text-slate-400 hover:text-slate-300"
          }`}
        >
          👥 Usuarios & Conversaciones
        </button>
        <button
          onClick={() => setActiveTab("prompts")}
          className={`px-6 py-4 text-base font-semibold border-b-2 transition-colors ${
            activeTab === "prompts"
              ? "border-sky-500 text-sky-300"
              : "border-transparent text-slate-400 hover:text-slate-300"
          }`}
        >
          ⚙️ System Prompts
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {activeTab === "users" ? (
          <>
            {/* Usuarios */}
            <aside className="w-64 border-r border-slate-800 p-4 bg-slate-900/30 overflow-y-auto">
              <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 12H9m6 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Usuarios ({selectedUserId ? "1 seleccionado" : "ninguno"})
              </h2>
              <AdminUsersList selectedId={selectedUserId} onSelect={(id) => {
                setSelectedUserId(id);
                setSelectedConvId(null);
              }} />
            </aside>

            {/* Conversaciones */}
            <aside className="w-64 border-r border-slate-800 p-4 bg-slate-900/20 overflow-y-auto">
              <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Conversaciones
              </h2>
              <AdminConversationsList
                userId={selectedUserId}
                selectedId={selectedConvId}
                onSelect={setSelectedConvId}
              />
            </aside>

            {/* Mensajes */}
            <section className="flex-1 flex flex-col overflow-hidden bg-slate-950/50">
              <div className="shrink-0 p-4 border-b border-slate-800 bg-slate-900/30">
                <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                  </svg>
                  Mensajes
                </h2>
              </div>
              <AdminMessagesViewer conversationId={selectedConvId} />
            </section>
          </>
        ) : (
          /* System Prompts */
          <section className="flex-1 flex flex-col p-6">
            <SystemPromptsManager />
          </section>
        )}
      </div>
    </main>
  );
}

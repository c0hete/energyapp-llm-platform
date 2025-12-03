"use client";

import { useAuthCheck } from "@/hooks/useAuthCheck";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import AdminUsersList from "@/components/AdminUsersList";
import AdminConversationsList from "@/components/AdminConversationsList";
import AdminMessagesViewer from "@/components/AdminMessagesViewer";
import SystemPromptsManager from "@/components/SystemPromptsManager";

type AdminTab = "users" | "prompts";

export default function AdminPage() {
  const router = useRouter();
  const { user, loading } = useAuthCheck();
  const [activeTab, setActiveTab] = useState<AdminTab>("users");
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedConvId, setSelectedConvId] = useState<number | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (!loading && user && user.role !== "admin") {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

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
        <span className="text-xs text-slate-400">{user.email}</span>
      </header>

      {/* Tabs */}
      <div className="border-b border-slate-800 bg-slate-900/30 px-6 flex gap-1">
        <button
          onClick={() => {
            setActiveTab("users");
            setSelectedUserId(null);
            setSelectedConvId(null);
          }}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "users"
              ? "border-sky-500 text-sky-300"
              : "border-transparent text-slate-400 hover:text-slate-300"
          }`}
        >
          Usuarios & Conversaciones
        </button>
        <button
          onClick={() => setActiveTab("prompts")}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "prompts"
              ? "border-sky-500 text-sky-300"
              : "border-transparent text-slate-400 hover:text-slate-300"
          }`}
        >
          System Prompts
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
            <section className="flex-1 flex flex-col bg-slate-950/50">
              <div className="p-4 border-b border-slate-800 bg-slate-900/30">
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

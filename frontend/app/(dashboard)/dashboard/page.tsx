"use client";

import { useAuthCheck } from "@/hooks/useAuthCheck";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import ConversationsList from "@/components/ConversationsList";
import ChatWindow from "@/components/ChatWindow";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuthCheck();
  const [selectedConvId, setSelectedConvId] = useState<number | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

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

  return (
    <main className="min-h-screen flex flex-col bg-slate-950">
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
          <h1 className="text-lg font-semibold text-white">EnergyApp</h1>
        </div>
        <span className="text-xs text-slate-400">
          {user.email} · {user.role}
        </span>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? "w-72" : "w-0"
          } border-r border-slate-800 p-4 bg-slate-900/30 overflow-y-auto transition-all duration-300 lg:w-72`}
        >
          <div className="mb-4 flex items-center justify-between">
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
          <ConversationsList selectedId={selectedConvId} onSelect={setSelectedConvId} />
        </aside>

        {/* Main Chat Area */}
        <section className="flex-1 flex flex-col bg-slate-950/50">
          <ChatWindow conversationId={selectedConvId} />
        </section>
      </div>
    </main>
  );
}

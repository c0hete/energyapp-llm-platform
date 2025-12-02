"use client";

import { useAuthCheck } from "@/hooks/useAuthCheck";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuthCheck();

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
        <h1 className="text-lg font-semibold text-white">EnergyApp Dashboard</h1>
        <span className="text-xs text-slate-400">
          {user.email} · {user.role}
        </span>
      </header>

      <div className="flex flex-1">
        <aside className="w-72 border-r border-slate-800 p-4 bg-slate-900/30">
          <p className="text-sm text-slate-400 mb-4 font-semibold">
            Conversaciones
          </p>
          <div className="text-xs text-slate-500 bg-slate-900/50 rounded p-4 text-center">
            Aquí irá la lista de conversaciones (React Query - FASE 2)
          </div>
        </aside>

        <section className="flex-1 p-4 flex flex-col">
          <div className="flex-1 border border-dashed border-slate-700 rounded-xl flex items-center justify-center bg-slate-900/20">
            <p className="text-sm text-slate-500">
              Aquí irá el chat con streaming (FASE 2)
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

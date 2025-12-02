"use client";

import { useAuthCheck } from "@/hooks/useAuthCheck";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AdminPage() {
  const router = useRouter();
  const { user, loading } = useAuthCheck();

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
      <header className="border-b border-slate-800 px-6 py-3 bg-slate-900/50 backdrop-blur">
        <h1 className="text-lg font-semibold text-white">
          Admin Panel
        </h1>
      </header>

      <div className="p-6 grid grid-cols-4 gap-4">
        <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/30">
          <h3 className="font-semibold text-white mb-4">Usuarios</h3>
          <p className="text-xs text-slate-500">
            Aquí irá la lista de usuarios (React Query - FASE 3)
          </p>
        </div>

        <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/30">
          <h3 className="font-semibold text-white mb-4">Conversaciones</h3>
          <p className="text-xs text-slate-500">
            Conversaciones del usuario seleccionado (FASE 3)
          </p>
        </div>

        <div className="col-span-2 border border-slate-700 rounded-lg p-4 bg-slate-900/30">
          <h3 className="font-semibold text-white mb-4">Mensajes</h3>
          <p className="text-xs text-slate-500">
            Visor de mensajes de la conversación seleccionada (FASE 3)
          </p>
        </div>
      </div>
    </main>
  );
}

"use client";

import Link from "next/link";

export default function RegisterPage() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-8 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="w-full max-w-md">
        {/* Logo Section */}
        <div className="mb-8">
          <div className="flex items-center justify-center mb-4">
            <img
              src="/logo.png"
              alt="EnergyApp Logo"
              className="w-16 h-16 object-contain"
            />
          </div>
          <h1 className="text-3xl font-bold text-center text-white">EnergyApp</h1>
          <p className="text-center text-slate-400 text-sm mt-2">Chat LLM con Qwen 2.5:3B</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900/80 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">Registro</h2>
            <p className="text-sm text-slate-400">Crea una nueva cuenta para acceder</p>
          </div>

          {/* Coming Soon Message */}
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-amber-950/40 border border-amber-900/70 flex items-start gap-3">
              <div className="text-amber-400 mt-0.5 flex-shrink-0">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-amber-400 mb-1">Funcionalidad en desarrollo</h3>
                <p className="text-xs text-amber-300/80">Por ahora, solo los administradores pueden crear nuevas cuentas. Esta funcionalidad estará disponible próximamente.</p>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
              <p className="text-xs text-slate-400 mb-3 font-medium">¿Ya tienes cuenta?</p>
              <Link
                href="/login"
                className="w-full inline-block text-center rounded-lg bg-sky-600 hover:bg-sky-500 py-2.5 text-sm font-semibold text-white transition-colors"
              >
                Ir a Login
              </Link>
            </div>

            {/* Admin Contact */}
            <div className="p-4 rounded-lg bg-slate-700/20 border border-slate-600/30">
              <p className="text-xs text-slate-400">
                Para solicitar una cuenta, contacta a un <span className="text-slate-300 font-medium">administrador</span>.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-600 mt-8">
          Versión 1.0 · FASE 1 · <span className="text-slate-500">2025</span>
        </p>
      </div>
    </main>
  );
}

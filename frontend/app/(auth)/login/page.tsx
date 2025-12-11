"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

interface FormErrors {
  email?: string;
  password?: string;
  submit?: string;
}

export default function LoginPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState({ email: false, password: false });

  function validateForm(): FormErrors {
    const newErrors: FormErrors = {};

    if (!email) {
      newErrors.email = "Email es requerido";
    } else if (!email.includes("@")) {
      newErrors.email = "Email inválido";
    }

    if (!password) {
      newErrors.password = "Contraseña es requerida";
    } else if (password.length < 6) {
      newErrors.password = "Contraseña debe tener al menos 6 caracteres";
    }

    return newErrors;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErrors({});

    const newErrors = validateForm();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);

    try {
      await api.auth.login(email, password);
      const me = await api.auth.me();
      setUser(me);
      queryClient.invalidateQueries({ queryKey: ["auth"] });
      router.push("/dashboard");
    } catch (err: any) {
      const errorMsg = err.message || "Error al iniciar sesión";
      setErrors({ submit: errorMsg });
    } finally {
      setLoading(false);
    }
  }

  function handleBlur(field: "email" | "password") {
    setTouched({ ...touched, [field]: true });
  }

  const emailError = touched.email && errors.email;
  const passwordError = touched.password && errors.password;

  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-8 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="w-full max-w-md">
        {/* Logo Section */}
        <div className="mb-8">
          <div className="flex items-center justify-center mb-4">
            <img src="/logo.png" alt="EnergyApp Logo" className="w-16 h-16 rounded-xl object-contain" />
          </div>
          <h1 className="text-3xl font-bold text-center text-white">EnergyApp</h1>
          <p className="text-center text-slate-400 text-sm mt-2">Chat LLM con Qwen 2.5:3B</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900/80 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
          {errors.submit && (
            <div className="mb-6 p-4 rounded-lg bg-red-950/40 border border-red-900/70 flex items-start gap-3">
              <div className="text-red-400 mt-0.5">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm text-red-400">{errors.submit}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => handleBlur("email")}
                autoComplete="email"
                placeholder="tu@email.com"
                className={`w-full rounded-lg border transition-all px-4 py-2.5 text-sm bg-slate-950 text-white placeholder-slate-500 outline-none ${
                  emailError
                    ? "border-red-500/50 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
                    : "border-slate-700 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                }`}
              />
              {emailError && (
                <p className="mt-1.5 text-xs text-red-400">{errors.email}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={() => handleBlur("password")}
                autoComplete="current-password"
                placeholder="••••••••"
                className={`w-full rounded-lg border transition-all px-4 py-2.5 text-sm bg-slate-950 text-white placeholder-slate-500 outline-none ${
                  passwordError
                    ? "border-red-500/50 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
                    : "border-slate-700 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                }`}
              />
              {passwordError && (
                <p className="mt-1.5 text-xs text-red-400">{errors.password}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-[var(--accent)] hover:bg-[var(--accent-strong)] disabled:opacity-50 disabled:cursor-not-allowed py-2.5 text-sm font-semibold text-white transition-colors duration-200 flex items-center justify-center gap-2"
            >
              {loading && (
                <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              )}
              <span>{loading ? "Ingresando..." : "Entrar"}</span>
            </button>
          </form>

          {/* Demo Credentials */}
          <div className="mt-6 p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <p className="text-xs text-slate-400 mb-2 font-medium">Credenciales de demostración:</p>
            <div className="space-y-1 text-xs text-slate-500 font-mono">
              <p>📧 <span className="text-slate-400">administrador@alvaradomazzei.cl</span></p>
              <p>🔑 <span className="text-slate-400">admin123</span></p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-600 mt-8">
          Versión 1.0 · MIT License · © 2025 <span className="text-slate-500">José Alvarado Mazzei</span>
        </p>
      </div>
    </main>
  );
}

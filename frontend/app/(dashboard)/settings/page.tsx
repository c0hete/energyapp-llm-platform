"use client";

import { useAuthCheck } from "@/hooks/useAuthCheck";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface TabType {
  id: string;
  label: string;
}

const tabs: TabType[] = [
  { id: "account", label: "Cuenta" },
  { id: "security", label: "Seguridad" },
];

export default function SettingsPage() {
  const router = useRouter();
  const { user, loading } = useAuthCheck();
  const [activeTab, setActiveTab] = useState("account");

  // Password change state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);

  // 2FA state
  const [twoFAQR, setTwoFAQR] = useState<string | null>(null);
  const [twoFASecret, setTwoFASecret] = useState<string | null>(null);
  const [twoFALoading, setTwoFALoading] = useState(false);
  const [showTwoFASetup, setShowTwoFASetup] = useState(false);
  const [twoFAMessage, setTwoFAMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: "error", text: "Las contraseñas no coinciden" });
      return;
    }

    if (newPassword.length < 8) {
      setPasswordMessage({ type: "error", text: "La contraseña debe tener al menos 8 caracteres" });
      return;
    }

    setPasswordLoading(true);
    try {
      await api.auth.changePassword(currentPassword, newPassword);
      setPasswordMessage({ type: "success", text: "Contraseña actualizada exitosamente" });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error: any) {
      setPasswordMessage({
        type: "error",
        text: error.message || "Error al cambiar la contraseña",
      });
    } finally {
      setPasswordLoading(false);
    }
  }

  async function handleSetup2FA() {
    setTwoFALoading(true);
    try {
      const response = await api.auth.setup2fa();
      setTwoFAQR(response.qr_code);
      setTwoFASecret(response.secret);
      setShowTwoFASetup(true);
      setTwoFAMessage(null);
    } catch (error: any) {
      setTwoFAMessage({
        type: "error",
        text: error.message || "Error al configurar 2FA",
      });
    } finally {
      setTwoFALoading(false);
    }
  }

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

  const isInacapUser = user.email.endsWith("@inacapmail.cl");

  return (
    <main className="min-h-screen flex flex-col bg-slate-950">
      <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between bg-slate-900/50 backdrop-blur">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="p-1 hover:bg-slate-800 rounded"
          >
            <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="text-lg font-semibold text-white">Configuración</h1>
        </div>
        <span className="text-xs text-slate-400">
          {user.email} · {user.role}
        </span>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <div className="w-full max-w-4xl mx-auto flex flex-col">
          {/* Tabs */}
          <div className="border-b border-slate-800 px-6 flex gap-4 bg-slate-900/30">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "text-sky-400 border-sky-500"
                    : "text-slate-400 border-transparent hover:text-slate-300"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === "account" && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-white mb-4">Información de Cuenta</h2>
                  <div className="space-y-4 bg-slate-900/30 border border-slate-800 rounded-lg p-6">
                    <div>
                      <label className="text-sm text-slate-400">Email</label>
                      <p className="text-white mt-1">{user.email}</p>
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">Rol</label>
                      <p className="text-white mt-1 capitalize">{user.role}</p>
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">Estado</label>
                      <p className="text-white mt-1">{user.active ? "Activo" : "Inactivo"}</p>
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">Creado el</label>
                      <p className="text-white mt-1">{new Date(user.created_at).toLocaleDateString("es-CL")}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "security" && (
              <div className="space-y-6">
                {/* Change Password */}
                {isInacapUser && (
                  <div>
                    <h2 className="text-xl font-semibold text-white mb-4">Cambiar Contraseña</h2>
                    <form onSubmit={handleChangePassword} className="bg-slate-900/30 border border-slate-800 rounded-lg p-6 max-w-md">
                      <div className="space-y-4">
                        <div>
                          <label htmlFor="current-password" className="block text-sm text-slate-400 mb-2">
                            Contraseña Actual
                          </label>
                          <input
                            id="current-password"
                            type="password"
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                            required
                            className="w-full px-4 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                            placeholder="Tu contraseña actual"
                          />
                        </div>

                        <div>
                          <label htmlFor="new-password" className="block text-sm text-slate-400 mb-2">
                            Nueva Contraseña
                          </label>
                          <input
                            id="new-password"
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            required
                            className="w-full px-4 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                            placeholder="Nueva contraseña"
                          />
                        </div>

                        <div>
                          <label htmlFor="confirm-password" className="block text-sm text-slate-400 mb-2">
                            Confirmar Contraseña
                          </label>
                          <input
                            id="confirm-password"
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                            className="w-full px-4 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                            placeholder="Confirma tu nueva contraseña"
                          />
                        </div>

                        {passwordMessage && (
                          <div
                            className={`p-3 rounded-lg text-sm ${
                              passwordMessage.type === "success"
                                ? "bg-green-900/30 border border-green-700 text-green-400"
                                : "bg-red-900/30 border border-red-700 text-red-400"
                            }`}
                          >
                            {passwordMessage.text}
                          </div>
                        )}

                        <button
                          type="submit"
                          disabled={passwordLoading || !currentPassword || !newPassword || !confirmPassword}
                          className="w-full px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors"
                        >
                          {passwordLoading ? "Actualizando..." : "Actualizar Contraseña"}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Two-Factor Authentication */}
                {isInacapUser && (
                  <div>
                    <h2 className="text-xl font-semibold text-white mb-4">Autenticación de Dos Factores</h2>
                    <div className="bg-slate-900/30 border border-slate-800 rounded-lg p-6 max-w-md">
                      {!showTwoFASetup ? (
                        <>
                          <p className="text-slate-300 text-sm mb-4">
                            Mejora la seguridad de tu cuenta activando autenticación de dos factores.
                          </p>
                          {twoFAMessage && (
                            <div
                              className={`p-3 rounded-lg text-sm mb-4 ${
                                twoFAMessage.type === "success"
                                  ? "bg-green-900/30 border border-green-700 text-green-400"
                                  : "bg-red-900/30 border border-red-700 text-red-400"
                              }`}
                            >
                              {twoFAMessage.text}
                            </div>
                          )}
                          <button
                            onClick={handleSetup2FA}
                            disabled={twoFALoading}
                            className="w-full px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors"
                          >
                            {twoFALoading ? "Cargando..." : "Configurar 2FA"}
                          </button>
                        </>
                      ) : (
                        <div className="space-y-4">
                          <p className="text-slate-300 text-sm">
                            Escanea este código QR con tu aplicación de autenticación:
                          </p>
                          {twoFAQR && (
                            <div className="flex justify-center">
                              <img
                                src={twoFAQR}
                                alt="QR Code"
                                className="w-48 h-48 bg-white p-2 rounded-lg"
                              />
                            </div>
                          )}
                          {twoFASecret && (
                            <div className="bg-slate-950 border border-slate-700 rounded p-3">
                              <p className="text-xs text-slate-400 mb-1">Código manual (si es necesario):</p>
                              <code className="text-sm text-sky-400 font-mono break-all">{twoFASecret}</code>
                            </div>
                          )}
                          <button
                            onClick={() => setShowTwoFASetup(false)}
                            className="w-full px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-medium text-sm transition-colors"
                          >
                            Cerrar
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {!isInacapUser && (
                  <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                    <p className="text-blue-400 text-sm">
                      Las opciones de seguridad avanzada están disponibles solo para cuentas @inacapmail.cl
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

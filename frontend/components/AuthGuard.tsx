"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

const PUBLIC_ROUTES = ["/login", "/register"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, setUser, clearUser } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    async function checkAuth() {
      // Si estamos en una ruta pública, no validar
      if (PUBLIC_ROUTES.includes(pathname)) {
        setIsChecking(false);
        return;
      }

      try {
        // Validar sesión con el backend
        const userData = await api.auth.me();
        setUser(userData);
        setIsChecking(false);
      } catch (error) {
        // Sesión inválida, redirigir a login
        clearUser();
        router.push("/login");
      }
    }

    checkAuth();
  }, [pathname, router, setUser, clearUser]);

  // Mostrar loading mientras valida
  if (isChecking && !PUBLIC_ROUTES.includes(pathname)) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-sky-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Verificando sesión...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

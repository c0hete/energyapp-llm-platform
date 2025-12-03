import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/useAuthStore";
import { ApiError } from "@/lib/api";

/**
 * Hook que limpia sesión cuando hay error 401
 * Se usa en handlers de errores de React Query
 */
export function useSessionErrorHandler() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { clearSession } = useAuthStore();

  const handleSessionExpired = async () => {
    // Limpiar todo
    await queryClient.cancelQueries();
    queryClient.clear();
    clearSession();

    // Redirigir a login
    router.push("/login");
  };

  const isSessionError = (error: unknown): boolean => {
    return error instanceof ApiError && error.status === 401;
  };

  return {
    handleSessionExpired,
    isSessionError,
  };
}

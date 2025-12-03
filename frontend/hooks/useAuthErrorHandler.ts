import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function useAuthErrorHandler(error: Error | null) {
  const router = useRouter();

  useEffect(() => {
    if (error && "status" in error && error.status === 401) {
      // Sesión expirada o no autorizado
      router.push("/login");
    }
  }, [error, router]);
}

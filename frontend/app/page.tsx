"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuthCheck } from "@/hooks/useAuthCheck";

export default function Home() {
  const router = useRouter();
  const { user, loading } = useAuthCheck();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!loading && mounted) {
      if (user) {
        router.push("/dashboard");
      } else {
        router.push("/login");
      }
    }
  }, [user, loading, mounted, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="text-slate-400">Cargando...</div>
    </div>
  );
}

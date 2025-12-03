"use client";

import { useEffect } from "react";
import { initializeChunkErrorHandler } from "@/lib/chunkErrorHandler";

export function ErrorBoundaryProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Inicializar manejador de errores de chunks
    initializeChunkErrorHandler();
  }, []);

  return children;
}

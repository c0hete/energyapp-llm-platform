"use client";

import { ReactNode } from "react";

/**
 * Provider que proporciona contexto para manejo de errores de sesión
 * Los hooks de sesión pueden ser usados dentro de este provider
 */
export function SessionErrorProvider({ children }: { children: ReactNode }) {
  return children;
}

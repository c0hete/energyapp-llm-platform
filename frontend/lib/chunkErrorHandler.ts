/**
 * Inicializa el manejador de errores de chunks fallidos
 * Limpia cache y redirige a login si un chunk no puede cargarse
 */
export function initializeChunkErrorHandler() {
  if (typeof window === "undefined") return;

  const originalError = window.onerror;

  window.onerror = (msg, url, lineNo, colNo, error) => {
    const message = msg?.toString() || "";

    // Detectar errores de chunks no encontrados
    if (
      message.includes("Failed to load") ||
      message.includes("chunk") ||
      (error?.message && error.message.includes("Failed to load"))
    ) {
      console.warn("🚨 Chunk fallido detectado, limpiando cache...");

      // Limpiar todos los caches
      localStorage.clear();
      sessionStorage.clear();

      // Limpiar cookies
      document.cookie.split(";").forEach((c) => {
        const eqPos = c.indexOf("=");
        const name = eqPos > -1 ? c.substring(0, eqPos).trim() : c.trim();
        if (name) {
          document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
        }
      });

      // Redirigir a login sin errores
      window.location.href = "/login";

      return true; // Prevenir comportamiento por defecto
    }

    // Llamar al handler original si existe
    if (originalError) {
      return originalError(msg, url, lineNo, colNo, error);
    }

    return false;
  };

  // También manejar errores de recursos (chunks)
  window.addEventListener("error", (event) => {
    if (event.target && event.target instanceof HTMLScriptElement) {
      const script = event.target as HTMLScriptElement;
      if (script.src && script.src.includes("_next")) {
        console.warn("🚨 Script de chunk fallido:", script.src);
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = "/login";
      }
    }
  });
}

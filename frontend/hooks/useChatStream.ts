import { useState, useCallback } from "react";
import { api } from "@/lib/api";

// Helper to add debug events
function addDebugEvent(type: string, message: string, data?: any) {
  if (typeof window !== "undefined" && (window as any).__addDebugEvent) {
    (window as any).__addDebugEvent(type, message, data);
  }
}

export function useChatStream() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(
    async (
      conversationId: number | null,
      prompt: string,
      system?: string,
      onChunk?: (chunk: string) => void,
      promptId?: number | null
    ): Promise<string> => {
      setLoading(true);
      setError(null);

      let fullResponse = "";

      try {
        // Event 1: User sends request
        addDebugEvent("request", "Enviando pregunta...", { prompt: prompt.substring(0, 50) + "..." });

        // Event 2: Calling FastAPI
        addDebugEvent("fastapi", "Conectando con FastAPI...");

        const response = await api.chat.send(conversationId, prompt, system, promptId);

        if (!response.ok) {
          addDebugEvent("error", `Error HTTP ${response.status}`, { status: response.status });
          throw new Error(`Chat failed: ${response.status}`);
        }

        // Event 3: FastAPI received, Ollama processing
        addDebugEvent("ollama", "Ollama está procesando...");

        const reader = response.body?.getReader();
        if (!reader) {
          addDebugEvent("error", "No se recibió respuesta del servidor");
          throw new Error("No response body");
        }

        // Event 4: Checking if tools are needed
        addDebugEvent("tools_check", "Verificando si necesita herramientas...");

        const decoder = new TextDecoder();
        let isFirstChunk = true;

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          fullResponse += chunk;

          // On first chunk, assume tools check is done and response is starting
          if (isFirstChunk) {
            isFirstChunk = false;

            // Check if response contains tool calling indicators
            if (chunk.includes("search_cie10") || chunk.includes("get_cie10_code")) {
              addDebugEvent("tool_call", "Ejecutando búsqueda en CIE-10...", { tool: "search_cie10" });
              addDebugEvent("database", "Consultando base de datos...");
            } else {
              addDebugEvent("response", "Generando respuesta directa...");
            }
          }

          if (onChunk) {
            onChunk(chunk);
          }
        }

        // Event 5: Response complete
        addDebugEvent("response", "Respuesta completada ✓");

        return fullResponse;
      } catch (err: any) {
        const errorMsg = err.message || "Error enviando mensaje";
        addDebugEvent("error", errorMsg, { error: err.message });
        setError(errorMsg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { send, loading, error };
}

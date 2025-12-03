import { useState, useCallback } from "react";
import { api } from "@/lib/api";

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
        const response = await api.chat.send(conversationId, prompt, system, promptId);

        if (!response.ok) {
          throw new Error(`Chat failed: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          fullResponse += chunk;

          if (onChunk) {
            onChunk(chunk);
          }
        }

        return fullResponse;
      } catch (err: any) {
        const errorMsg = err.message || "Error enviando mensaje";
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

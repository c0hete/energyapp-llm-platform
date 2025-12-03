"use client";

import { useState } from "react";
import {
  useSystemPrompts,
  useCreatePrompt,
  useUpdatePrompt,
  useDeletePrompt,
} from "@/hooks/useSystemPrompts";

export default function SystemPromptsManager() {
  const { data: prompts = [], isLoading } = useSystemPrompts();
  const createMutation = useCreatePrompt();
  const updateMutation = useUpdatePrompt(0);
  const deleteMutation = useDeletePrompt();

  const [editingId, setEditingId] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    content: "",
    is_default: false,
  });

  const handleCreate = async () => {
    if (!formData.name.trim() || !formData.content.trim()) return;

    try {
      await createMutation.mutateAsync({
        name: formData.name,
        description: formData.description || undefined,
        content: formData.content,
        is_default: formData.is_default,
      });
      setFormData({ name: "", description: "", content: "", is_default: false });
      setShowCreate(false);
    } catch (error) {
      console.error("Error creating prompt:", error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("¿Eliminar este prompt?")) return;
    try {
      await deleteMutation.mutateAsync(id);
    } catch (error) {
      console.error("Error deleting prompt:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-sm text-slate-500">Cargando prompts...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">System Prompts</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-sm rounded-lg transition-colors"
        >
          {showCreate ? "Cancelar" : "Nuevo Prompt"}
        </button>
      </div>

      {showCreate && (
        <div className="border border-slate-700 rounded-lg p-4 bg-slate-800/30 space-y-3">
          <input
            type="text"
            placeholder="Nombre del prompt"
            value={formData.name}
            onChange={(e) =>
              setFormData({ ...formData, name: e.target.value })
            }
            maxLength={255}
            className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 text-sm"
          />
          <input
            type="text"
            placeholder="Descripción (opcional)"
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 text-sm"
          />
          <textarea
            placeholder="Contenido del prompt (mínimo 10 caracteres)"
            value={formData.content}
            onChange={(e) =>
              setFormData({ ...formData, content: e.target.value })
            }
            rows={4}
            className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 text-sm font-mono text-xs"
          />
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={formData.is_default}
              onChange={(e) =>
                setFormData({ ...formData, is_default: e.target.checked })
              }
              className="rounded"
            />
            Establecer como default
          </label>
          <button
            onClick={handleCreate}
            disabled={
              !formData.name.trim() ||
              !formData.content.trim() ||
              createMutation.isPending
            }
            className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white text-sm rounded transition-colors"
          >
            {createMutation.isPending ? "Creando..." : "Crear Prompt"}
          </button>
        </div>
      )}

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {prompts.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-8">
            Sin prompts disponibles
          </p>
        ) : (
          prompts.map((prompt: any) => (
            <div
              key={prompt.id}
              className="border border-slate-700 rounded-lg p-3 bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white truncate">
                      {prompt.name}
                    </p>
                    {prompt.is_default && (
                      <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded">
                        Default
                      </span>
                    )}
                    {!prompt.is_active && (
                      <span className="text-xs bg-red-900/50 text-red-300 px-2 py-0.5 rounded">
                        Inactivo
                      </span>
                    )}
                  </div>
                  {prompt.description && (
                    <p className="text-xs text-slate-400 mt-1 truncate">
                      {prompt.description}
                    </p>
                  )}
                  <p className="text-xs text-slate-500 mt-2 line-clamp-2">
                    {prompt.content}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(prompt.id)}
                  disabled={deleteMutation.isPending}
                  className="px-2 py-1 bg-red-900/30 hover:bg-red-900/50 text-red-300 text-xs rounded transition-colors flex-shrink-0"
                >
                  Eliminar
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

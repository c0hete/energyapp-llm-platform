"use client";

import { useState } from "react";
import {
  useSystemPrompts,
  useCreatePrompt,
  useUpdatePrompt,
  useDeletePrompt,
} from "@/hooks/useSystemPrompts";

interface SystemPrompt {
  id: number;
  name: string;
  description: string | null;
  content: string;
  is_default: boolean;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export default function SystemPromptsManager() {
  const { data: prompts = [], isLoading, error: loadError } = useSystemPrompts();
  const createMutation = useCreatePrompt();
  const deleteMutation = useDeletePrompt();

  const [editingId, setEditingId] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    content: "",
    is_default: false,
  });

  const updateMutation = useUpdatePrompt(editingId || 0);

  const handleCreate = async () => {
    if (!formData.name.trim() || !formData.content.trim()) return;

    try {
      setErrorMessage(null);
      await createMutation.mutateAsync({
        name: formData.name,
        description: formData.description || undefined,
        content: formData.content,
        is_default: formData.is_default,
      });
      setFormData({ name: "", description: "", content: "", is_default: false });
      setShowCreate(false);
    } catch (error) {
      setErrorMessage("Error al crear prompt. Intenta nuevamente.");
      console.error("Error creating prompt:", error);
    }
  };

  const handleEdit = (prompt: SystemPrompt) => {
    setEditingId(prompt.id);
    setFormData({
      name: prompt.name,
      description: prompt.description || "",
      content: prompt.content,
      is_default: prompt.is_default,
    });
    setShowCreate(false);
  };

  const handleUpdate = async () => {
    if (!formData.name.trim() || !formData.content.trim() || !editingId) return;

    try {
      setErrorMessage(null);
      await updateMutation.mutateAsync({
        name: formData.name,
        description: formData.description || undefined,
        content: formData.content,
        is_default: formData.is_default,
      });
      setEditingId(null);
      setFormData({ name: "", description: "", content: "", is_default: false });
    } catch (error) {
      setErrorMessage("Error al actualizar prompt. Intenta nuevamente.");
      console.error("Error updating prompt:", error);
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setFormData({ name: "", description: "", content: "", is_default: false });
    setErrorMessage(null);
  };

  const handleDelete = async (id: number) => {
    if (!confirm("¿Eliminar este prompt?")) return;
    try {
      setErrorMessage(null);
      await deleteMutation.mutateAsync(id);
    } catch (error) {
      setErrorMessage("Error al eliminar prompt. Intenta nuevamente.");
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

  if (loadError) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-red-400 mb-2">Error al cargar system prompts</p>
          <p className="text-slate-400 text-sm">Intenta recargar la página</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {errorMessage && (
        <div className="border border-red-500/50 bg-red-900/20 rounded-lg p-3">
          <p className="text-sm text-red-300">{errorMessage}</p>
        </div>
      )}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">System Prompts</h2>
        <button
          onClick={() => {
            if (editingId) {
              handleCancelEdit();
            } else {
              setShowCreate(!showCreate);
            }
          }}
          className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-sm rounded-lg transition-colors"
        >
          {showCreate || editingId ? "Cancelar" : "Nuevo Prompt"}
        </button>
      </div>

      {(showCreate || editingId) && (
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
            onClick={editingId ? handleUpdate : handleCreate}
            disabled={
              !formData.name.trim() ||
              !formData.content.trim() ||
              (editingId ? updateMutation.isPending : createMutation.isPending)
            }
            className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white text-sm rounded transition-colors"
          >
            {editingId
              ? updateMutation.isPending
                ? "Guardando..."
                : "Guardar Cambios"
              : createMutation.isPending
              ? "Creando..."
              : "Crear Prompt"}
          </button>
        </div>
      )}

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {prompts.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-8">
            Sin prompts disponibles
          </p>
        ) : (
          prompts.map((prompt: SystemPrompt) => (
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
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleEdit(prompt)}
                    disabled={editingId === prompt.id}
                    className="px-2 py-1 bg-blue-900/30 hover:bg-blue-900/50 text-blue-300 text-xs rounded transition-colors disabled:opacity-50"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(prompt.id)}
                    disabled={deleteMutation.isPending}
                    className="px-2 py-1 bg-red-900/30 hover:bg-red-900/50 text-red-300 text-xs rounded transition-colors"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

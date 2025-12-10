"use client";

import { useState, useEffect, useRef } from "react";

interface DebugEvent {
  timestamp: Date;
  type: "request" | "fastapi" | "ollama" | "tools_check" | "tool_call" | "database" | "response" | "error";
  message: string;
  data?: any;
}

interface ToolCallingDebugPanelProps {
  onDebugEvent?: (event: DebugEvent) => void;
}

export default function ToolCallingDebugPanel({ onDebugEvent }: ToolCallingDebugPanelProps) {
  const [events, setEvents] = useState<DebugEvent[]>([]);
  const [isExpanded, setIsExpanded] = useState(true);
  const topEventRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (onDebugEvent) {
      // This hook is called from parent when new events arrive
    }
  }, [onDebugEvent]);

  const addEvent = (type: DebugEvent["type"], message: string, data?: any) => {
    const event: DebugEvent = {
      timestamp: new Date(),
      type,
      message,
      data,
    };
    setEvents((prev) => [event, ...prev]); // Prepend new events (newest first)
  };

  const clearEvents = () => {
    setEvents([]);
  };

  // Auto-scroll to top when new event arrives
  useEffect(() => {
    if (events.length > 0 && topEventRef.current) {
      topEventRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [events]);

  const getIcon = (type: DebugEvent["type"]) => {
    switch (type) {
      case "request":
        return "📨";
      case "fastapi":
        return "⚙️";
      case "ollama":
        return "🤖";
      case "tools_check":
        return "🔍";
      case "tool_call":
        return "⚡";
      case "database":
        return "💾";
      case "response":
        return "✅";
      case "error":
        return "❌";
      default:
        return "•";
    }
  };

  const getStatusColor = (type: DebugEvent["type"]) => {
    switch (type) {
      case "request":
        return "text-blue-400";
      case "fastapi":
        return "text-purple-400";
      case "ollama":
        return "text-yellow-400";
      case "tools_check":
        return "text-cyan-400";
      case "tool_call":
        return "text-orange-400";
      case "database":
        return "text-green-400";
      case "response":
        return "text-blue-400";
      case "error":
        return "text-red-400";
      default:
        return "text-slate-400";
    }
  };

  // Expose addEvent method to parent via ref or callback
  useEffect(() => {
    if (typeof window !== "undefined") {
      (window as any).__addDebugEvent = addEvent;
    }
  }, []);

  if (!isExpanded) {
    return (
      <div className="group border border-slate-700/50 rounded-xl bg-linear-to-br from-slate-900/80 to-slate-950/80 p-3 hover:border-slate-600/50 transition-all duration-200">
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="font-medium">Sistema Activo</span>
          </div>
          <svg className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div className="border border-slate-700/50 rounded-xl bg-linear-to-br from-slate-900/80 to-slate-950/80 overflow-hidden shadow-xl shadow-slate-950/50 backdrop-blur-sm">
      {/* Header con gradiente sutil */}
      <div className="flex items-center justify-between p-3 border-b border-slate-700/50 bg-linear-to-r from-slate-800/40 to-slate-800/20">
        <div className="flex items-center gap-2.5">
          <div className="relative flex items-center">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <div className="absolute w-2 h-2 rounded-full bg-emerald-500/30 animate-ping"></div>
          </div>
          <span className="text-xs font-semibold text-slate-200 tracking-tight">Monitor del Sistema</span>
          {events.length > 0 && (
            <span className="text-[10px] text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded-full border border-slate-700/50 font-medium">
              {events.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={clearEvents}
            disabled={events.length === 0}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 rounded-lg transition-all duration-200 disabled:opacity-30 disabled:hover:bg-transparent"
            title="Limpiar eventos"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
          <button
            onClick={() => setIsExpanded(false)}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 rounded-lg transition-all duration-200"
            title="Minimizar"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Events List - Reversed order (newest at top) */}
      <div className="overflow-y-auto p-2.5 space-y-1.5 max-h-72">
        {events.length === 0 ? (
          <div className="text-center py-8">
            <div className="inline-flex items-center gap-2 text-xs text-slate-500">
              <svg className="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Esperando actividad...</span>
            </div>
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={index}
              ref={index === 0 ? topEventRef : null}
              className="group relative flex items-start gap-2.5 text-xs hover:bg-slate-800/30 p-2.5 rounded-lg transition-all duration-200 border border-transparent hover:border-slate-700/30"
            >
              {/* Icono con glow effect en eventos importantes */}
              <div className="relative shrink-0 mt-0.5">
                <span className="text-base relative z-10">{getIcon(event.type)}</span>
                {(event.type === "tool_call" || event.type === "response") && (
                  <div className="absolute inset-0 blur-md opacity-50 scale-150">
                    {getIcon(event.type)}
                  </div>
                )}
              </div>

              {/* Contenido */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`font-medium ${getStatusColor(event.type)} leading-tight`}>
                    {event.message}
                  </span>
                  <span className="text-slate-600 text-[10px] font-mono ml-auto">
                    {event.timestamp.toLocaleTimeString('es-CL', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}
                  </span>
                </div>

                {/* Data expandible con mejor diseño */}
                {event.data && (
                  <details className="mt-1.5 group/details">
                    <summary className="cursor-pointer text-[10px] text-slate-500 hover:text-slate-400 transition-colors select-none list-none flex items-center gap-1">
                      <svg className="w-3 h-3 transition-transform group-open/details:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      Ver detalles
                    </summary>
                    <pre className="mt-1.5 text-[10px] text-slate-400 bg-slate-950/80 border border-slate-800/50 p-2.5 rounded-lg overflow-x-auto scrollbar-hide font-mono leading-relaxed">
                      {JSON.stringify(event.data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>

              {/* Indicador de línea temporal para eventos recientes */}
              {index === 0 && (
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-linear-to-b from-emerald-500/50 to-transparent rounded-full"></div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Export helper function for external use
export function addDebugEvent(type: DebugEvent["type"], message: string, data?: any) {
  if (typeof window !== "undefined" && (window as any).__addDebugEvent) {
    (window as any).__addDebugEvent(type, message, data);
  }
}

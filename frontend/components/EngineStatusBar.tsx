"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

interface EngineStatus {
  status: "ok" | "warning" | "critical" | "offline";
  cpu_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  memory_free_gb: number;
  ollama: "healthy" | "unhealthy";
  engine_enabled: boolean;
}

export default function EngineStatusBar() {
  const [showTooltip, setShowTooltip] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["engine-status"],
    queryFn: async () => {
      const response = await fetch("/api/engine/status");
      if (!response.ok) {
        throw new Error("Failed to fetch engine status");
      }
      return response.json() as Promise<EngineStatus>;
    },
    refetchInterval: 2000, // Poll every 2 seconds for real-time monitoring
    refetchIntervalInBackground: false, // Pause when tab is not active to save resources
  });

  if (isLoading || error || !data) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700">
        <div className="w-2 h-2 rounded-full bg-gray-500 animate-pulse"></div>
        <span className="text-xs text-slate-400">Cargando...</span>
      </div>
    );
  }

  const getStatusConfig = () => {
    switch (data.status) {
      case "ok":
        return {
          color: "bg-emerald-500",
          text: "Motor estable",
          textColor: "text-emerald-400",
          progressColor: "bg-emerald-500",
        };
      case "warning":
        return {
          color: "bg-amber-500",
          text: "Motor exigido",
          textColor: "text-amber-400",
          progressColor: "bg-amber-500",
        };
      case "critical":
        return {
          color: "bg-red-500",
          text: "Motor crítico",
          textColor: "text-red-400",
          progressColor: "bg-red-500",
        };
      case "offline":
        return {
          color: "bg-gray-500",
          text: "Motor offline",
          textColor: "text-gray-400",
          progressColor: "bg-gray-500",
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div
      className="relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700 hover:bg-slate-800 transition-colors cursor-pointer">
        {/* Status indicator */}
        <div className={`w-2 h-2 rounded-full ${config.color} ${data.status !== 'offline' ? 'animate-pulse' : ''}`}></div>

        {/* Status text and CPU bar */}
        <div className="flex flex-col gap-1 min-w-[120px]">
          <span className={`text-xs font-medium ${config.textColor}`}>
            {config.text}
          </span>

          {/* CPU Progress bar */}
          <div className="w-full h-1 bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full ${config.progressColor} transition-all duration-500 ease-out`}
              style={{ width: `${Math.min(data.cpu_percent, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* CPU percentage */}
        <span className="text-xs text-slate-400 font-mono">
          {data.cpu_percent.toFixed(1)}%
        </span>
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 z-50 w-64 p-3 rounded-lg bg-slate-800 border border-slate-700 shadow-xl">
          <div className="space-y-2 text-xs">
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">CPU:</span>
              <span className="font-mono text-slate-200">{data.cpu_percent.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">Memoria usada:</span>
              <span className="font-mono text-slate-200">{data.memory_used_gb.toFixed(2)} GB</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">Memoria disponible:</span>
              <span className="font-mono text-slate-200">{data.memory_free_gb.toFixed(2)} GB</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">Memoria total:</span>
              <span className="font-mono text-slate-200">{data.memory_total_gb.toFixed(2)} GB</span>
            </div>
            <div className="pt-2 border-t border-slate-700">
              <div className="flex justify-between gap-4">
                <span className="text-slate-400">Ollama:</span>
                <span className={`font-semibold ${data.ollama === 'healthy' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {data.ollama === 'healthy' ? 'Saludable' : 'No disponible'}
                </span>
              </div>
            </div>
          </div>

          {/* Tooltip arrow */}
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-800 border-l border-t border-slate-700 rotate-45"></div>
        </div>
      )}
    </div>
  );
}

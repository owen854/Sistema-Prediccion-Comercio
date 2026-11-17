"use client";

import { useEffect, useState } from "react";

import { ApiError, getHealth, type HealthResponse } from "@/lib/api/client";

type State =
  | { kind: "cargando" }
  | { kind: "ok"; health: HealthResponse }
  | { kind: "error"; message: string };

/** Estado de la API, la base de datos y los recursos de cómputo (GET /health). */
export function ApiStatus({ detailed = false }: { detailed?: boolean }) {
  const [state, setState] = useState<State>({ kind: "cargando" });

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((health) => !cancelled && setState({ kind: "ok", health }))
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof ApiError ? err.message : "Error desconocido.";
        setState({ kind: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.kind === "cargando") {
    return <Badge tone="neutral" text="Conectando con la API…" />;
  }
  if (state.kind === "error") {
    return (
      <div className="flex flex-col gap-1">
        <Badge tone="error" text="API sin conexión" />
        {detailed && <p className="text-xs text-[#475569]">{state.message}</p>}
      </div>
    );
  }

  const { health } = state;
  const tone = health.status === "ok" ? "ok" : "warn";
  return (
    <div className="flex flex-col gap-2">
      <Badge
        tone={tone}
        text={health.status === "ok" ? `API v${health.version} en línea` : "API en modo degradado"}
      />
      {detailed && (
        <ul className="grid grid-cols-1 gap-x-6 gap-y-1 text-xs text-[#475569] sm:grid-cols-2 xl:grid-cols-4">
          <Item label="Base de datos" ok={health.base_de_datos === "ok"} />
          <Item label="OpenMP (C++)" ok={health.capacidades.openmp_kernels} />
          <Item label="MPI" ok={health.capacidades.mpi4py} />
          <Item label="GPU CUDA" ok={health.capacidades.cuda} />
        </ul>
      )}
    </div>
  );
}

function Item({ label, ok }: { label: string; ok: boolean }) {
  return (
    <li className="flex items-center gap-1.5">
      <span
        aria-hidden
        className={`h-2 w-2 rounded-full ${ok ? "bg-[#15803D]" : "bg-[#CBD5E1]"}`}
      />
      {label}: <span className="font-medium text-[#0F172A]">{ok ? "disponible" : "no disponible"}</span>
    </li>
  );
}

const TONES = {
  ok: "bg-[#DCFCE7] text-[#15803D]",
  warn: "bg-[#FEF3C7] text-[#B45309]",
  error: "bg-[#FEE2E2] text-[#B91C1C]",
  neutral: "bg-[#E2E8F0] text-[#475569]",
} as const;

function Badge({ tone, text }: { tone: keyof typeof TONES; text: string }) {
  return (
    <span
      role="status"
      className={`inline-flex w-fit items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${TONES[tone]}`}
    >
      {text}
    </span>
  );
}

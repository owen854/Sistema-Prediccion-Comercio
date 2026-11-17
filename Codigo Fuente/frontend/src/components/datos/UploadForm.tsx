"use client";

import { useEffect, useState, type FormEvent } from "react";

import {
  ApiError,
  listAutorizaciones,
  uploadSales,
  type Autorizacion,
  type Carga,
  type Comercio,
} from "@/lib/api/client";

type Status =
  | { kind: "idle" }
  | { kind: "sending" }
  | { kind: "ok"; result: Carga }
  | { kind: "error"; message: string; problems: { mensaje: string; fila?: number | null }[] };

export function UploadForm({ comercios, onUploaded }: { comercios: Comercio[]; onUploaded: () => void }) {
  const [elegido, setElegido] = useState<number | null>(null);
  // Los comercios llegan después del primer render: por defecto se usa el primero.
  const comercioId = elegido ?? comercios[0]?.id ?? null;
  const [autorizaciones, setAutorizaciones] = useState<Autorizacion[]>([]);
  const [autorizacionId, setAutorizacionId] = useState<number | null>(null);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [nombre, setNombre] = useState("Ventas");
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  useEffect(() => {
    if (comercioId === null) return;
    let cancelled = false;
    listAutorizaciones(comercioId)
      .then((list) => {
        if (cancelled) return;
        setAutorizaciones(list);
        setAutorizacionId(list[0]?.id ?? null);
      })
      .catch(() => !cancelled && setAutorizaciones([]));
    return () => {
      cancelled = true;
    };
  }, [comercioId]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!archivo || comercioId === null || autorizacionId === null) return;
    setStatus({ kind: "sending" });
    try {
      const result = await uploadSales({ archivo, comercioId, autorizacionId, nombre });
      setStatus({ kind: "ok", result });
      onUploaded();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "No se pudo cargar el archivo.";
      const problems = err instanceof ApiError ? (err.detail?.problemas ?? []) : [];
      setStatus({ kind: "error", message, problems });
    }
  }

  if (comercios.length === 0) {
    return (
      <p className="text-sm text-[#475569]">
        Primero debe registrarse el comercio y su autorización de uso de datos (Ley 1581 de 2012).
      </p>
    );
  }

  const field = "rounded-md border border-[#CBD5E1] bg-white px-3 py-2 text-sm";
  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm font-medium">
          Comercio
          <select className={field} value={comercioId ?? ""} onChange={(e) => setElegido(Number(e.target.value))}>
            {comercios.map((c) => (
              <option key={c.id} value={c.id}>
                {c.codigo_seudonimo} · {c.municipio}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Autorización de uso de datos
          <select
            className={field}
            value={autorizacionId ?? ""}
            onChange={(e) => setAutorizacionId(Number(e.target.value))}
            disabled={autorizaciones.length === 0}
          >
            {autorizaciones.length === 0 && <option value="">Sin autorización registrada</option>}
            {autorizaciones.map((a) => (
              <option key={a.id} value={a.id}>
                {a.fecha} · {a.alcance.slice(0, 50)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Nombre del conjunto
          <input className={field} value={nombre} maxLength={120} onChange={(e) => setNombre(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Archivo (.xlsx o .csv)
          <input
            className={field}
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
          />
        </label>
      </div>
      <button
        type="submit"
        disabled={!archivo || autorizacionId === null || status.kind === "sending"}
        className="w-fit rounded-md bg-[#B45309] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
      >
        {status.kind === "sending" ? "Cargando…" : "Cargar ventas"}
      </button>

      {status.kind === "ok" && (
        <p role="status" className="text-sm text-[#15803D]">
          {status.result.nueva
            ? `Archivo cargado como versión ${status.result.version.version} (${status.result.version.filas} filas).`
            : "Este archivo ya se había cargado; no se creó una versión nueva."}
          {status.result.version.columnas_eliminadas.length > 0 &&
            ` Se eliminaron columnas con datos personales: ${status.result.version.columnas_eliminadas.join(", ")}.`}
        </p>
      )}
      {status.kind === "error" && (
        <div role="alert" className="text-sm text-[#B91C1C]">
          <p className="font-semibold">{status.message}</p>
          <ul className="list-disc pl-5">
            {status.problems.map((p, i) => (
              <li key={i}>
                {p.fila ? `Fila ${p.fila}: ` : ""}
                {p.mensaje}
              </li>
            ))}
          </ul>
        </div>
      )}
    </form>
  );
}

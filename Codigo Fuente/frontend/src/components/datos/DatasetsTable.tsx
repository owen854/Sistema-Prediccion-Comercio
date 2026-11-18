"use client";

import { useState } from "react";

import { ApiError, getCalidad, type Dataset, type ReporteCalidad } from "@/lib/api/client";
import {
  FRECUENCIA_LABEL,
  ORIGEN_LABEL,
  latestVersion,
  qualityRows,
  qualityWarnings,
} from "@/lib/datasets";

const ORIGEN_TONE: Record<string, string> = {
  publico: "bg-[#E0F2FE] text-[#0369A1]",
  transaccional: "bg-[#DCFCE7] text-[#15803D]",
  sintetico: "bg-[#FEF3C7] text-[#B45309]",
};

export function DatasetsTable({ datasets }: { datasets: Dataset[] }) {
  const [open, setOpen] = useState<number | null>(null);
  const [report, setReport] = useState<ReporteCalidad | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function toggle(dataset: Dataset) {
    if (open === dataset.id) {
      setOpen(null);
      return;
    }
    const v = latestVersion(dataset);
    setOpen(dataset.id);
    setReport(null);
    setError(null);
    if (!v) return;
    try {
      setReport(await getCalidad(dataset.id, v.version));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cargar el reporte.");
    }
  }

  if (datasets.length === 0) {
    return <p className="text-sm text-[#475569]">Todavía no hay conjuntos de datos registrados.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-md border border-[#E2E8F0] bg-white">
      <table className="w-full text-left text-sm">
        <thead className="bg-[#F8F7F4] text-xs text-[#475569] uppercase">
          <tr>
            <th className="px-4 py-2.5 font-semibold">Conjunto</th>
            <th className="px-4 py-2.5 font-semibold">Origen</th>
            <th className="px-4 py-2.5 font-semibold">Frecuencia</th>
            <th className="px-4 py-2.5 text-right font-semibold">Versión</th>
            <th className="px-4 py-2.5 text-right font-semibold">Filas</th>
            <th className="px-4 py-2.5 font-semibold">Calidad</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#E2E8F0]">
          {datasets.map((d) => {
            const v = latestVersion(d);
            return (
              <FragmentRow key={d.id}>
                <tr>
                  <td className="px-4 py-3">
                    <p className="font-medium">{d.nombre}</p>
                    <p className="text-xs text-[#64748B]">{d.fuente}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${ORIGEN_TONE[d.origen] ?? ""}`}
                    >
                      {ORIGEN_LABEL[d.origen] ?? d.origen}
                    </span>
                  </td>
                  <td className="px-4 py-3">{FRECUENCIA_LABEL[d.frecuencia] ?? d.frecuencia}</td>
                  <td className="font-mono-tabular px-4 py-3 text-right">{v?.version ?? "—"}</td>
                  <td className="font-mono-tabular px-4 py-3 text-right">{v?.filas ?? "—"}</td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => toggle(d)}
                      aria-expanded={open === d.id}
                      className="text-sm font-semibold text-[#B45309] hover:underline"
                    >
                      {open === d.id ? "Ocultar" : "Ver reporte"}
                    </button>
                  </td>
                </tr>
                {open === d.id && (
                  <tr>
                    <td colSpan={6} className="bg-[#F8F7F4] px-4 py-4">
                      {error && <p className="text-sm text-[#B91C1C]">{error}</p>}
                      {!error && !report && <p className="text-sm text-[#475569]">Cargando…</p>}
                      {report && <QualityReport report={report} />}
                    </td>
                  </tr>
                )}
              </FragmentRow>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function FragmentRow({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

function QualityReport({ report }: { report: ReporteCalidad }) {
  const warnings = qualityWarnings(report);
  return (
    <div className="flex flex-col gap-3">
      <dl className="grid grid-cols-1 gap-x-8 gap-y-1 text-sm sm:grid-cols-2">
        {qualityRows(report).map((r) => (
          <div key={r.label} className="flex justify-between gap-4 border-b border-[#E2E8F0] py-1">
            <dt className="text-[#475569]">{r.label}</dt>
            <dd className="font-mono-tabular font-medium">{r.value}</dd>
          </div>
        ))}
      </dl>
      {warnings.length > 0 && (
        <ul className="list-disc pl-5 text-sm text-[#B45309]">
          {warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

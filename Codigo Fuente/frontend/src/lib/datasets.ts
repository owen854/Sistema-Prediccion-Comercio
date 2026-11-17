// Presentación de conjuntos de datos y reportes de calidad (lógica pura, probada con Vitest).
import type { Dataset, DatasetVersion, ReporteCalidad } from "@/lib/api/client";

export const ORIGEN_LABEL: Record<string, string> = {
  publico: "Público",
  transaccional: "Comercio",
  sintetico: "Sintético",
};

export const FRECUENCIA_LABEL: Record<string, string> = {
  D: "Diaria",
  W: "Semanal",
  MS: "Mensual",
};

export function latestVersion(dataset: Dataset): DatasetVersion | undefined {
  return dataset.versiones.reduce<DatasetVersion | undefined>(
    (best, v) => (best === undefined || v.version > best.version ? v : best),
    undefined,
  );
}

// Filas del reporte de calidad en el orden y con los nombres que entiende el comerciante.
const CALIDAD_CAMPOS: [string, string][] = [
  ["filas", "Filas recibidas"],
  ["series", "Productos o series"],
  ["fecha_inicio", "Desde"],
  ["fecha_fin", "Hasta"],
  ["periodos_cubiertos", "Periodos cubiertos"],
  ["duplicados", "Filas repetidas (se suman)"],
  ["nulos", "Valores vacíos"],
  ["negativos", "Valores negativos"],
  ["pct_ceros", "% de ventas en cero"],
  ["celdas_faltantes", "Días o meses sin registro"],
  ["pct_celdas_faltantes", "% sin registro"],
];

export function qualityRows(report: ReporteCalidad): { label: string; value: string }[] {
  return CALIDAD_CAMPOS.filter(([key]) => key in report).map(([key, label]) => ({
    label,
    value: report[key] === null ? "—" : String(report[key]),
  }));
}

export function qualityWarnings(report: ReporteCalidad): string[] {
  const warnings: string[] = [];
  if (Number(report.negativos ?? 0) > 0) warnings.push("Hay ventas negativas: revise devoluciones.");
  if (Number(report.pct_celdas_faltantes ?? 0) > 20)
    warnings.push("Más del 20 % de los periodos no tiene registro.");
  if (Number(report.duplicados ?? 0) > 0) warnings.push("Hay filas repetidas; se sumaron.");
  return warnings;
}

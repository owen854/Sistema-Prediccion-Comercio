// Cliente de la API FastAPI. Toda cifra que muestra la interfaz viene de aquí (ADR-001).
import type { components } from "./schema";

type Schemas = components["schemas"];
export type HealthResponse = Schemas["HealthResponse"];
export type Comercio = Schemas["ComercioOut"];
export type Autorizacion = Schemas["AutorizacionOut"];
export type Dataset = Schemas["DatasetOut"];
export type DatasetVersion = Schemas["DatasetVersionOut"];
export type Carga = Schemas["CargaOut"];
export type ErrorCarga = Schemas["ErrorCargaOut"];
export type ReporteCalidad = Record<string, string | number | null>;

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly detail?: ErrorCarga,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(`No se pudo conectar con la API en ${API_URL}.`);
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | (ErrorCarga & { detail?: string })
      | null;
    const message = body?.detalle ?? body?.detail ?? `La API respondió ${response.status}.`;
    throw new ApiError(String(message), response.status, body ?? undefined);
  }
  return (await response.json()) as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { cache: "no-store" });
}

export const getHealth = () => apiGet<HealthResponse>("/health");
export const listDatasets = () => apiGet<Dataset[]>("/api/v1/datasets");
export const listComercios = () => apiGet<Comercio[]>("/api/v1/comercios");
export const listAutorizaciones = (comercioId: number) =>
  apiGet<Autorizacion[]>(`/api/v1/comercios/${comercioId}/autorizaciones`);
export const getCalidad = (datasetId: number, version: number) =>
  apiGet<ReporteCalidad>(`/api/v1/datasets/${datasetId}/versiones/${version}/calidad`);

export function uploadSales(form: {
  archivo: File;
  comercioId: number;
  autorizacionId: number;
  nombre: string;
}): Promise<Carga> {
  const data = new FormData();
  data.append("archivo", form.archivo);
  data.append("comercio_id", String(form.comercioId));
  data.append("autorizacion_id", String(form.autorizacionId));
  data.append("nombre", form.nombre);
  return request<Carga>("/api/v1/datasets/carga", { method: "POST", body: data });
}

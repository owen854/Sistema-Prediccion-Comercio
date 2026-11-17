// Cliente de la API FastAPI. Toda cifra que muestra la interfaz viene de aquí (ADR-001).
import type { components } from "./schema";

export type HealthResponse = components["schemas"]["HealthResponse"];

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
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
    throw new ApiError(`La API respondió ${response.status} en ${path}.`, response.status);
  }
  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health", { cache: "no-store" });
}

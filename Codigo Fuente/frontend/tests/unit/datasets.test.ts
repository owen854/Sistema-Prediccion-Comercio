import { describe, expect, it } from "vitest";

import type { Dataset } from "@/lib/api/client";
import { latestVersion, qualityRows, qualityWarnings } from "@/lib/datasets";

const version = (n: number) => ({
  id: n,
  version: n,
  sha256: "x".repeat(64),
  archivo_original: "ventas.csv",
  filas: 10 * n,
  columnas_eliminadas: [],
  autorizacion_id: null,
  creado_en: "2026-11-17T00:00:00Z",
});

describe("conjuntos de datos", () => {
  it("toma la versión más reciente", () => {
    const d = { versiones: [version(1), version(3), version(2)] } as unknown as Dataset;
    expect(latestVersion(d)?.version).toBe(3);
    expect(latestVersion({ versiones: [] } as unknown as Dataset)).toBeUndefined();
  });

  it("muestra el reporte de calidad con nombres comprensibles", () => {
    const rows = qualityRows({ filas: 120, duplicados: 2, desconocido: 5 });
    expect(rows).toEqual([
      { label: "Filas recibidas", value: "120" },
      { label: "Filas repetidas (se suman)", value: "2" },
    ]);
  });

  it("advierte sobre negativos, huecos y duplicados", () => {
    expect(qualityWarnings({ negativos: 1, pct_celdas_faltantes: 35, duplicados: 1 })).toHaveLength(3);
    expect(qualityWarnings({ negativos: 0, pct_celdas_faltantes: 5, duplicados: 0 })).toEqual([]);
  });
});

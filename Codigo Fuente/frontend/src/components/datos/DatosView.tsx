"use client";

import { useCallback, useEffect, useState } from "react";

import { DatasetsTable } from "@/components/datos/DatasetsTable";
import { UploadForm } from "@/components/datos/UploadForm";
import { ApiError, listComercios, listDatasets, type Comercio, type Dataset } from "@/lib/api/client";

export function DatosView() {
  const [datasets, setDatasets] = useState<Dataset[] | null>(null);
  const [comercios, setComercios] = useState<Comercio[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [d, c] = await Promise.all([listDatasets(), listComercios()]);
      setDatasets(d);
      setComercios(c);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los datos.");
    }
  }, []);

  useEffect(() => {
    // Carga inicial desde la API (sistema externo).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-bold">Cargar ventas</h2>
        <p className="max-w-2xl text-sm text-[#475569]">
          Use la{" "}
          <a className="font-semibold text-[#B45309] hover:underline" href="/plantilla_ventas_comercio.xlsx">
            plantilla de ventas
          </a>
          . Una fila por producto y día. Las columnas con datos de clientes se eliminan y la sucursal se
          reemplaza por un seudónimo.
        </p>
        <div className="rounded-md border border-[#E2E8F0] bg-white p-5">
          <UploadForm comercios={comercios} onUploaded={load} />
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-bold">Conjuntos de datos registrados</h2>
        {error && <p className="text-sm text-[#B91C1C]">{error}</p>}
        {!error && datasets === null && <p className="text-sm text-[#475569]">Cargando…</p>}
        {datasets && <DatasetsTable datasets={datasets} />}
      </section>
    </div>
  );
}

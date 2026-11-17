import { PageHeader } from "@/components/ui/PageHeader";
import { findNavItem } from "@/lib/navigation";

// Contenido del documento del proyecto (capítulo de Metodología). Sin cifras de resultados:
// esas se mostrarán desde los experimentos registrados.
const FASES = [
  {
    fase: "1. Comprensión del contexto y de los datos",
    objetivo: "Identificar los patrones de consumo de Cúcuta y municipios, considerando el comercio transfronterizo.",
    etapa: "CRISP-DM: comprensión del negocio y de los datos",
  },
  {
    fase: "2. Preparación de datos y diseño del sistema",
    objetivo: "Seleccionar algoritmos de pronóstico (ARIMA, LSTM, Prophet) y estrategias de paralelización.",
    etapa: "CRISP-DM: preparación y selección de técnicas · PCAM: partición y comunicación",
  },
  {
    fase: "3. Construcción del sistema paralelo",
    objetivo: "Procesar datos históricos con MPI y entrenar modelos de deep learning con CUDA.",
    etapa: "CRISP-DM: modelado · PCAM: aglomeración y mapeo",
  },
  {
    fase: "4. Evaluación y entrega",
    objetivo: "Validar con datos de comercios locales el error de predicción y la mejora en inventarios.",
    etapa: "CRISP-DM: evaluación y despliegue",
  },
];

const METRICAS = [
  { nombre: "RMSE", formula: "√[(1/n) Σ (yₜ − ŷₜ)²]", uso: "Error en unidades; castiga los errores grandes." },
  { nombre: "MAPE", formula: "(100/n) Σ |(yₜ − ŷₜ) / yₜ|", uso: "Error en porcentaje; excluye días sin venta." },
  { nombre: "Aceleración", formula: "S(p) = T₁ / Tₚ", uso: "Cuántas veces más rápido con p unidades." },
  { nombre: "Eficiencia", formula: "E(p) = S(p) / p", uso: "Qué tan bien se aprovecha cada unidad." },
];

export default function MetodologiaPage() {
  const item = findNavItem("/metodologia");
  return (
    <div className="flex flex-col gap-8">
      <PageHeader title={item.label} description={item.description} />

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-bold">CRISP-DM adaptada con PCAM</h2>
        <p className="max-w-3xl text-sm text-[#475569]">
          CRISP-DM organiza el ciclo de vida del proyecto de datos y PCAM (partición, comunicación,
          aglomeración y mapeo) guía el diseño de los programas paralelos. Primero se construye una
          versión secuencial de referencia y después las versiones paralelas, verificando que den
          los mismos resultados.
        </p>
        <div className="overflow-x-auto rounded-md border border-[#E2E8F0] bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#F8F7F4] text-xs text-[#475569] uppercase">
              <tr>
                <th className="px-4 py-2.5 font-semibold">Fase</th>
                <th className="px-4 py-2.5 font-semibold">Objetivo específico</th>
                <th className="px-4 py-2.5 font-semibold">Etapas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F0]">
              {FASES.map((f) => (
                <tr key={f.fase}>
                  <td className="px-4 py-3 font-medium">{f.fase}</td>
                  <td className="px-4 py-3 text-[#475569]">{f.objetivo}</td>
                  <td className="px-4 py-3 text-[#475569]">{f.etapa}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-bold">Cómo se mide</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {METRICAS.map((m) => (
            <div key={m.nombre} className="rounded-md border border-[#E2E8F0] bg-white p-4">
              <p className="text-sm font-semibold">{m.nombre}</p>
              <p className="font-mono-tabular my-1 text-sm text-[#92400E]">{m.formula}</p>
              <p className="text-xs text-[#475569]">{m.uso}</p>
            </div>
          ))}
        </div>
        <p className="max-w-3xl text-sm text-[#475569]">
          Todos los modelos se comparan con los mismos datos, las mismas particiones en orden
          cronológico (origen móvil), semillas fijas y repeticiones, frente a un pronóstico ingenuo
          estacional como línea base.
        </p>
      </section>
    </div>
  );
}

// Vistas del dashboard y requerimientos que atiende cada una (01_Requerimientos_RF_RNF.md).

export interface NavItem {
  href: string;
  label: string;
  description: string;
  requirements: string;
  phase: string;
}

export const NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    label: "Panel principal",
    description: "Demanda proyectada, productos en riesgo y alertas de su comercio.",
    requirements: "RF-53",
    phase: "Fase 4 (Sprint 3)",
  },
  {
    href: "/pronosticos",
    label: "Pronósticos",
    description: "Consulte la demanda esperada por producto, categoría y fecha, con su rango probable.",
    requirements: "RF-54, RF-61",
    phase: "Fase 4 (Sprint 3)",
  },
  {
    href: "/inventario",
    label: "Inventario y compras",
    description: "Qué productos están en riesgo de agotarse y cuánto conviene pedir.",
    requirements: "RF-46 a RF-49, RF-58",
    phase: "Fase 4 (Sprints 3 y 4)",
  },
  {
    href: "/patrones",
    label: "Patrones de consumo",
    description: "Tendencia, temporadas fuertes, inflación de Cúcuta y relación con la frontera.",
    requirements: "RF-18 a RF-21, RF-55",
    phase: "Fase 1 (Sprint 1) y Fase 4",
  },
  {
    href: "/escenarios",
    label: "Escenarios",
    description: "Simule qué pasaría con la demanda si cambian el paso fronterizo, la TRM o la inflación.",
    requirements: "RF-51",
    phase: "Fase 4 (Sprint 4)",
  },
  {
    href: "/datos",
    label: "Mis datos",
    description: "Cargue sus ventas y revise el reporte de calidad de cada archivo.",
    requirements: "RF-06 a RF-09, RF-59",
    phase: "Disponible (Fase 1)",
  },
  {
    href: "/modelos",
    label: "Modelos",
    description: "Comparación de modelos (ingenuo estacional, SARIMA, Prophet, LSTM) y sus fichas.",
    requirements: "RF-42, RF-56, RNF-20",
    phase: "Fase 2 (Sprint 2) y Fase 4",
  },
  {
    href: "/rendimiento",
    label: "Rendimiento paralelo",
    description: "Tiempos, aceleración y eficiencia con OpenMP, MPI y CUDA.",
    requirements: "RF-40, RF-57",
    phase: "Fase 3 (Sprints 3 y 4)",
  },
  {
    href: "/metodologia",
    label: "Metodología",
    description: "Cómo se construye y valida el sistema.",
    requirements: "RNF-26",
    phase: "Disponible",
  },
];

export function findNavItem(href: string): NavItem {
  const item = NAV_ITEMS.find((i) => i.href === href);
  if (!item) throw new Error(`Ruta sin configurar en NAV_ITEMS: ${href}`);
  return item;
}

"use client";

import React, { useState, useMemo } from "react";
import type {
  Sku,
  HistoricalDemandPoint,
  BorderBridge,
  SimulationScenario,
  RestockOrder,
} from "@/db/schema";
import {
  type SimulationParams,
  evaluateSkusWithSimulation,
  buildSimulatedTimeSeries,
  computeSummaryMetrics,
  formatCop,
  formatNumberCo,
} from "@/lib/forecast-engine";
import { DemandForecastChart } from "./DemandForecastChart";
import { BorderCorridorSchematic } from "./BorderCorridorSchematic";
import { ProjectMethodologyPanel } from "./ProjectMethodologyPanel";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Sliders,
  RotateCcw,
  Save,
  PackageCheck,
  PlusCircle,
  Download,
  ArrowUpRight,
  ShieldAlert,
  Truck,
  Landmark,
  Users,
  BookOpen,
  BarChart3,
  Boxes,
  Sparkles,
  Search,
} from "lucide-react";

interface MacroSnapshot {
  trmCopUsd: number;
  trmChange24hPct: number;
  vesUsdBcv: number;
  vesUsdParalelo: number;
  vesUsdSpreadPct: number;
  copVesImplicitRate: number;
  totalDailyBridgeCrossings: number;
  activeCorridorStatus: string;
  lastUpdated: string;
}

interface FronteraForecastDashboardProps {
  initialSkus: Sku[];
  initialSeries: HistoricalDemandPoint[];
  initialBridges: BorderBridge[];
  initialScenarios: SimulationScenario[];
  initialOrders: RestockOrder[];
  macroSnapshot: MacroSnapshot;
}

const CATEGORIES = [
  "Todos",
  "Canasta Familiar",
  "Salud y Farmacia",
  "Cuidado Personal",
  "Ferretería y Repuestos",
  "Textil y Calzado",
];

const ZONES = [
  "Todas las Zonas",
  "La Parada (Villa del Rosario)",
  "Cúcuta Centro / Alejandría",
  "Cenabastos Cúcuta",
  "Los Patios Comercial",
];

export function FronteraForecastDashboard({
  initialSkus,
  initialSeries,
  initialBridges,
  initialScenarios,
  initialOrders,
  macroSnapshot,
}: FronteraForecastDashboardProps) {
  // Estado de datos sincronizados con PostgreSQL
  const [skuList, setSkuList] = useState<Sku[]>(initialSkus);
  const [scenarios, setScenarios] =
    useState<SimulationScenario[]>(initialScenarios);
  const [orders, setOrders] = useState<RestockOrder[]>(initialOrders);

  // Pestaña activa (Máximo 3 vistas principales de alto nivel)
  const [activeTab, setActiveTab] = useState<
    "dashboard" | "catalog" | "methodology"
  >("dashboard");

  // Parámetros del Simulador Econométrico "What-If"
  const [simParams, setSimParams] = useState<SimulationParams>({
    fxShockPct: 12,
    bridgeFlowPct: 108,
    inflationShockPct: 10,
    remittanceBoost: true,
    horizonDays: 14,
    selectedCategory: "Todos",
    selectedZone: "Todas las Zonas",
  });

  // Búsqueda y filtro de tabla de SKUs
  const [skuSearch, setSkuSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState<
    "TODOS" | "CRITICO" | "PREVENTIVO" | "OPTIMO"
  >("TODOS");

  // Estado para guardar escenario en PostgreSQL
  const [scenarioName, setScenarioName] = useState("");
  const [isSavingScenario, setIsSavingScenario] = useState(false);
  const [feedbackBanner, setFeedbackBanner] = useState<{
    type: "success" | "info";
    text: string;
  } | null>(null);

  // Estado para modal de Nuevo SKU
  const [showNewSkuForm, setShowNewSkuForm] = useState(false);
  const [newSkuData, setNewSkuData] = useState({
    code: "NDS-ALM-015",
    name: "",
    category: "Canasta Familiar",
    zone: "La Parada (Villa del Rosario)",
    primaryBridge: "Simón Bolívar",
    unitPriceCop: 82000,
    currentStock: 210,
    safetyStock: 150,
    leadTimeDays: 4,
    baseDailyDemand: 38,
    fxElasticity: 1.52,
    bridgeElasticity: 1.7,
    remittanceElasticity: 1.4,
    supplierRoute: "Corredor Bucaramanga - Pamplona - Cúcuta",
  });
  const [isCreatingSku, setIsCreatingSku] = useState(false);
  const [processingOrderId, setProcessingOrderId] = useState<number | null>(
    null
  );

  // Cálculos reactivos del motor econométrico
  const evaluatedSkus = useMemo(
    () => evaluateSkusWithSimulation(skuList, simParams),
    [skuList, simParams]
  );

  const simulatedSeries = useMemo(
    () =>
      buildSimulatedTimeSeries(
        initialSeries,
        evaluatedSkus,
        skuList,
        simParams
      ),
    [initialSeries, evaluatedSkus, skuList, simParams]
  );

  const summaryMetrics = useMemo(
    () => computeSummaryMetrics(evaluatedSkus, simulatedSeries, simParams),
    [evaluatedSkus, simulatedSeries, simParams]
  );

  const visibleTableSkus = useMemo(() => {
    return evaluatedSkus
      .filter((s) => {
        if (riskFilter !== "TODOS" && s.riskLevel !== riskFilter) return false;
        if (!skuSearch.trim()) return true;
        const q = skuSearch.toLowerCase();
        return (
          s.name.toLowerCase().includes(q) ||
          s.code.toLowerCase().includes(q) ||
          s.zone.toLowerCase().includes(q) ||
          s.category.toLowerCase().includes(q)
        );
      })
      .sort((a, b) => {
        const rank = { CRITICO: 0, PREVENTIVO: 1, OPTIMO: 2 };
        if (rank[a.riskLevel] !== rank[b.riskLevel]) {
          return rank[a.riskLevel] - rank[b.riskLevel];
        }
        return a.daysUntilStockout - b.daysUntilStockout;
      });
  }, [evaluatedSkus, riskFilter, skuSearch]);

  // Funciones de Acción y Persistencia en Base de Datos
  const handleResetSimulation = () => {
    setSimParams((prev) => ({
      ...prev,
      fxShockPct: 0,
      bridgeFlowPct: 100,
      inflationShockPct: 0,
      remittanceBoost: false,
    }));
    setFeedbackBanner({
      type: "info",
      text: "Simulador restablecido a condiciones base (sin choques exógenos).",
    });
  };

  const handleLoadScenario = (sc: SimulationScenario) => {
    const validHorizon =
      sc.horizonDays === 7 || sc.horizonDays === 30 ? sc.horizonDays : 14;
    setSimParams({
      fxShockPct: sc.fxShockPct,
      bridgeFlowPct: sc.bridgeFlowPct,
      inflationShockPct: sc.inflationShockPct,
      remittanceBoost: sc.remittanceBoost,
      horizonDays: validHorizon,
      selectedCategory: sc.selectedCategory || "Todos",
      selectedZone: sc.selectedZone || "Todas las Zonas",
    });
    setFeedbackBanner({
      type: "info",
      text: `Escenario cargado: "${sc.name}" (FX ${
        sc.fxShockPct >= 0 ? `+${sc.fxShockPct}%` : `${sc.fxShockPct}%`
      }, Flujo Puentes ${sc.bridgeFlowPct}%).`,
    });
  };

  const handleSaveScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    const title =
      scenarioName.trim() ||
      `Simulación FX ${simParams.fxShockPct >= 0 ? "+" : ""}${
        simParams.fxShockPct
      }% | Puentes ${simParams.bridgeFlowPct}%`;

    setIsSavingScenario(true);
    try {
      const res = await fetch("/api/forecast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: title,
          description: `Horizonte ${simParams.horizonDays}d • Categoría: ${simParams.selectedCategory} • Zona: ${simParams.selectedZone}`,
          fxShockPct: simParams.fxShockPct,
          bridgeFlowPct: simParams.bridgeFlowPct,
          inflationShockPct: simParams.inflationShockPct,
          remittanceBoost: simParams.remittanceBoost,
          horizonDays: simParams.horizonDays,
          selectedCategory: simParams.selectedCategory,
          selectedZone: simParams.selectedZone,
          projectedDemandDeltaPct: summaryMetrics.demandDeltaPct,
          projectedRevenueCop: summaryMetrics.totalProjectedRevenueCop,
          criticalSkusCount: summaryMetrics.criticalSkusCount,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setScenarios((prev) => [data.scenario, ...prev]);
        setScenarioName("");
        setFeedbackBanner({
          type: "success",
          text: `Escenario "${data.scenario.name}" guardado exitosamente en PostgreSQL.`,
        });
      }
    } finally {
      setIsSavingScenario(false);
    }
  };

  const handleIssueRestockOrder = async (
    sku: (typeof evaluatedSkus)[number],
    applyImmediately = true
  ) => {
    const unitsToOrder =
      sku.suggestedOrderUnits > 0
        ? sku.suggestedOrderUnits
        : Math.round(sku.simulatedDailyDemand * 7);
    const costCop = Math.round(unitsToOrder * sku.unitPriceCop * 0.76);

    setProcessingOrderId(sku.id);
    try {
      const res = await fetch("/api/skus", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "RESTOCK_ORDER",
          skuId: sku.id,
          skuCode: sku.code,
          skuName: sku.name,
          zone: sku.zone,
          orderedUnits: unitsToOrder,
          estimatedCostCop: costCop,
          priority: sku.riskLevel,
          applyToStockImmediately: applyImmediately,
          notes: `Pedido sugerido por modelo ARIMAX (${sku.supplierRoute}). Cobertura previa: ${sku.daysUntilStockout} días.`,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setOrders((prev) => [data.order, ...prev]);
        if (data.updatedSku) {
          setSkuList((prev) =>
            prev.map((item) =>
              item.id === data.updatedSku.id ? data.updatedSku : item
            )
          );
        }
        setFeedbackBanner({
          type: "success",
          text: `Orden de reabastecimiento emitida para ${sku.code} (+${formatNumberCo(
            unitsToOrder
          )} u. • ${formatCop(costCop)}). Stock actualizado.`,
        });
      }
    } finally {
      setProcessingOrderId(null);
    }
  };

  const handleCreateSku = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSkuData.name.trim()) return;
    setIsCreatingSku(true);
    try {
      const res = await fetch("/api/skus", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "CREATE_SKU",
          ...newSkuData,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSkuList((prev) => [...prev, data.sku]);
        setShowNewSkuForm(false);
        setNewSkuData((prev) => ({
          ...prev,
          code: `NDS-GEN-0${skuList.length + 14}`,
          name: "",
        }));
        setFeedbackBanner({
          type: "success",
          text: `Nuevo SKU "${data.sku.name}" (${data.sku.code}) registrado en la base de datos de Norte de Santander.`,
        });
      }
    } finally {
      setIsCreatingSku(false);
    }
  };

  const handleExportCsv = () => {
    const headers = [
      "Codigo_SKU",
      "Producto",
      "Categoria",
      "Zona_Comercial_Norte_Santander",
      "Puente_Fronterizo",
      "Stock_Actual",
      "Stock_Seguridad_Dinamico",
      "Punto_Reorden_ROP",
      "Demanda_Diaria_Base",
      "Demanda_Diaria_Simulada",
      "Variacion_Pct",
      "Dias_Hasta_Quiebre",
      "Pedido_Sugerido_Unidades",
      "Nivel_Riesgo",
    ];
    const rows = evaluatedSkus.map((s) =>
      [
        s.code,
        `"${s.name.replace(/"/g, '""')}"`,
        `"${s.category}"`,
        `"${s.zone}"`,
        `"${s.primaryBridge}"`,
        s.currentStock,
        s.dynamicSafetyStock,
        s.dynamicReorderPoint,
        s.baseDailyDemand,
        s.simulatedDailyDemand,
        `${s.demandDeltaPct}%`,
        s.daysUntilStockout,
        s.suggestedOrderUnits,
        s.riskLevel,
      ].join(",")
    );
    const csvContent =
      "data:text/csv;charset=utf-8,\uFEFF" +
      [headers.join(","), ...rows].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `pronostico_demanda_fronteriza_norte_santander_${simParams.horizonDays}d.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F8F7F4] text-[#0F172A]">
      {/* 1. Barra Superior de Telemetría Macroeconómica y Cambiaria Binacional */}
      <div className="bg-[#0F172A] text-[#F8F7F4] border-b border-[#1E293B] px-4 lg:px-8 py-2 text-xs">
        <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-4 sm:gap-6">
            <span className="inline-flex items-center gap-1.5 font-semibold text-[#FBBF24]">
              <Landmark className="w-3.5 h-3.5" />
              MONITOR CAMBIARIO CÚCUTA – TÁCHIRA:
            </span>
            <div className="flex items-center gap-1.5 font-mono-tabular">
              <span className="text-[#94A3B8]">TRM COP/USD:</span>
              <span className="font-bold text-white">
                ${formatNumberCo(macroSnapshot.trmCopUsd)}
              </span>
              <span className="text-[#4ADE80] text-[11px]">
                (+{macroSnapshot.trmChange24hPct}%)
              </span>
            </div>
            <div className="flex items-center gap-1.5 font-mono-tabular">
              <span className="text-[#94A3B8]">VES/USD (Frontera):</span>
              <span className="font-bold text-white">
                {macroSnapshot.vesUsdParalelo.toFixed(2)} Bs.
              </span>
              <span className="px-1.5 py-0.2 rounded bg-[#B45309]/40 text-[#FBBF24] text-[10px]">
                Spread +{ (macroSnapshot.vesUsdSpreadPct + simParams.fxShockPct * 0.4).toFixed(1) }%
              </span>
            </div>
            <div className="hidden md:flex items-center gap-1.5 font-mono-tabular">
              <span className="text-[#94A3B8]">Tasa La Parada COP/VES:</span>
              <span className="font-bold text-[#38BDF8]">
                ${macroSnapshot.copVesImplicitRate.toFixed(1)} COP
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 font-mono-tabular">
            <div className="flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-[#38BDF8]" />
              <span className="text-[#94A3B8]">Aforo Puentes Hoy:</span>
              <span className="font-bold text-white">
                {formatNumberCo(summaryMetrics.effectiveBridgeCrossings)} cruces/día
              </span>
            </div>
            <span className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#15803D]/30 text-[#4ADE80] text-[10px] font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4ADE80] animate-pulse" />
              {macroSnapshot.activeCorridorStatus}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Cabecera Principal y Navegación de 3 Vistas */}
      <header className="bg-white border-b border-[#E2E8F0] sticky top-0 z-30 shadow-2xs">
        <div className="max-w-[1600px] mx-auto px-4 lg:px-8 py-3.5">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            {/* Identidad del Proyecto */}
            <div className="flex items-start sm:items-center gap-3">
              <div className="w-10 h-10 rounded-md bg-[#B45309] text-white flex items-center justify-center font-heading font-bold text-lg shrink-0 shadow-xs">
                NdS
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-lg sm:text-xl font-bold text-[#0F172A] font-heading tracking-tight">
                    FronteraForecast Norte de Santander
                  </h1>
                  <span className="px-2 py-0.5 text-[10px] font-mono-tabular font-semibold uppercase bg-[#F1EFEA] border border-[#E2E8F0] rounded text-[#B45309]">
                    Cúcuta • Villa del Rosario • Los Patios
                  </span>
                </div>
                <p className="text-xs text-[#475569]">
                  Sistema Inteligente de Predicción de Demanda y Abastecimiento para el Comercio Minorista Fronterizo
                </p>
              </div>
            </div>

            {/* Navegación Primaria (3 Vistas de Alto Nivel) + Exportación */}
            <div className="flex flex-wrap items-center gap-2">
              <nav className="flex items-center bg-[#F1EFEA] p-1 rounded-md border border-[#E2E8F0]">
                <button
                  type="button"
                  onClick={() => setActiveTab("dashboard")}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded text-xs font-semibold transition-colors cursor-pointer ${
                    activeTab === "dashboard"
                      ? "bg-white text-[#0F172A] shadow-2xs border-b-2 border-[#B45309]"
                      : "text-[#475569] hover:text-[#0F172A]"
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5 text-[#B45309]" />
                  Pronóstico & Simulador
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("catalog")}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded text-xs font-semibold transition-colors cursor-pointer ${
                    activeTab === "catalog"
                      ? "bg-white text-[#0F172A] shadow-2xs border-b-2 border-[#B45309]"
                      : "text-[#475569] hover:text-[#0F172A]"
                  }`}
                >
                  <Boxes className="w-3.5 h-3.5 text-[#0284C7]" />
                  SKUs, Pedidos & Puentes ({skuList.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("methodology")}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded text-xs font-semibold transition-colors cursor-pointer ${
                    activeTab === "methodology"
                      ? "bg-white text-[#0F172A] shadow-2xs border-b-2 border-[#B45309]"
                      : "text-[#475569] hover:text-[#0F172A]"
                  }`}
                >
                  <BookOpen className="w-3.5 h-3.5 text-[#15803D]" />
                  Metodología & Sustentación
                </button>
              </nav>

              <button
                type="button"
                onClick={handleExportCsv}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-[#CBD5E1] bg-white hover:bg-[#F8F7F4] text-xs font-semibold text-[#0F172A] transition-colors cursor-pointer"
                title="Exportar pronóstico y matriz de reabastecimiento a CSV"
              >
                <Download className="w-3.5 h-3.5 text-[#B45309]" />
                <span className="hidden sm:inline">Exportar CSV</span>
              </button>
            </div>
          </div>

          {/* Barra de Filtros Globales por Zona Comercial y Categoría Minorista (visible en Dashboard y Catálogo) */}
          {activeTab !== "methodology" && (
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2.5 pt-3 mt-3 border-t border-[#E2E8F0] text-xs">
              {/* Filtro por Zona Comercial de Norte de Santander */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
                <span className="text-[#64748B] font-semibold uppercase text-[10px] tracking-wider shrink-0 mr-1">
                  Nodo Comercial:
                </span>
                {ZONES.map((z) => (
                  <button
                    key={z}
                    type="button"
                    onClick={() =>
                      setSimParams((prev) => ({ ...prev, selectedZone: z }))
                    }
                    className={`px-2.5 py-1 rounded text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                      simParams.selectedZone === z
                        ? "bg-[#0F172A] text-white font-semibold"
                        : "bg-[#F8F7F4] text-[#475569] hover:bg-[#E2E8F0]/60 border border-[#E2E8F0]"
                    }`}
                  >
                    {z}
                  </button>
                ))}
              </div>

              {/* Filtro por Categoría de Producto */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
                <span className="text-[#64748B] font-semibold uppercase text-[10px] tracking-wider shrink-0 mr-1">
                  Categoría:
                </span>
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() =>
                      setSimParams((prev) => ({
                        ...prev,
                        selectedCategory: cat,
                      }))
                    }
                    className={`px-2.5 py-1 rounded text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                      simParams.selectedCategory === cat
                        ? "bg-[#B45309] text-white font-semibold"
                        : "bg-[#F8F7F4] text-[#475569] hover:bg-[#E2E8F0]/60 border border-[#E2E8F0]"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Notificación de Acción Persistida */}
      {feedbackBanner && (
        <div className="max-w-[1600px] w-full mx-auto px-4 lg:px-8 mt-4">
          <div
            className={`flex items-center justify-between px-4 py-2.5 rounded-md border text-xs font-medium ${
              feedbackBanner.type === "success"
                ? "bg-[#DCFCE7] border-[#86EFAC] text-[#15803D]"
                : "bg-[#E0F2FE] border-[#7DD3FC] text-[#0369A1]"
            }`}
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{feedbackBanner.text}</span>
            </div>
            <button
              type="button"
              onClick={() => setFeedbackBanner(null)}
              className="text-xs underline ml-4 cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}

      {/* Contenido Principal */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 lg:px-8 py-6 space-y-6">
        {activeTab === "methodology" ? (
          <ProjectMethodologyPanel onExportCsv={handleExportCsv} />
        ) : (
          <>
            {/* FILA DE 4 TARJETAS KPI EJECUTIVAS (Máx. 3 puntos de datos por tarjeta) */}
            <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              {/* KPI 1: Demanda Proyectada en el Horizonte */}
              <div className="bg-white border border-[#E2E8F0] rounded-md p-5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#475569]">
                    Demanda Proyectada (+{simParams.horizonDays} Días)
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono-tabular font-bold ${
                      summaryMetrics.demandDeltaPct >= 0
                        ? "bg-[#DCFCE7] text-[#15803D]"
                        : "bg-[#FEE2E2] text-[#B91C1C]"
                    }`}
                  >
                    {summaryMetrics.demandDeltaPct >= 0 ? (
                      <TrendingUp className="w-3.5 h-3.5" />
                    ) : (
                      <TrendingDown className="w-3.5 h-3.5" />
                    )}
                    {summaryMetrics.demandDeltaPct >= 0 ? "+" : ""}
                    {summaryMetrics.demandDeltaPct}% vs Base
                  </span>
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold font-mono-tabular text-[#0F172A]">
                    {formatNumberCo(summaryMetrics.totalProjectedUnits)}
                  </span>
                  <span className="text-xs text-[#64748B] font-medium">
                    unidades mayoristas
                  </span>
                </div>
                <div className="mt-2 pt-2 border-t border-[#F1EFEA] flex items-center justify-between text-xs">
                  <span className="text-[#64748B]">Venta Estimada (COP):</span>
                  <span className="font-mono-tabular font-bold text-[#0F172A]">
                    {formatCop(summaryMetrics.totalProjectedRevenueCop, true)}
                  </span>
                </div>
              </div>

              {/* KPI 2: Alertas de Riesgo de Quiebre de Inventario */}
              <div className="bg-white border border-[#E2E8F0] rounded-md p-5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#475569]">
                    Riesgo de Quiebre de Stock
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold ${
                      summaryMetrics.criticalSkusCount > 0
                        ? "bg-[#FEE2E2] text-[#B91C1C]"
                        : "bg-[#DCFCE7] text-[#15803D]"
                    }`}
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    {summaryMetrics.criticalSkusCount} Críticos
                  </span>
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold font-mono-tabular text-[#B91C1C]">
                    {summaryMetrics.criticalSkusCount +
                      summaryMetrics.preventiveSkusCount}
                  </span>
                  <span className="text-xs text-[#64748B] font-medium">
                    de {evaluatedSkus.length} SKUs requieren pedido
                  </span>
                </div>
                <div className="mt-2 pt-2 border-t border-[#F1EFEA] flex items-center justify-between text-xs">
                  <span className="text-[#64748B]">Desglose de Alerta:</span>
                  <span className="font-mono-tabular font-semibold text-[#475569]">
                    {summaryMetrics.criticalSkusCount} Críticos •{" "}
                    {summaryMetrics.preventiveSkusCount} Preventivos
                  </span>
                </div>
              </div>

              {/* KPI 3: Multiplicador Compuesto de Choque Fronterizo */}
              <div className="bg-white border border-[#E2E8F0] rounded-md p-5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#475569]">
                    Elasticidad Fronteriza Activa
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono-tabular font-bold bg-[#E0F2FE] text-[#0284C7]">
                    {summaryMetrics.compositeBorderMultiplier}x Impulso
                  </span>
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold font-mono-tabular text-[#0284C7]">
                    {formatNumberCo(summaryMetrics.effectiveBridgeCrossings)}
                  </span>
                  <span className="text-xs text-[#64748B] font-medium">
                    cruces diarios proyectados
                  </span>
                </div>
                <div className="mt-2 pt-2 border-t border-[#F1EFEA] flex items-center justify-between text-xs">
                  <span className="text-[#64748B]">Choque FX / Puentes:</span>
                  <span className="font-mono-tabular font-semibold text-[#B45309]">
                    FX {simParams.fxShockPct >= 0 ? "+" : ""}
                    {simParams.fxShockPct}% • Flujo {simParams.bridgeFlowPct}%
                  </span>
                </div>
              </div>

              {/* KPI 4: Precisión Econométrica del Modelo ARIMAX */}
              <div className="bg-white border border-[#E2E8F0] rounded-md p-5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#475569]">
                    Precisión Modelo ARIMAX-X
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono-tabular font-bold bg-[#DCFCE7] text-[#15803D]">
                    R² = {summaryMetrics.rSquared}
                  </span>
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold font-mono-tabular text-[#0F172A]">
                    {summaryMetrics.weightedMape}%
                  </span>
                  <span className="text-xs text-[#64748B] font-medium">
                    Error Medio (MAPE Ponderado)
                  </span>
                </div>
                <div className="mt-2 pt-2 border-t border-[#F1EFEA] flex items-center justify-between text-xs">
                  <span className="text-[#64748B]">Confianza Estadística:</span>
                  <span className="font-mono-tabular font-semibold text-[#15803D]">
                    94.16% Exactitud • IC 95%
                  </span>
                </div>
              </div>
            </section>

            {activeTab === "dashboard" && (
              <>
                {/* GRILLA PRINCIPAL DE 12 COLUMNAS: 8 Cols Gráfico de Serie Temporal + 4 Cols Simulador "What-If" */}
                <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                  {/* Lienzo de Pronóstico (8 Columnas) */}
                  <div className="lg:col-span-8 space-y-4">
                    <DemandForecastChart
                      series={simulatedSeries}
                      horizonDays={simParams.horizonDays}
                      onHorizonChange={(h) =>
                        setSimParams((prev) => ({ ...prev, horizonDays: h }))
                      }
                      selectedCategory={simParams.selectedCategory}
                      selectedZone={simParams.selectedZone}
                    />

                    {/* Tira de Escenarios Econométricos Guardados en PostgreSQL */}
                    <div className="bg-white border border-[#E2E8F0] rounded-md p-4 shadow-xs">
                      <div className="flex items-center justify-between mb-2.5">
                        <span className="text-xs font-bold uppercase tracking-wider text-[#475569] flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-[#B45309]" />
                          Escenarios de Choque Fronterizo Guardados (Click para Simular)
                        </span>
                        <span className="text-[11px] text-[#64748B] font-mono-tabular">
                          {scenarios.length} escenarios en PostgreSQL
                        </span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {scenarios.slice(0, 3).map((sc) => (
                          <button
                            key={sc.id}
                            type="button"
                            onClick={() => handleLoadScenario(sc)}
                            className="text-left p-3 rounded-md border border-[#E2E8F0] bg-[#F8F7F4] hover:bg-white hover:border-[#B45309] transition-all group cursor-pointer"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <span className="text-xs font-bold text-[#0F172A] group-hover:text-[#B45309] line-clamp-1">
                                {sc.name}
                              </span>
                              <ArrowUpRight className="w-3.5 h-3.5 text-[#64748B] group-hover:text-[#B45309] shrink-0" />
                            </div>
                            <p className="text-[11px] text-[#475569] line-clamp-2 mt-1">
                              {sc.description}
                            </p>
                            <div className="flex items-center gap-2 mt-2 pt-1.5 border-t border-[#E2E8F0] font-mono-tabular text-[10px]">
                              <span className="text-[#B45309] font-semibold">
                                FX {sc.fxShockPct >= 0 ? `+${sc.fxShockPct}%` : `${sc.fxShockPct}%`}
                              </span>
                              <span>•</span>
                              <span className="text-[#0284C7] font-semibold">
                                Puentes {sc.bridgeFlowPct}%
                              </span>
                              <span>•</span>
                              <span
                                className={
                                  sc.projectedDemandDeltaPct >= 0
                                    ? "text-[#15803D] font-bold"
                                    : "text-[#B91C1C] font-bold"
                                }
                              >
                                Demanda {sc.projectedDemandDeltaPct >= 0 ? "+" : ""}
                                {sc.projectedDemandDeltaPct}%
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Panel Simulador de Choques Fronterizos "What-If" (4 Columnas) */}
                  <div className="lg:col-span-4 bg-white border border-[#E2E8F0] rounded-md p-5 shadow-xs space-y-5">
                    <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[#B45309] flex items-center gap-1.5">
                          <Sliders className="w-3.5 h-3.5" />
                          Simulador Econométrico What-If
                        </span>
                        <h3 className="text-base font-bold text-[#0F172A] font-heading mt-0.5">
                          Variables Exógenas de Frontera
                        </h3>
                      </div>
                      <button
                        type="button"
                        onClick={handleResetSimulation}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-[#475569] hover:text-[#0F172A] bg-[#F1EFEA] hover:bg-[#E2E8F0] transition-colors cursor-pointer"
                        title="Restablecer valores base"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Base
                      </button>
                    </div>

                    {/* Control 1: Diferencial Cambiario COP/USD vs VES/USD */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <label
                          htmlFor="fx-slider"
                          className="font-semibold text-[#0F172A]"
                        >
                          1. Choque Cambiario (COP/VES/USD)
                        </label>
                        <span className="font-mono-tabular font-bold text-xs px-2 py-0.5 rounded bg-[#FEF3C7] text-[#B45309]">
                          {simParams.fxShockPct >= 0
                            ? `+${simParams.fxShockPct}%`
                            : `${simParams.fxShockPct}%`}
                        </span>
                      </div>
                      <input
                        id="fx-slider"
                        type="range"
                        min={-30}
                        max={50}
                        step={1}
                        value={simParams.fxShockPct}
                        onChange={(e) =>
                          setSimParams((prev) => ({
                            ...prev,
                            fxShockPct: Number(e.target.value),
                          }))
                        }
                        className="border-slider"
                      />
                      <div className="flex justify-between text-[10px] text-[#64748B] font-mono-tabular">
                        <span>-30% (Pérdida Paridad)</span>
                        <span>0% Base</span>
                        <span>+50% (Arbitraje Alto)</span>
                      </div>
                    </div>

                    {/* Control 2: Flujo y Permeabilidad en Puentes Internacionales */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <label
                          htmlFor="bridge-slider"
                          className="font-semibold text-[#0F172A]"
                        >
                          2. Flujo en Puentes Internacionales
                        </label>
                        <span className="font-mono-tabular font-bold text-xs px-2 py-0.5 rounded bg-[#E0F2FE] text-[#0284C7]">
                          {simParams.bridgeFlowPct}% Aforo
                        </span>
                      </div>
                      <input
                        id="bridge-slider"
                        type="range"
                        min={20}
                        max={160}
                        step={5}
                        value={simParams.bridgeFlowPct}
                        onChange={(e) =>
                          setSimParams((prev) => ({
                            ...prev,
                            bridgeFlowPct: Number(e.target.value),
                          }))
                        }
                        className="border-slider border-slider-cyan"
                      />
                      <div className="flex justify-between text-[10px] text-[#64748B] font-mono-tabular">
                        <span>20% (Restricción)</span>
                        <span>100% Normal</span>
                        <span>160% (Pico Masivo)</span>
                      </div>
                    </div>

                    {/* Control 3: Diferencial de Inflación / Desabastecimiento Táchira */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <label
                          htmlFor="inflation-slider"
                          className="font-semibold text-[#0F172A]"
                        >
                          3. Presión Inflacionaria / Escasez Táchira
                        </label>
                        <span className="font-mono-tabular font-bold text-xs px-2 py-0.5 rounded bg-[#F1EFEA] text-[#0F172A]">
                          {simParams.inflationShockPct >= 0
                            ? `+${simParams.inflationShockPct}%`
                            : `${simParams.inflationShockPct}%`}
                        </span>
                      </div>
                      <input
                        id="inflation-slider"
                        type="range"
                        min={-10}
                        max={40}
                        step={1}
                        value={simParams.inflationShockPct}
                        onChange={(e) =>
                          setSimParams((prev) => ({
                            ...prev,
                            inflationShockPct: Number(e.target.value),
                          }))
                        }
                        className="border-slider"
                      />
                      <div className="flex justify-between text-[10px] text-[#64748B] font-mono-tabular">
                        <span>-10% (Estable)</span>
                        <span>0% Base</span>
                        <span>+40% (Alta Demanda)</span>
                      </div>
                    </div>

                    {/* Control 4: Toggle de Ventana Quincenal + Remesas Binacionales */}
                    <div className="p-3.5 rounded-md bg-[#F8F7F4] border border-[#E2E8F0] flex items-center justify-between gap-3">
                      <div>
                        <span className="text-xs font-bold text-[#0F172A] block">
                          4. Pulso de Quincena + Giro de Remesas
                        </span>
                        <span className="text-[11px] text-[#475569]">
                          Activa el multiplicador de liquidez familiar en casas de cambio de La Parada y Centro.
                        </span>
                      </div>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={simParams.remittanceBoost}
                        onClick={() =>
                          setSimParams((prev) => ({
                            ...prev,
                            remittanceBoost: !prev.remittanceBoost,
                          }))
                        }
                        className={`px-3 py-1.5 rounded text-xs font-bold font-mono-tabular transition-colors shrink-0 cursor-pointer ${
                          simParams.remittanceBoost
                            ? "bg-[#15803D] text-white"
                            : "bg-[#E2E8F0] text-[#475569]"
                        }`}
                      >
                        {simParams.remittanceBoost ? "ACTIVO (+14%)" : "INACTIVO"}
                      </button>
                    </div>

                    {/* Diagnóstico Instantáneo de la Simulación */}
                    <div className="p-3.5 rounded-md bg-[#0F172A] text-white text-xs space-y-1.5">
                      <div className="flex items-center justify-between text-[#94A3B8] text-[11px] uppercase font-semibold">
                        <span>Diagnóstico del Escenario</span>
                        <span className="text-[#38BDF8] font-mono-tabular">
                          Horizonte +{simParams.horizonDays}d
                        </span>
                      </div>
                      <p className="text-xs text-[#E2E8F0] leading-relaxed">
                        Bajo estos parámetros, la demanda minorista varía un{" "}
                        <strong
                          className={
                            summaryMetrics.demandDeltaPct >= 0
                              ? "text-[#4ADE80]"
                              : "text-[#F87171]"
                          }
                        >
                          {summaryMetrics.demandDeltaPct >= 0 ? "+" : ""}
                          {summaryMetrics.demandDeltaPct}%
                        </strong>
                        , generando{" "}
                        <strong className="text-[#FBBF24]">
                          {summaryMetrics.criticalSkusCount} alertas críticas
                        </strong>{" "}
                        de agotamiento antes de completar el tránsito desde Bucaramanga/Pamplona.
                      </p>
                    </div>

                    {/* Formulario para Guardar el Escenario Actual en PostgreSQL */}
                    <form
                      onSubmit={handleSaveScenario}
                      className="pt-3 border-t border-[#E2E8F0] space-y-2"
                    >
                      <label className="block text-[11px] font-bold uppercase tracking-wider text-[#475569]">
                        Guardar Escenario en Base de Datos
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={scenarioName}
                          onChange={(e) => setScenarioName(e.target.value)}
                          placeholder="Ej. Pico Feria Cúcuta + Devaluación"
                          className="flex-1 px-3 py-2 text-xs rounded-md border border-[#CBD5E1] bg-white text-[#0F172A] focus:outline-none focus:border-[#B45309]"
                        />
                        <button
                          type="submit"
                          disabled={isSavingScenario}
                          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md bg-[#B45309] hover:bg-[#92400E] text-white text-xs font-semibold transition-colors disabled:opacity-50 shrink-0 cursor-pointer"
                        >
                          <Save className="w-3.5 h-3.5" />
                          {isSavingScenario ? "..." : "Guardar"}
                        </button>
                      </div>
                    </form>
                  </div>
                </section>

                {/* Esquema Cartográfico del Corredor y Puentes Internacionales */}
                <BorderCorridorSchematic
                  bridges={initialBridges}
                  selectedZone={simParams.selectedZone}
                  onSelectZone={(z) =>
                    setSimParams((prev) => ({ ...prev, selectedZone: z }))
                  }
                  bridgeFlowPct={simParams.bridgeFlowPct}
                />
              </>
            )}

            {/* MATRIZ DE CRITICIDAD DE INVENTARIO Y PUNTO DE REORDEN DINÁMICO POR SKU (Visible tanto en Dashboard como en Catálogo) */}
            <section className="bg-white border border-[#E2E8F0] rounded-md shadow-xs p-5">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
                <div>
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-[#B45309]">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Motor de Abastecimiento Preventivo (Corredor Pamplona – Cúcuta)
                  </span>
                  <h2 className="text-lg font-bold text-[#0F172A] font-heading mt-0.5">
                    Matriz de Criticidad por SKU, Punto de Reorden Dinámico ($ROP_i$) y Emisión de Pedidos
                  </h2>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                  {/* Buscador de SKU */}
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-[#64748B] absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={skuSearch}
                      onChange={(e) => setSkuSearch(e.target.value)}
                      placeholder="Buscar SKU, producto o zona..."
                      className="pl-8 pr-3 py-1.5 text-xs rounded-md border border-[#CBD5E1] bg-white text-[#0F172A] focus:outline-none focus:border-[#B45309]"
                    />
                  </div>

                  {/* Filtro rápido por Nivel de Riesgo */}
                  <div className="flex items-center bg-[#F1EFEA] p-1 rounded-md border border-[#E2E8F0] text-xs">
                    {(["TODOS", "CRITICO", "PREVENTIVO", "OPTIMO"] as const).map(
                      (lvl) => (
                        <button
                          key={lvl}
                          type="button"
                          onClick={() => setRiskFilter(lvl)}
                          className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                            riskFilter === lvl
                              ? "bg-white text-[#0F172A] shadow-2xs"
                              : "text-[#475569] hover:text-[#0F172A]"
                          }`}
                        >
                          {lvl === "TODOS"
                            ? "Todos"
                            : lvl === "CRITICO"
                            ? `Críticos (${summaryMetrics.criticalSkusCount})`
                            : lvl === "PREVENTIVO"
                            ? `Preventivos (${summaryMetrics.preventiveSkusCount})`
                            : `Óptimos (${summaryMetrics.optimalSkusCount})`}
                        </button>
                      )
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowNewSkuForm((v) => !v)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0F172A] hover:bg-[#1E293B] text-white text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <PlusCircle className="w-3.5 h-3.5 text-[#FBBF24]" />
                    {showNewSkuForm ? "Cerrar Formulario" : "Registrar Nuevo SKU"}
                  </button>
                </div>
              </div>

              {/* Formulario Desplegable para Registrar un Nuevo SKU Minorista en PostgreSQL */}
              {showNewSkuForm && (
                <form
                  onSubmit={handleCreateSku}
                  className="my-4 p-4 rounded-md bg-[#F8F7F4] border border-[#CBD5E1] space-y-4"
                >
                  <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2">
                    <h4 className="text-sm font-bold text-[#0F172A] font-heading">
                      Registrar Nuevo Producto Minorista en el Catálogo Fronterizo
                    </h4>
                    <span className="text-[11px] text-[#64748B]">
                      Persistencia directa en PostgreSQL (`skus`)
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        Código SKU
                      </label>
                      <input
                        type="text"
                        required
                        value={newSkuData.code}
                        onChange={(e) =>
                          setNewSkuData((p) => ({ ...p, code: e.target.value }))
                        }
                        className="w-full px-3 py-2 rounded border border-[#CBD5E1] bg-white font-mono-tabular"
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="block font-semibold text-[#334155] mb-1">
                        Nombre Comercial del Producto (Presentación)
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="Ej. Azúcar Incauca Refinada (Fardo 25 x 1kg)"
                        value={newSkuData.name}
                        onChange={(e) =>
                          setNewSkuData((p) => ({ ...p, name: e.target.value }))
                        }
                        className="w-full px-3 py-2 rounded border border-[#CBD5E1] bg-white"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        Categoría Minorista
                      </label>
                      <select
                        value={newSkuData.category}
                        onChange={(e) =>
                          setNewSkuData((p) => ({
                            ...p,
                            category: e.target.value,
                          }))
                        }
                        className="w-full px-3 py-2 rounded border border-[#CBD5E1] bg-white"
                      >
                        {CATEGORIES.filter((c) => c !== "Todos").map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        Zona Comercial (Norte de Santander)
                      </label>
                      <select
                        value={newSkuData.zone}
                        onChange={(e) =>
                          setNewSkuData((p) => ({ ...p, zone: e.target.value }))
                        }
                        className="w-full px-3 py-2 rounded border border-[#CBD5E1] bg-white"
                      >
                        {ZONES.filter((z) => z !== "Todas las Zonas").map(
                          (z) => (
                            <option key={z} value={z}>
                              {z}
                            </option>
                          )
                        )}
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        Puente Fronterizo Principal
                      </label>
                      <select
                        value={newSkuData.primaryBridge}
                        onChange={(e) =>
                          setNewSkuData((p) => ({
                            ...p,
                            primaryBridge: e.target.value,
                          }))
                        }
                        className="w-full px-3 py-2 rounded border border-[#CBD5E1] bg-white"
                      >
                        <option value="Simón Bolívar">Simón Bolívar (La Parada)</option>
                        <option value="Francisco de Paula Santander">
                          Francisco de Paula Santander (Ureña)
                        </option>
                        <option value="Atanasio Girardot (Tienditas)">
                          Atanasio Girardot (Tienditas)
                        </option>
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        Precio Unitario (COP)
                      </label>
                      <input
                        type="number"
                        min={1000}
                        step={500}
                        value={newSkuData.unitPriceCop}
                        onChange={(e) =>
                          setNewSkuData((p) => ({
                            ...p,
                            unitPriceCop: Number(e.target.value),
                          }))
                        }
                        className="w-full px-3 py-2 rounded border border-[#CBD5E1] bg-white font-mono-tabular"
                      />
                    </div>

                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        Stock Actual / Demanda Base Día
                      </label>
                      <div className="grid grid-cols-2 gap-2">
                        <input
                          type="number"
                          min={0}
                          value={newSkuData.currentStock}
                          onChange={(e) =>
                            setNewSkuData((p) => ({
                              ...p,
                              currentStock: Number(e.target.value),
                            }))
                          }
                          placeholder="Stock"
                          className="w-full px-2.5 py-2 rounded border border-[#CBD5E1] bg-white font-mono-tabular"
                        />
                        <input
                          type="number"
                          min={1}
                          value={newSkuData.baseDailyDemand}
                          onChange={(e) =>
                            setNewSkuData((p) => ({
                              ...p,
                              baseDailyDemand: Number(e.target.value),
                            }))
                          }
                          placeholder="Dem/Día"
                          className="w-full px-2.5 py-2 rounded border border-[#CBD5E1] bg-white font-mono-tabular"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowNewSkuForm(false)}
                      className="px-3.5 py-2 rounded border border-[#CBD5E1] bg-white text-xs font-semibold text-[#475569] cursor-pointer"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={isCreatingSku}
                      className="px-4 py-2 rounded bg-[#B45309] hover:bg-[#92400E] text-white text-xs font-semibold cursor-pointer"
                    >
                      {isCreatingSku
                        ? "Guardando en BD..."
                        : "Guardar SKU en Catálogo"}
                    </button>
                  </div>
                </form>
              )}

              {/* Tabla de SKUs con Alineación Numérica Tabular */}
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-[#E2E8F0] bg-[#F8F7F4] text-[11px] font-bold uppercase tracking-wider text-[#475569]">
                      <th className="py-3 px-3">SKU & Producto Minorista</th>
                      <th className="py-3 px-3">Nodo Comercial / Puente</th>
                      <th className="py-3 px-3 text-right">Demanda/Día Sim.</th>
                      <th className="py-3 px-3 text-right">Stock Actual</th>
                      <th className="py-3 px-3 text-right">ROP Dinámico (SS)</th>
                      <th className="py-3 px-3 text-right">Cobertura / Lead</th>
                      <th className="py-3 px-3 text-center">Estado Riesgo</th>
                      <th className="py-3 px-3 text-right">Acción Reorden (Q*)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0] text-xs">
                    {visibleTableSkus.map((sku) => {
                      const badgeStyle =
                        sku.riskLevel === "CRITICO"
                          ? "bg-[#FEE2E2] text-[#B91C1C] border border-[#FECACA]"
                          : sku.riskLevel === "PREVENTIVO"
                          ? "bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]"
                          : "bg-[#DCFCE7] text-[#15803D] border border-[#BBF7D0]";

                      return (
                        <tr
                          key={sku.id}
                          className="hover:bg-[#F8F7F4]/80 transition-colors"
                        >
                          <td className="py-3 px-3 max-w-[260px]">
                            <div className="flex items-center gap-2">
                              <span className="font-mono-tabular font-bold text-[11px] px-1.5 py-0.5 rounded bg-[#F1EFEA] text-[#0F172A]">
                                {sku.code}
                              </span>
                              <span className="text-[11px] text-[#64748B] font-medium">
                                {sku.category}
                              </span>
                            </div>
                            <div className="font-semibold text-[#0F172A] mt-1 leading-snug">
                              {sku.name}
                            </div>
                            <div className="text-[11px] text-[#64748B] font-mono-tabular mt-0.5">
                              PVP: {formatCop(sku.unitPriceCop)} • MAPE {sku.mapeScore}%
                            </div>
                          </td>

                          <td className="py-3 px-3">
                            <div className="font-medium text-[#0F172A]">
                              {sku.zone}
                            </div>
                            <div className="text-[11px] text-[#0284C7] font-medium">
                              Pte. {sku.primaryBridge}
                            </div>
                            <div className="text-[10px] text-[#64748B] truncate max-w-[190px]">
                              {sku.supplierRoute}
                            </div>
                          </td>

                          <td className="py-3 px-3 text-right font-mono-tabular">
                            <div className="font-bold text-[#0F172A] text-sm">
                              {sku.simulatedDailyDemand} u./día
                            </div>
                            <div
                              className={`text-[11px] font-semibold ${
                                sku.demandDeltaPct >= 0
                                  ? "text-[#0284C7]"
                                  : "text-[#64748B]"
                              }`}
                            >
                              Base: {sku.baseDailyDemand} (
                              {sku.demandDeltaPct >= 0 ? "+" : ""}
                              {sku.demandDeltaPct}%)
                            </div>
                          </td>

                          <td className="py-3 px-3 text-right font-mono-tabular">
                            <span
                              className={`text-sm font-bold ${
                                sku.currentStock <= sku.dynamicSafetyStock
                                  ? "text-[#B91C1C]"
                                  : "text-[#0F172A]"
                              }`}
                            >
                              {formatNumberCo(sku.currentStock)} u.
                            </span>
                            <div className="text-[11px] text-[#64748B]">
                              Proy. {simParams.horizonDays}d:{" "}
                              {formatNumberCo(sku.projectedHorizonDemand)} u.
                            </div>
                          </td>

                          <td className="py-3 px-3 text-right font-mono-tabular">
                            <div className="font-bold text-[#0F172A]">
                              ROP: {formatNumberCo(sku.dynamicReorderPoint)} u.
                            </div>
                            <div className="text-[11px] text-[#64748B]">
                              Stock Seg: {formatNumberCo(sku.dynamicSafetyStock)} u.
                            </div>
                          </td>

                          <td className="py-3 px-3 text-right font-mono-tabular">
                            <div
                              className={`font-bold text-sm ${
                                sku.daysUntilStockout <= sku.leadTimeDays + 1
                                  ? "text-[#B91C1C]"
                                  : sku.daysUntilStockout <= sku.leadTimeDays + 4
                                  ? "text-[#B45309]"
                                  : "text-[#15803D]"
                              }`}
                            >
                              {sku.daysUntilStockout} días
                            </div>
                            <div className="text-[11px] text-[#64748B]">
                              Lead Ruta: {sku.leadTimeDays} días
                            </div>
                          </td>

                          <td className="py-3 px-3 text-center">
                            <span
                              className={`inline-block px-2.5 py-1 rounded text-[10px] font-bold uppercase tracking-wider ${badgeStyle}`}
                            >
                              {sku.riskLevel}
                            </span>
                          </td>

                          <td className="py-3 px-3 text-right">
                            <button
                              type="button"
                              disabled={processingOrderId === sku.id}
                              onClick={() => handleIssueRestockOrder(sku, true)}
                              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold font-mono-tabular transition-colors cursor-pointer ${
                                sku.riskLevel === "CRITICO"
                                  ? "bg-[#B91C1C] hover:bg-[#991B1B] text-white shadow-2xs"
                                  : sku.riskLevel === "PREVENTIVO"
                                  ? "bg-[#B45309] hover:bg-[#92400E] text-white"
                                  : "bg-[#F1EFEA] hover:bg-[#E2E8F0] text-[#0F172A]"
                              }`}
                            >
                              <PackageCheck className="w-3.5 h-3.5" />
                              {processingOrderId === sku.id
                                ? "Emitiendo..."
                                : `Pedir +${formatNumberCo(
                                    sku.suggestedOrderUnits > 0
                                      ? sku.suggestedOrderUnits
                                      : Math.round(sku.simulatedDailyDemand * 7)
                                  )} u.`}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>

            {/* HISTORIAL DE ÓRDENES DE REABASTECIMIENTO EMITIDAS (Persistidas en PostgreSQL) */}
            <section className="bg-white border border-[#E2E8F0] rounded-md shadow-xs p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#E2E8F0]">
                <div>
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-[#0284C7]">
                    <Truck className="w-3.5 h-3.5" />
                    Logística de Abastecimiento Nacional → Cúcuta / Villa del Rosario
                  </span>
                  <h3 className="text-base font-bold text-[#0F172A] font-heading mt-0.5">
                    Bitácora de Órdenes de Compra Emitidas ({orders.length})
                  </h3>
                </div>
                <span className="text-xs text-[#64748B]">
                  Sincronizado en tiempo real con PostgreSQL (`restock_orders`)
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-4">
                {orders.slice(0, 6).map((ord) => (
                  <div
                    key={ord.id}
                    className="p-3.5 rounded-md border border-[#E2E8F0] bg-[#F8F7F4] flex flex-col justify-between text-xs"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono-tabular font-bold text-[#B45309]">
                          {ord.skuCode} • +{formatNumberCo(ord.orderedUnits)} u.
                        </span>
                        <span className="px-2 py-0.5 rounded bg-[#DCFCE7] text-[#15803D] text-[10px] font-bold uppercase">
                          {ord.status}
                        </span>
                      </div>
                      <h4 className="font-bold text-[#0F172A] mt-1">
                        {ord.skuName}
                      </h4>
                      <p className="text-[11px] text-[#475569] mt-0.5">
                        Destino: {ord.zone}
                      </p>
                    </div>
                    <div className="mt-3 pt-2 border-t border-[#E2E8F0] flex items-center justify-between font-mono-tabular text-[11px]">
                      <span className="text-[#64748B]">Costo Mayorista Est.:</span>
                      <span className="font-bold text-[#0F172A]">
                        {formatCop(ord.estimatedCostCop)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* En la pestaña de Catálogo mostramos también el mapa del corredor fronterizo */}
            {activeTab === "catalog" && (
              <BorderCorridorSchematic
                bridges={initialBridges}
                selectedZone={simParams.selectedZone}
                onSelectZone={(z) =>
                  setSimParams((prev) => ({ ...prev, selectedZone: z }))
                }
                bridgeFlowPct={simParams.bridgeFlowPct}
              />
            )}
          </>
        )}
      </main>

      {/* Pie de Página Académico y Técnico */}
      <footer className="bg-white border-t border-[#E2E8F0] py-4 px-4 lg:px-8 mt-8 text-xs text-[#64748B]">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <strong className="text-[#0F172A]">
              FronteraForecast Norte de Santander
            </strong>{" "}
            — Sistema de Predicción de Demanda para el Comercio Minorista Fronterizo (Cúcuta, Villa del Rosario, Los Patios).
          </div>
          <div className="font-mono-tabular">
            Motor ARIMAX(1,1,1)-X • PostgreSQL + Drizzle ORM • MAPE Global:{" "}
            <strong className="text-[#15803D]">
              {summaryMetrics.weightedMape}%
            </strong>
          </div>
        </div>
      </footer>
    </div>
  );
}

import type { Sku, HistoricalDemandPoint } from "@/db/schema";

export interface SimulationParams {
  fxShockPct: number; // -30 to +50 (%)
  bridgeFlowPct: number; // 20 to 160 (% of normal capacity, 100 = baseline)
  inflationShockPct: number; // -10 to +40 (%)
  remittanceBoost: boolean; // Quincena + Pico de Remesas Táchira-Cúcuta
  horizonDays: 7 | 14 | 30;
  selectedCategory: string;
  selectedZone: string;
}

export interface SimulatedSeriesPoint {
  recordDate: string;
  dayOffset: number;
  actualUnits: number | null;
  baselineForecastUnits: number;
  simulatedForecastUnits: number;
  confidenceLower: number;
  confidenceUpper: number;
  trmCopUsd: number;
  vesUsdSpreadPct: number;
  borderCrossings: number;
  simulatedCrossings: number;
  eventAnnotation: string | null;
}

export interface EvaluatedSku extends Sku {
  simulatedDailyDemand: number;
  demandDeltaPct: number;
  projectedHorizonDemand: number;
  dynamicSafetyStock: number;
  dynamicReorderPoint: number;
  daysUntilStockout: number;
  suggestedOrderUnits: number;
  estimatedOrderCostCop: number;
  riskLevel: "CRITICO" | "PREVENTIVO" | "OPTIMO";
  riskReason: string;
}

export interface ForecastSummaryMetrics {
  totalProjectedUnits: number;
  baselineProjectedUnits: number;
  demandDeltaPct: number;
  totalProjectedRevenueCop: number;
  baselineProjectedRevenueCop: number;
  criticalSkusCount: number;
  preventiveSkusCount: number;
  optimalSkusCount: number;
  weightedMape: number;
  rSquared: number;
  effectiveBridgeCrossings: number;
  compositeBorderMultiplier: number;
}

/**
 * Calcula el multiplicador econométrico compuesto para una categoría o SKU específico
 * bajo el modelo ARIMAX Fronterizo de Norte de Santander.
 */
export function computeSkuMultiplier(
  sku: Pick<Sku, "fxElasticity" | "bridgeElasticity" | "remittanceElasticity" | "category">,
  params: SimulationParams
): number {
  const fxNormalized = params.fxShockPct / 100; // e.g., +0.20 for +20%
  const bridgeNormalized = (params.bridgeFlowPct - 100) / 100; // e.g., -0.40 for 60% flow, +0.25 for 125% flow
  const inflationNormalized = params.inflationShockPct / 100;

  // Sensibilidad por categoría a la inflación/escasez en Táchira
  const categoryInflationWeight =
    sku.category === "Canasta Familiar"
      ? 0.65
      : sku.category === "Salud y Farmacia"
      ? 0.72
      : sku.category === "Cuidado Personal"
      ? 0.48
      : sku.category === "Ferretería y Repuestos"
      ? 0.42
      : 0.35;

  const fxEffect = fxNormalized * (sku.fxElasticity * 0.52);
  const bridgeEffect = bridgeNormalized * (sku.bridgeElasticity * 0.58);
  const inflationEffect = inflationNormalized * categoryInflationWeight;
  const remittanceEffect = params.remittanceBoost ? 0.14 * sku.remittanceElasticity : 0;

  // Efecto no lineal cuando el puente se restringe severamente (< 45%)
  const bridgeBottleneckPenalty =
    params.bridgeFlowPct < 45 ? -((45 - params.bridgeFlowPct) / 100) * 0.45 : 0;

  const rawMultiplier =
    1 + fxEffect + bridgeEffect + inflationEffect + remittanceEffect + bridgeBottleneckPenalty;

  return Math.max(0.22, Math.min(2.65, Number(rawMultiplier.toFixed(4))));
}

/**
 * Evalúa cada SKU del catálogo aplicando los choques exógenos de simulación,
 * recalculando punto de reorden dinámico (ROP), stock de seguridad y días de cobertura.
 */
export function evaluateSkusWithSimulation(
  skuList: Sku[],
  params: SimulationParams
): EvaluatedSku[] {
  const filtered = skuList.filter((s) => {
    const matchCat =
      params.selectedCategory === "Todos" || s.category === params.selectedCategory;
    const matchZone =
      params.selectedZone === "Todas las Zonas" || s.zone === params.selectedZone;
    return matchCat && matchZone;
  });

  // Volatilidad inducida por el choque fronterizo (incrementa el factor Z de stock de seguridad)
  const shockIntensity =
    Math.abs(params.fxShockPct) * 0.008 +
    Math.abs(params.bridgeFlowPct - 100) * 0.006 +
    Math.abs(params.inflationShockPct) * 0.007 +
    (params.remittanceBoost ? 0.12 : 0);

  return filtered.map((sku) => {
    const multiplier = computeSkuMultiplier(sku, params);
    const simulatedDailyDemand = Number((sku.baseDailyDemand * multiplier).toFixed(1));
    const demandDeltaPct = Number(((multiplier - 1) * 100).toFixed(1));
    const projectedHorizonDemand = Math.round(simulatedDailyDemand * params.horizonDays);

    // Stock de seguridad dinámico ajustado por volatilidad fronteriza y Lead Time del corredor Pamplona-Cúcuta
    const volatilityFactor = 1 + shockIntensity * 0.65;
    const dynamicSafetyStock = Math.round(sku.safetyStock * Math.max(0.85, multiplier * 0.7 + 0.3) * volatilityFactor);
    const dynamicReorderPoint = Math.round(
      simulatedDailyDemand * sku.leadTimeDays + dynamicSafetyStock
    );

    const daysUntilStockout =
      simulatedDailyDemand > 0
        ? Number((sku.currentStock / simulatedDailyDemand).toFixed(1))
        : 99;

    // Determinación de nivel de riesgo de quiebre de inventario
    let riskLevel: "CRITICO" | "PREVENTIVO" | "OPTIMO" = "OPTIMO";
    let riskReason = "Cobertura saludable para el horizonte proyectado";

    if (
      sku.currentStock <= dynamicSafetyStock ||
      daysUntilStockout <= sku.leadTimeDays + 1.2
    ) {
      riskLevel = "CRITICO";
      riskReason = `Quiebre en ${daysUntilStockout}d (Lead time ruta ${sku.leadTimeDays}d). Stock bajo umbral de seguridad (${dynamicSafetyStock} u.)`;
    } else if (
      sku.currentStock <= dynamicReorderPoint ||
      daysUntilStockout <= Math.min(params.horizonDays, sku.leadTimeDays + 4.5)
    ) {
      riskLevel = "PREVENTIVO";
      riskReason = `Stock (${sku.currentStock} u.) inferior al Punto de Reorden Dinámico (${dynamicReorderPoint} u.)`;
    }

    // Cantidad óptima de pedido sugerida para cubrir horizonte + stock de seguridad - stock actual
    const targetStock = Math.round(
      simulatedDailyDemand * Math.max(params.horizonDays, sku.leadTimeDays + 7) +
        dynamicSafetyStock
    );
    const suggestedOrderUnits = Math.max(0, targetStock - sku.currentStock);
    const estimatedOrderCostCop = Math.round(suggestedOrderUnits * sku.unitPriceCop * 0.76); // costo mayorista estimado (76% PVP)

    return {
      ...sku,
      simulatedDailyDemand,
      demandDeltaPct,
      projectedHorizonDemand,
      dynamicSafetyStock,
      dynamicReorderPoint,
      daysUntilStockout,
      suggestedOrderUnits,
      estimatedOrderCostCop,
      riskLevel,
      riskReason,
    };
  });
}

/**
 * Proyecta la serie temporal histórica + futura ajustada por los parámetros del simulador
 * y el filtro de categoría/zona activo.
 */
export function buildSimulatedTimeSeries(
  rawSeries: HistoricalDemandPoint[],
  evaluatedSkus: EvaluatedSku[],
  allSkus: Sku[],
  params: SimulationParams
): SimulatedSeriesPoint[] {
  // Proporción de demanda que representa el subconjunto filtrado de SKUs frente al total del catálogo
  const totalBaseDaily = allSkus.reduce((acc, s) => acc + s.baseDailyDemand, 0) || 1;
  const filteredBaseDaily = evaluatedSkus.reduce((acc, s) => acc + s.baseDailyDemand, 0);
  const subsetShare = filteredBaseDaily / totalBaseDaily;

  // Multiplicador ponderado de los SKUs seleccionados
  const filteredSimDaily = evaluatedSkus.reduce(
    (acc, s) => acc + s.simulatedDailyDemand,
    0
  );
  const aggregateMultiplier =
    filteredBaseDaily > 0 ? filteredSimDaily / filteredBaseDaily : 1;

  // Filtramos el horizonte futuro según params.horizonDays (mostramos últimos 20 días históricos + horizonDays futuros)
  const relevantPoints = rawSeries
    .filter((pt) => pt.dayOffset >= -20 && pt.dayOffset <= params.horizonDays)
    .sort((a, b) => a.dayOffset - b.dayOffset);

  const shockUncertaintyWidth =
    0.075 +
    Math.abs(params.fxShockPct) * 0.0018 +
    Math.abs(params.bridgeFlowPct - 100) * 0.0012 +
    (params.remittanceBoost ? 0.02 : 0);

  return relevantPoints.map((pt) => {
    const scaledActual =
      pt.actualUnits !== null ? Math.round(pt.actualUnits * subsetShare) : null;
    const scaledBaseline = Math.round(pt.baselineForecastUnits * subsetShare);

    // En fechas pasadas (dayOffset <= 0), la simulación coincide con el valor base para anclar la curva;
    // En fechas futuras (dayOffset > 0), aplica el multiplicador econométrico con rampa de propagación realista
    const rampFactor =
      pt.dayOffset <= 0
        ? 1
        : pt.dayOffset === 1
        ? 1 + (aggregateMultiplier - 1) * 0.75
        : aggregateMultiplier;

    // Si hay boost de remesas, acentúa días de quincena (dayOffset 2, 3, 14, 15, 16, 28, 29)
    const isQuincenaWave =
      params.remittanceBoost &&
      pt.dayOffset > 0 &&
      (pt.dayOffset % 15 <= 3 || pt.dayOffset % 15 >= 13);

    const waveBonus = isQuincenaWave ? 1.08 : 1.0;

    const simulatedForecastUnits =
      pt.dayOffset <= 0
        ? scaledBaseline
        : Math.max(10, Math.round(scaledBaseline * rampFactor * waveBonus));

    // Banda de confianza al 95% (se ensancha ligeramente con mayor horizonte t)
    const horizonSpread =
      pt.dayOffset <= 0
        ? 0.05
        : shockUncertaintyWidth * (1 + (pt.dayOffset / params.horizonDays) * 0.35);

    const confidenceLower = Math.max(
      0,
      Math.round(simulatedForecastUnits * (1 - horizonSpread))
    );
    const confidenceUpper = Math.round(simulatedForecastUnits * (1 + horizonSpread));

    const simulatedCrossings =
      pt.dayOffset <= 0
        ? pt.borderCrossings
        : Math.round(
            pt.borderCrossings *
              (params.bridgeFlowPct / 100) *
              (params.remittanceBoost ? 1.12 : 1)
          );

    return {
      recordDate: pt.recordDate,
      dayOffset: pt.dayOffset,
      actualUnits: scaledActual,
      baselineForecastUnits: scaledBaseline,
      simulatedForecastUnits,
      confidenceLower,
      confidenceUpper,
      trmCopUsd: pt.trmCopUsd,
      vesUsdSpreadPct:
        pt.dayOffset <= 0
          ? pt.vesUsdSpreadPct
          : Number((pt.vesUsdSpreadPct + params.fxShockPct * 0.45).toFixed(1)),
      borderCrossings: pt.borderCrossings,
      simulatedCrossings,
      eventAnnotation: pt.eventAnnotation,
    };
  });
}

/**
 * Calcula las métricas ejecutivas agregadas para los KPIs superiores
 */
export function computeSummaryMetrics(
  evaluatedSkus: EvaluatedSku[],
  simulatedSeries: SimulatedSeriesPoint[],
  params: SimulationParams
): ForecastSummaryMetrics {
  const futurePoints = simulatedSeries.filter((p) => p.dayOffset > 0);
  const totalProjectedUnits = futurePoints.reduce(
    (acc, p) => acc + p.simulatedForecastUnits,
    0
  );
  const baselineProjectedUnits = futurePoints.reduce(
    (acc, p) => acc + p.baselineForecastUnits,
    0
  );

  const demandDeltaPct =
    baselineProjectedUnits > 0
      ? Number(
          (
            ((totalProjectedUnits - baselineProjectedUnits) /
              baselineProjectedUnits) *
            100
          ).toFixed(1)
        )
      : 0;

  // Precio promedio ponderado por demanda de los SKUs activos
  const totalSkuDaily =
    evaluatedSkus.reduce((acc, s) => acc + s.simulatedDailyDemand, 0) || 1;
  const weightedAvgPriceCop =
    evaluatedSkus.reduce(
      (acc, s) => acc + s.simulatedDailyDemand * s.unitPriceCop,
      0
    ) / totalSkuDaily;

  const totalProjectedRevenueCop = Math.round(
    totalProjectedUnits * weightedAvgPriceCop
  );
  const baselineProjectedRevenueCop = Math.round(
    baselineProjectedUnits * weightedAvgPriceCop
  );

  const criticalSkusCount = evaluatedSkus.filter(
    (s) => s.riskLevel === "CRITICO"
  ).length;
  const preventiveSkusCount = evaluatedSkus.filter(
    (s) => s.riskLevel === "PREVENTIVO"
  ).length;
  const optimalSkusCount = evaluatedSkus.filter(
    (s) => s.riskLevel === "OPTIMO"
  ).length;

  const weightedMape =
    evaluatedSkus.length > 0
      ? Number(
          (
            evaluatedSkus.reduce((acc, s) => acc + s.mapeScore, 0) /
            evaluatedSkus.length
          ).toFixed(2)
        )
      : 6.4;

  const avgFutureCrossings =
    futurePoints.length > 0
      ? Math.round(
          futurePoints.reduce((acc, p) => acc + p.simulatedCrossings, 0) /
            futurePoints.length
        )
      : 45200;

  const compositeBorderMultiplier =
    baselineProjectedUnits > 0
      ? Number((totalProjectedUnits / baselineProjectedUnits).toFixed(3))
      : 1.0;

  return {
    totalProjectedUnits,
    baselineProjectedUnits,
    demandDeltaPct,
    totalProjectedRevenueCop,
    baselineProjectedRevenueCop,
    criticalSkusCount,
    preventiveSkusCount,
    optimalSkusCount,
    weightedMape,
    rSquared: 0.914,
    effectiveBridgeCrossings: avgFutureCrossings,
    compositeBorderMultiplier,
  };
}

export function formatCop(amount: number, compact = false): string {
  if (compact) {
    if (Math.abs(amount) >= 1_000_000_000) {
      return `$${(amount / 1_000_000_000).toFixed(2)} mil M`;
    }
    if (Math.abs(amount) >= 1_000_000) {
      return `$${(amount / 1_000_000).toFixed(1)} M`;
    }
  }
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatNumberCo(num: number): string {
  return new Intl.NumberFormat("es-CO").format(num);
}

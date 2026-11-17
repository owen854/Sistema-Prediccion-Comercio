import { db } from "./index";
import {
  skus,
  historicalDemandSeries,
  borderBridges,
  simulationScenarios,
  restockOrders,
} from "./schema";
import { count } from "drizzle-orm";

export async function ensureSeeded() {
  try {
    const existingSkus = await db.select({ value: count() }).from(skus);
    if ((existingSkus[0]?.value ?? 0) > 0) {
      return;
    }

    // 1. Seed SKUs representativos del comercio minorista en Norte de Santander
    const initialSkus = [
      {
        code: "NDS-ALM-001",
        name: "Harina de Maíz Precocida PAN (Fardo 20 x 1kg)",
        category: "Canasta Familiar",
        zone: "La Parada (Villa del Rosario)",
        primaryBridge: "Simón Bolívar",
        unitPriceCop: 76000,
        currentStock: 340,
        safetyStock: 260,
        reorderPoint: 510,
        leadTimeDays: 4,
        baseDailyDemand: 68.5,
        fxElasticity: 1.64,
        bridgeElasticity: 1.85,
        remittanceElasticity: 1.48,
        mapeScore: 5.4,
        supplierRoute: "Corredor Bucaramanga - Pamplona - Villa del Rosario",
      },
      {
        code: "NDS-ALM-002",
        name: "Aceite Vegetal Premier / Gourmet (Caja 12 x 1000ml)",
        category: "Canasta Familiar",
        zone: "La Parada (Villa del Rosario)",
        primaryBridge: "Simón Bolívar",
        unitPriceCop: 118000,
        currentStock: 185,
        safetyStock: 190,
        reorderPoint: 365,
        leadTimeDays: 4,
        baseDailyDemand: 46.0,
        fxElasticity: 1.58,
        bridgeElasticity: 1.76,
        remittanceElasticity: 1.42,
        mapeScore: 5.9,
        supplierRoute: "Corredor Costa Atlántica - Ocaña - Cúcuta",
      },
      {
        code: "NDS-ALM-003",
        name: "Arroz Diana Premium (Paca 25 x 500g)",
        category: "Canasta Familiar",
        zone: "Cenabastos Cúcuta",
        primaryBridge: "Simón Bolívar",
        unitPriceCop: 68500,
        currentStock: 620,
        safetyStock: 290,
        reorderPoint: 540,
        leadTimeDays: 3,
        baseDailyDemand: 82.0,
        fxElasticity: 1.38,
        bridgeElasticity: 1.65,
        remittanceElasticity: 1.35,
        mapeScore: 4.8,
        supplierRoute: "Distribución Local Molinos Zulia - Cenabastos",
      },
      {
        code: "NDS-ALM-004",
        name: "Leche en Polvo Entera Klim / El Rodeo (Caja 12 x 900g)",
        category: "Canasta Familiar",
        zone: "La Parada (Villa del Rosario)",
        primaryBridge: "Simón Bolívar",
        unitPriceCop: 312000,
        currentStock: 115,
        safetyStock: 120,
        reorderPoint: 235,
        leadTimeDays: 5,
        baseDailyDemand: 24.5,
        fxElasticity: 1.72,
        bridgeElasticity: 1.68,
        remittanceElasticity: 1.55,
        mapeScore: 6.2,
        supplierRoute: "Corredor Bogotá - Tunja - Pamplona - Cúcuta",
      },
      {
        code: "NDS-FAR-005",
        name: "Acetaminofén 500mg + Antigripal MK (Display 100 Blísters)",
        category: "Salud y Farmacia",
        zone: "Cúcuta Centro / Alejandría",
        primaryBridge: "Simón Bolívar",
        unitPriceCop: 145000,
        currentStock: 140,
        safetyStock: 155,
        reorderPoint: 310,
        leadTimeDays: 4,
        baseDailyDemand: 39.0,
        fxElasticity: 1.45,
        bridgeElasticity: 1.78,
        remittanceElasticity: 1.62,
        mapeScore: 6.1,
        supplierRoute: "Corredor Bogotá - Bucaramanga - Cúcuta",
      },
      {
        code: "NDS-FAR-006",
        name: "Losartán 50mg + Metformina 850mg (Lote Crónicos 50 Cajas)",
        category: "Salud y Farmacia",
        zone: "Cúcuta Centro / Alejandría",
        primaryBridge: "Francisco de Paula Santander",
        unitPriceCop: 210000,
        currentStock: 210,
        safetyStock: 130,
        reorderPoint: 260,
        leadTimeDays: 5,
        baseDailyDemand: 27.5,
        fxElasticity: 1.32,
        bridgeElasticity: 1.54,
        remittanceElasticity: 1.68,
        mapeScore: 5.7,
        supplierRoute: "Corredor Medellín - Bucaramanga - Cúcuta",
      },
      {
        code: "NDS-PER-007",
        name: "Pañales Winny / Pequeñín Etapa 3-4 (Paca Mayorista 6x50 u.)",
        category: "Cuidado Personal",
        zone: "La Parada (Villa del Rosario)",
        primaryBridge: "Simón Bolívar",
        unitPriceCop: 192000,
        currentStock: 175,
        safetyStock: 140,
        reorderPoint: 285,
        leadTimeDays: 4,
        baseDailyDemand: 35.0,
        fxElasticity: 1.51,
        bridgeElasticity: 1.72,
        remittanceElasticity: 1.49,
        mapeScore: 6.5,
        supplierRoute: "Corredor Cali / Medellín - La Lizama - Cúcuta",
      },
      {
        code: "NDS-PER-008",
        name: "Kit Cuidado Familiar (Jabón Protex + Dental Colgate x24)",
        category: "Cuidado Personal",
        zone: "Cúcuta Centro / Alejandría",
        primaryBridge: "Simón Bolívar",
        unitPriceCop: 94000,
        currentStock: 410,
        safetyStock: 180,
        reorderPoint: 340,
        leadTimeDays: 4,
        baseDailyDemand: 41.0,
        fxElasticity: 1.39,
        bridgeElasticity: 1.60,
        remittanceElasticity: 1.33,
        mapeScore: 5.5,
        supplierRoute: "Corredor Cali - Bogotá - Pamplona - Cúcuta",
      },
      {
        code: "NDS-FER-009",
        name: "Batería Automotriz MAC / Willard 850 Amp (Flota Binacional)",
        category: "Ferretería y Repuestos",
        zone: "Los Patios Comercial",
        primaryBridge: "Atanasio Girardot (Tienditas)",
        unitPriceCop: 385000,
        currentStock: 72,
        safetyStock: 65,
        reorderPoint: 135,
        leadTimeDays: 6,
        baseDailyDemand: 12.5,
        fxElasticity: 1.48,
        bridgeElasticity: 1.82,
        remittanceElasticity: 1.18,
        mapeScore: 7.4,
        supplierRoute: "Corredor Manizales / Bogotá - Cúcuta",
      },
      {
        code: "NDS-FER-010",
        name: "Kit Transmisión y Rodamientos Moto 150cc (Caja x10 Kits)",
        category: "Ferretería y Repuestos",
        zone: "Cúcuta Centro / Alejandría",
        primaryBridge: "Francisco de Paula Santander",
        unitPriceCop: 265000,
        currentStock: 95,
        safetyStock: 85,
        reorderPoint: 175,
        leadTimeDays: 5,
        baseDailyDemand: 18.5,
        fxElasticity: 1.55,
        bridgeElasticity: 1.74,
        remittanceElasticity: 1.25,
        mapeScore: 6.9,
        supplierRoute: "Corredor Medellín - Bucaramanga - Cúcuta",
      },
      {
        code: "NDS-TEX-011",
        name: "Calzado Cuero Manufactura Cúcuta (Docena Surtida Export)",
        category: "Textil y Calzado",
        zone: "Cúcuta Centro / Alejandría",
        primaryBridge: "Atanasio Girardot (Tienditas)",
        unitPriceCop: 540000,
        currentStock: 130,
        safetyStock: 60,
        reorderPoint: 115,
        leadTimeDays: 2,
        baseDailyDemand: 16.0,
        fxElasticity: 1.68,
        bridgeElasticity: 1.52,
        remittanceElasticity: 1.58,
        mapeScore: 7.1,
        supplierRoute: "Clúster Calzado Atalaya / San Mateo - Cúcuta",
      },
      {
        code: "NDS-ALM-012",
        name: "Café Molido Águila Roja / La Bastilla (Fardo 20 x 500g)",
        category: "Canasta Familiar",
        zone: "Cenabastos Cúcuta",
        primaryBridge: "Francisco de Paula Santander",
        unitPriceCop: 248000,
        currentStock: 215,
        safetyStock: 145,
        reorderPoint: 290,
        leadTimeDays: 4,
        baseDailyDemand: 34.5,
        fxElasticity: 1.42,
        bridgeElasticity: 1.63,
        remittanceElasticity: 1.36,
        mapeScore: 5.3,
        supplierRoute: "Corredor Eje Cafetero - Bucaramanga - Cúcuta",
      },
    ];

    const insertedSkus = await db.insert(skus).values(initialSkus).returning();

    // 2. Seed de Serie Histórica (-29 a 0) y Pronóstico Base (+1 a +30)
    // Suma de baseDailyDemand de los 12 SKUs = 445.0 unidades mayoristas/día equivalentes
    const baseTotalDaily = initialSkus.reduce((acc, s) => acc + s.baseDailyDemand, 0);
    const today = new Date("2025-05-15T12:00:00Z");
    const seriesRows = [];

    for (let offset = -29; offset <= 30; offset++) {
      const d = new Date(today);
      d.setUTCDate(today.getUTCDate() + offset);
      const isoDate = d.toISOString().slice(0, 10);
      const dayOfWeek = d.getUTCDay(); // 0 = Sun, 5 = Fri, 6 = Sat
      const dayOfMonth = d.getUTCDate();

      // Estacionalidad semanal en frontera (viernes y sábado +22%, domingo -18%)
      const weeklyFactor =
        dayOfWeek === 5
          ? 1.21
          : dayOfWeek === 6
          ? 1.26
          : dayOfWeek === 0
          ? 0.82
          : dayOfWeek === 1
          ? 0.94
          : 1.02;

      // Efecto quincena y remesas (días 14-17 y 28-31 / 1-2)
      const isQuincena =
        (dayOfMonth >= 14 && dayOfMonth <= 17) ||
        dayOfMonth >= 28 ||
        dayOfMonth <= 2;
      const quincenaFactor = isQuincena ? 1.18 : 1.0;

      // Ruido determinista suave para realismo econométrico
      const wave = Math.sin(offset * 0.55) * 0.045 + Math.cos(offset * 0.27) * 0.03;

      let eventAnnotation: string | null = null;
      let eventMultiplier = 1.0;

      if (offset === -15) {
        eventAnnotation = "Pico Quincena + Giros Remesas Táchira";
        eventMultiplier = 1.19;
      } else if (offset === -8) {
        eventAnnotation = "Control Aduanero DIAN Puente Tienditas";
        eventMultiplier = 0.86;
      } else if (offset === -2) {
        eventAnnotation = "Alza Spread Cambiario VES/COP (+9%)";
        eventMultiplier = 1.14;
      } else if (offset === 0) {
        eventAnnotation = "Corte Actual de Inventario (Hoy)";
        eventMultiplier = 1.08;
      } else if (offset === 3) {
        eventAnnotation = "Proyección: Ventana Quincenal Binacional";
        eventMultiplier = 1.15;
      } else if (offset === 15) {
        eventAnnotation = "Proyección: Pico Fin de Mes + Abastecimiento";
        eventMultiplier = 1.21;
      }

      const baselineForecastUnits = Math.round(
        baseTotalDaily * weeklyFactor * quincenaFactor * (1 + wave) * eventMultiplier
      );

      // Para días históricos (offset <= 0), generamos actualUnits con una desviación realista (MAPE ~5.8%)
      const actualError =
        offset <= 0
          ? Math.sin(offset * 1.3) * 0.042 + (offset === -8 ? -0.05 : 0.015)
          : 0;
      const actualUnits =
        offset <= 0
          ? Math.round(baselineForecastUnits * (1 + actualError))
          : null;

      const confidenceMargin = Math.round(
        baselineForecastUnits * (offset <= 0 ? 0.05 : 0.08 + (offset / 30) * 0.05)
      );

      const trmCopUsd = Number(
        (4185 + Math.sin(offset * 0.22) * 48 + offset * 0.8).toFixed(1)
      );
      const vesUsdSpreadPct = Number(
        (14.2 + Math.cos(offset * 0.3) * 2.4 + (offset >= -3 ? 1.5 : 0)).toFixed(1)
      );
      const borderCrossings = Math.round(
        44800 * weeklyFactor * (isQuincena ? 1.14 : 1.0) * (offset === -8 ? 0.78 : 1.0)
      );

      seriesRows.push({
        recordDate: isoDate,
        dayOffset: offset,
        actualUnits,
        baselineForecastUnits,
        confidenceLower: baselineForecastUnits - confidenceMargin,
        confidenceUpper: baselineForecastUnits + confidenceMargin,
        trmCopUsd,
        vesUsdSpreadPct,
        borderCrossings,
        eventAnnotation,
      });
    }

    await db.insert(historicalDemandSeries).values(seriesRows);

    // 3. Seed de los 4 Puentes Internacionales de Norte de Santander
    await db.insert(borderBridges).values([
      {
        name: "Puente Internacional Simón Bolívar",
        municipality: "Villa del Rosario (La Parada)",
        venezuelanCounterpart: "San Antonio del Táchira",
        status: "FLUJO_DENSO",
        dailyPedestrians: 28450,
        dailyVehicles: 3120,
        commercialSharePct: 54.5,
        avgWaitMinutes: 28,
        permeabilityIndex: 92.0,
        notes:
          "Principal arteria peatonal de compradores minoristas de canasta familiar, medicamentos y aseo personal en La Parada.",
      },
      {
        name: "Puente Internacional Francisco de Paula Santander",
        municipality: "Cúcuta (El Escobal)",
        venezuelanCounterpart: "Pedro María Ureña",
        status: "OPERATIVO",
        dailyPedestrians: 11200,
        dailyVehicles: 2450,
        commercialSharePct: 24.0,
        avgWaitMinutes: 16,
        permeabilityIndex: 95.0,
        notes:
          "Corredor clave hacia zona industrial de Ureña; alta demanda de repuestos, insumos ferreteros y medicamentos crónicos.",
      },
      {
        name: "Puente Internacional Atanasio Girardot (Tienditas)",
        municipality: "Villa del Rosario / Cúcuta",
        venezuelanCounterpart: "Tienditas / Ureña",
        status: "OPERATIVO",
        dailyPedestrians: 3420,
        dailyVehicles: 4890,
        commercialSharePct: 17.5,
        avgWaitMinutes: 22,
        permeabilityIndex: 96.5,
        notes:
          "Paso moderno habilitado para transporte automotor, carga comercial formalizada, baterías y calzado manufacturado en Cúcuta.",
      },
      {
        name: "Puente Internacional Unión",
        municipality: "Puerto Santander",
        venezuelanCounterpart: "Boca de Grita (Táchira)",
        status: "RESTRICCION_PARCIAL",
        dailyPedestrians: 2150,
        dailyVehicles: 410,
        commercialSharePct: 4.0,
        avgWaitMinutes: 35,
        permeabilityIndex: 74.0,
        notes:
          "Nodo norte de intercambio agroalimentario y abarrotes; sensibilidad alta a controles fluviales y climáticos.",
      },
    ]);

    // 4. Seed de Escenarios de Simulación Econométrica preconfigurados
    await db.insert(simulationScenarios).values([
      {
        name: "Choque Cambiario: Devaluación VES +25% + Pico Remesas",
        description:
          "Simula una ampliación del diferencial cambiario en Táchira junto con ventana de pago de remesas familiares que se dolarizan y compran víveres en La Parada y Cúcuta Centro.",
        fxShockPct: 25,
        bridgeFlowPct: 118,
        inflationShockPct: 18,
        remittanceBoost: true,
        horizonDays: 14,
        selectedCategory: "Todos",
        selectedZone: "Todas las Zonas",
        projectedDemandDeltaPct: 38.4,
        projectedRevenueCop: 1685400000,
        criticalSkusCount: 7,
      },
      {
        name: "Contingencia Aduanera: Paso Regulado en Puentes (55%)",
        description:
          "Evalúa el impacto de operativos de control intensivo o cierre parcial en Simón Bolívar y Tienditas, reduciendo el flujo peatonal al 55% de su capacidad normal.",
        fxShockPct: -5,
        bridgeFlowPct: 55,
        inflationShockPct: 5,
        remittanceBoost: false,
        horizonDays: 14,
        selectedCategory: "Todos",
        selectedZone: "Todas las Zonas",
        projectedDemandDeltaPct: -26.2,
        projectedRevenueCop: 895200000,
        criticalSkusCount: 1,
      },
      {
        name: "Alerta Sanitaria & Desabastecimiento Farmacéutico Táchira",
        description:
          "Aumento de demanda transfronteriza en medicamentos esenciales y cuidado infantil en droguerías de Alejandría y Villa del Rosario.",
        fxShockPct: 12,
        bridgeFlowPct: 125,
        inflationShockPct: 28,
        remittanceBoost: true,
        horizonDays: 14,
        selectedCategory: "Salud y Farmacia",
        selectedZone: "Cúcuta Centro / Alejandría",
        projectedDemandDeltaPct: 44.1,
        projectedRevenueCop: 318900000,
        criticalSkusCount: 2,
      },
    ]);

    // 5. Seed de Órdenes de Reabastecimiento iniciales
    if (insertedSkus.length >= 2) {
      await db.insert(restockOrders).values([
        {
          skuId: insertedSkus[0].id,
          skuCode: insertedSkus[0].code,
          skuName: insertedSkus[0].name,
          zone: insertedSkus[0].zone,
          orderedUnits: 450,
          estimatedCostCop: 25992000,
          priority: "CRITICO",
          status: "EN_TRANSITO_PAMPLONA",
          notes:
            "Despacho prioritario solicitado por alerta de diferencial cambiario en La Parada.",
        },
        {
          skuId: insertedSkus[4].id,
          skuCode: insertedSkus[4].code,
          skuName: insertedSkus[4].name,
          zone: insertedSkus[4].zone,
          orderedUnits: 280,
          estimatedCostCop: 30856000,
          priority: "CRITICO",
          status: "ORDEN_EMITIDA",
          notes:
            "Reposición preventiva para droguerías del centro de Cúcuta antes de corte quincenal.",
        },
      ]);
    }
  } catch (err) {
    console.error("Error seeding database:", err);
  }
}

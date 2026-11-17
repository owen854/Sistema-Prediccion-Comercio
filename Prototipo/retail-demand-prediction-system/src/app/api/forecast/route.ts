import { NextRequest, NextResponse } from "next/server";
import { db } from "@/db";
import {
  skus,
  historicalDemandSeries,
  borderBridges,
  simulationScenarios,
  restockOrders,
} from "@/db/schema";
import { ensureSeeded } from "@/db/seed";
import { asc, desc } from "drizzle-orm";

export async function GET() {
  try {
    await ensureSeeded();

    const [skuList, seriesList, bridgeList, scenarioList, orderList] =
      await Promise.all([
        db.select().from(skus).orderBy(asc(skus.id)),
        db
          .select()
          .from(historicalDemandSeries)
          .orderBy(asc(historicalDemandSeries.dayOffset)),
        db.select().from(borderBridges).orderBy(asc(borderBridges.id)),
        db
          .select()
          .from(simulationScenarios)
          .orderBy(desc(simulationScenarios.createdAt)),
        db.select().from(restockOrders).orderBy(desc(restockOrders.createdAt)),
      ]);

    return NextResponse.json({
      skus: skuList,
      historicalSeries: seriesList,
      bridges: bridgeList,
      scenarios: scenarioList,
      restockOrders: orderList,
      macroSnapshot: {
        trmCopUsd: 4185.0,
        trmChange24hPct: 0.65,
        vesUsdBcv: 56.75,
        vesUsdParalelo: 64.8,
        vesUsdSpreadPct: 14.2,
        copVesImplicitRate: 64.6,
        totalDailyBridgeCrossings: bridgeList.reduce(
          (acc, b) => acc + b.dailyPedestrians + b.dailyVehicles,
          0
        ),
        activeCorridorStatus: "OPERATIVO - FLUJO ALTO EN LA PARADA",
        lastUpdated: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error("Error in GET /api/forecast:", error);
    return NextResponse.json(
      { error: "Error al cargar los datos del sistema de predicción fronteriza." },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      name,
      description,
      fxShockPct,
      bridgeFlowPct,
      inflationShockPct,
      remittanceBoost,
      horizonDays,
      selectedCategory,
      selectedZone,
      projectedDemandDeltaPct,
      projectedRevenueCop,
      criticalSkusCount,
    } = body;

    if (!name || typeof name !== "string") {
      return NextResponse.json(
        { error: "El nombre del escenario es obligatorio." },
        { status: 400 }
      );
    }

    const [created] = await db
      .insert(simulationScenarios)
      .values({
        name: name.trim(),
        description:
          description?.trim() ||
          "Escenario de simulación econométrica generado desde la consola de mando.",
        fxShockPct: Number(fxShockPct ?? 0),
        bridgeFlowPct: Number(bridgeFlowPct ?? 100),
        inflationShockPct: Number(inflationShockPct ?? 0),
        remittanceBoost: Boolean(remittanceBoost),
        horizonDays: Number(horizonDays ?? 14),
        selectedCategory: selectedCategory || "Todos",
        selectedZone: selectedZone || "Todas las Zonas",
        projectedDemandDeltaPct: Number(projectedDemandDeltaPct ?? 0),
        projectedRevenueCop: Math.round(Number(projectedRevenueCop ?? 0)),
        criticalSkusCount: Number(criticalSkusCount ?? 0),
      })
      .returning();

    return NextResponse.json({ scenario: created }, { status: 201 });
  } catch (error) {
    console.error("Error in POST /api/forecast:", error);
    return NextResponse.json(
      { error: "No se pudo guardar el escenario de simulación." },
      { status: 500 }
    );
  }
}

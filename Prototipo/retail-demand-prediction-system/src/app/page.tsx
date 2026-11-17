import React from "react";
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
import { FronteraForecastDashboard } from "@/components/FronteraForecastDashboard";

export const dynamic = "force-dynamic";

export default async function HomePage() {
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

  const macroSnapshot = {
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
    activeCorridorStatus: "OPERATIVO • FLUJO ALTO EN LA PARADA",
    lastUpdated: new Date().toISOString(),
  };

  return (
    <FronteraForecastDashboard
      initialSkus={skuList}
      initialSeries={seriesList}
      initialBridges={bridgeList}
      initialScenarios={scenarioList}
      initialOrders={orderList}
      macroSnapshot={macroSnapshot}
    />
  );
}

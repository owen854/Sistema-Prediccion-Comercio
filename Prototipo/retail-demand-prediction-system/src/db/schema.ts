import {
  pgTable,
  serial,
  varchar,
  integer,
  real,
  bigint,
  boolean,
  text,
  timestamp,
} from "drizzle-orm/pg-core";

export const skus = pgTable("skus", {
  id: serial("id").primaryKey(),
  code: varchar("code", { length: 32 }).notNull().unique(),
  name: varchar("name", { length: 160 }).notNull(),
  category: varchar("category", { length: 64 }).notNull(),
  zone: varchar("zone", { length: 80 }).notNull(),
  primaryBridge: varchar("primary_bridge", { length: 80 }).notNull(),
  unitPriceCop: integer("unit_price_cop").notNull(),
  currentStock: integer("current_stock").notNull(),
  safetyStock: integer("safety_stock").notNull(),
  reorderPoint: integer("reorder_point").notNull(),
  leadTimeDays: integer("lead_time_days").notNull(),
  baseDailyDemand: real("base_daily_demand").notNull(),
  fxElasticity: real("fx_elasticity").notNull(),
  bridgeElasticity: real("bridge_elasticity").notNull(),
  remittanceElasticity: real("remittance_elasticity").notNull(),
  mapeScore: real("mape_score").notNull(),
  supplierRoute: varchar("supplier_route", { length: 120 }).notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const historicalDemandSeries = pgTable("historical_demand_series", {
  id: serial("id").primaryKey(),
  recordDate: varchar("record_date", { length: 16 }).notNull(),
  dayOffset: integer("day_offset").notNull(), // negative for past (-29..0), positive for future (1..30)
  actualUnits: integer("actual_units"),
  baselineForecastUnits: integer("baseline_forecast_units").notNull(),
  confidenceLower: integer("confidence_lower").notNull(),
  confidenceUpper: integer("confidence_upper").notNull(),
  trmCopUsd: real("trm_cop_usd").notNull(),
  vesUsdSpreadPct: real("ves_usd_spread_pct").notNull(),
  borderCrossings: integer("border_crossings").notNull(),
  eventAnnotation: varchar("event_annotation", { length: 120 }),
});

export const borderBridges = pgTable("border_bridges", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 100 }).notNull(),
  municipality: varchar("municipality", { length: 80 }).notNull(),
  venezuelanCounterpart: varchar("venezuelan_counterpart", { length: 80 }).notNull(),
  status: varchar("status", { length: 32 }).notNull(), // OPERATIVO | FLUJO_DENSO | RESTRICCION_PARCIAL
  dailyPedestrians: integer("daily_pedestrians").notNull(),
  dailyVehicles: integer("daily_vehicles").notNull(),
  commercialSharePct: real("commercial_share_pct").notNull(),
  avgWaitMinutes: integer("avg_wait_minutes").notNull(),
  permeabilityIndex: real("permeability_index").notNull(), // 0 - 100
  notes: text("notes").notNull(),
});

export const simulationScenarios = pgTable("simulation_scenarios", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 120 }).notNull(),
  description: text("description").notNull(),
  fxShockPct: real("fx_shock_pct").notNull(),
  bridgeFlowPct: real("bridge_flow_pct").notNull(),
  inflationShockPct: real("inflation_shock_pct").notNull(),
  remittanceBoost: boolean("remittance_boost").notNull().default(false),
  horizonDays: integer("horizon_days").notNull().default(14),
  selectedCategory: varchar("selected_category", { length: 64 }).notNull().default("Todos"),
  selectedZone: varchar("selected_zone", { length: 80 }).notNull().default("Todas las Zonas"),
  projectedDemandDeltaPct: real("projected_demand_delta_pct").notNull(),
  projectedRevenueCop: bigint("projected_revenue_cop", { mode: "number" }).notNull(),
  criticalSkusCount: integer("critical_skus_count").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const restockOrders = pgTable("restock_orders", {
  id: serial("id").primaryKey(),
  skuId: integer("sku_id").notNull(),
  skuCode: varchar("sku_code", { length: 32 }).notNull(),
  skuName: varchar("sku_name", { length: 160 }).notNull(),
  zone: varchar("zone", { length: 80 }).notNull(),
  orderedUnits: integer("ordered_units").notNull(),
  estimatedCostCop: bigint("estimated_cost_cop", { mode: "number" }).notNull(),
  priority: varchar("priority", { length: 32 }).notNull(), // CRITICO | PREVENTIVO | OPTIMO
  status: varchar("status", { length: 40 }).notNull(), // ORDEN_EMITIDA | EN_TRANSITO_PAMPLONA | RECIBIDO
  notes: text("notes").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type Sku = typeof skus.$inferSelect;
export type NewSku = typeof skus.$inferInsert;
export type HistoricalDemandPoint = typeof historicalDemandSeries.$inferSelect;
export type BorderBridge = typeof borderBridges.$inferSelect;
export type SimulationScenario = typeof simulationScenarios.$inferSelect;
export type RestockOrder = typeof restockOrders.$inferSelect;

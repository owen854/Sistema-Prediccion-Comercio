import { NextRequest, NextResponse } from "next/server";
import { db } from "@/db";
import { skus, restockOrders } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { action } = body;

    if (action === "RESTOCK_ORDER") {
      const {
        skuId,
        skuCode,
        skuName,
        zone,
        orderedUnits,
        estimatedCostCop,
        priority,
        notes,
        applyToStockImmediately,
      } = body;

      if (!skuId || !orderedUnits || orderedUnits <= 0) {
        return NextResponse.json(
          { error: "Datos de orden de reabastecimiento inválidos." },
          { status: 400 }
        );
      }

      const [order] = await db
        .insert(restockOrders)
        .values({
          skuId: Number(skuId),
          skuCode: String(skuCode),
          skuName: String(skuName),
          zone: String(zone),
          orderedUnits: Number(orderedUnits),
          estimatedCostCop: Math.round(Number(estimatedCostCop ?? 0)),
          priority: String(priority || "CRITICO"),
          status: applyToStockImmediately ? "RECIBIDO" : "ORDEN_EMITIDA",
          notes:
            notes ||
            "Orden generada automáticamente desde el Motor de Predicción Fronteriza.",
        })
        .returning();

      let updatedSku = null;
      if (applyToStockImmediately) {
        const existing = await db
          .select()
          .from(skus)
          .where(eq(skus.id, Number(skuId)));
        if (existing.length > 0) {
          const newStock = existing[0].currentStock + Number(orderedUnits);
          const [res] = await db
            .update(skus)
            .set({ currentStock: newStock, updatedAt: new Date() })
            .where(eq(skus.id, Number(skuId)))
            .returning();
          updatedSku = res;
        }
      }

      return NextResponse.json(
        { order, updatedSku },
        { status: 201 }
      );
    }

    if (action === "CREATE_SKU") {
      const {
        code,
        name,
        category,
        zone,
        primaryBridge,
        unitPriceCop,
        currentStock,
        safetyStock,
        leadTimeDays,
        baseDailyDemand,
        fxElasticity,
        bridgeElasticity,
        remittanceElasticity,
        supplierRoute,
      } = body;

      if (!code || !name || !category || !zone) {
        return NextResponse.json(
          { error: "Código, nombre, categoría y zona comercial son requeridos." },
          { status: 400 }
        );
      }

      const daily = Number(baseDailyDemand || 25);
      const lead = Number(leadTimeDays || 4);
      const safety = Number(safetyStock || Math.round(daily * 2.5));
      const reorderPoint = Math.round(daily * lead + safety);

      const [createdSku] = await db
        .insert(skus)
        .values({
          code: String(code).trim().toUpperCase(),
          name: String(name).trim(),
          category: String(category),
          zone: String(zone),
          primaryBridge: String(primaryBridge || "Simón Bolívar"),
          unitPriceCop: Math.round(Number(unitPriceCop || 85000)),
          currentStock: Math.round(Number(currentStock || 200)),
          safetyStock: safety,
          reorderPoint,
          leadTimeDays: lead,
          baseDailyDemand: daily,
          fxElasticity: Number(fxElasticity || 1.45),
          bridgeElasticity: Number(bridgeElasticity || 1.65),
          remittanceElasticity: Number(remittanceElasticity || 1.35),
          mapeScore: 5.8,
          supplierRoute:
            supplierRoute || "Corredor Bucaramanga - Pamplona - Cúcuta",
        })
        .returning();

      return NextResponse.json({ sku: createdSku }, { status: 201 });
    }

    return NextResponse.json({ error: "Acción no reconocida." }, { status: 400 });
  } catch (error) {
    console.error("Error in POST /api/skus:", error);
    return NextResponse.json(
      { error: "Error procesando la solicitud en el catálogo de SKUs." },
      { status: 500 }
    );
  }
}

export async function PATCH(req: NextRequest) {
  try {
    const body = await req.json();
    const { id, currentStock, safetyStock, unitPriceCop } = body;

    if (!id) {
      return NextResponse.json({ error: "ID de SKU requerido." }, { status: 400 });
    }

    const updateData: Record<string, unknown> = { updatedAt: new Date() };
    if (typeof currentStock === "number") updateData.currentStock = Math.max(0, Math.round(currentStock));
    if (typeof safetyStock === "number") updateData.safetyStock = Math.max(0, Math.round(safetyStock));
    if (typeof unitPriceCop === "number") updateData.unitPriceCop = Math.max(100, Math.round(unitPriceCop));

    const [updated] = await db
      .update(skus)
      .set(updateData)
      .where(eq(skus.id, Number(id)))
      .returning();

    return NextResponse.json({ sku: updated });
  } catch (error) {
    console.error("Error in PATCH /api/skus:", error);
    return NextResponse.json(
      { error: "No se pudo actualizar el SKU." },
      { status: 500 }
    );
  }
}

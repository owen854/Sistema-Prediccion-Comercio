"use client";

import React from "react";
import type { BorderBridge } from "@/db/schema";
import { formatNumberCo } from "@/lib/forecast-engine";
import { MapPin, Users, Truck, Clock, ArrowLeftRight } from "lucide-react";

interface BorderCorridorSchematicProps {
  bridges: BorderBridge[];
  selectedZone: string;
  onSelectZone: (zone: string) => void;
  bridgeFlowPct: number;
}

const COMMERCIAL_ZONES = [
  {
    name: "La Parada (Villa del Rosario)",
    shortLabel: "La Parada • Villa del Rosario",
    x: 245,
    y: 195,
    mainFocus: "Canasta Familiar, Víveres y Aseo",
    bridgeLink: "Puente Simón Bolívar",
  },
  {
    name: "Cúcuta Centro / Alejandría",
    shortLabel: "Cúcuta Centro • Alejandría",
    x: 135,
    y: 135,
    mainFocus: "Salud/Farmacia, Calzado, Textil y Repuestos",
    bridgeLink: "Simón Bolívar & Fco. de Paula",
  },
  {
    name: "Cenabastos Cúcuta",
    shortLabel: "Cenabastos • Zona Norte",
    x: 155,
    y: 72,
    mainFocus: "Mayorista-Minorista Granos, Café y Aceites",
    bridgeLink: "Fco. de Paula & Tienditas",
  },
  {
    name: "Los Patios Comercial",
    shortLabel: "Los Patios • Corredor Sur",
    x: 115,
    y: 215,
    mainFocus: "Ferretería, Baterías y Automotor",
    bridgeLink: "Corredor Metropolitano",
  },
];

export function BorderCorridorSchematic({
  bridges,
  selectedZone,
  onSelectZone,
  bridgeFlowPct,
}: BorderCorridorSchematicProps) {
  const flowMultiplier = bridgeFlowPct / 100;

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-md shadow-xs p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-[#E2E8F0]">
        <div>
          <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-[#0284C7]">
            <ArrowLeftRight className="w-3.5 h-3.5" />
            Cartografía Operativa del Eje Binacional
          </span>
          <h3 className="text-base font-bold text-[#0F172A] font-heading mt-0.5">
            Pasos Fronterizos (Río Táchira) y Nodos Comerciales de Norte de Santander
          </h3>
        </div>
        {selectedZone !== "Todas las Zonas" && (
          <button
            type="button"
            onClick={() => onSelectZone("Todas las Zonas")}
            className="text-xs font-semibold text-[#B45309] hover:underline self-start sm:self-auto cursor-pointer"
          >
            Restablecer filtro: Ver todas las zonas
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 mt-4 items-center">
        {/* Esquema Cartográfico Vectorial SVG (Columna 5/12) */}
        <div className="xl:col-span-5 bg-[#F8F7F4] border border-[#E2E8F0] rounded-md p-3">
          <div className="flex items-center justify-between text-[11px] text-[#475569] mb-2 font-medium">
            <span>🇨🇴 NORTE DE SANTANDER (COL)</span>
            <span className="text-[#0284C7] font-mono-tabular">RÍO TÁCHIRA</span>
            <span>🇻🇪 ESTADO TÁCHIRA (VEN)</span>
          </div>

          <svg
            viewBox="0 0 460 265"
            className="w-full h-auto rounded border border-[#E2E8F0] bg-[#F1EFEA]"
          >
            {/* Territorio Colombia (Izquierda) y Venezuela (Derecha) */}
            <rect x="0" y="0" width="295" height="265" fill="#F8F7F4" />
            <rect x="295" y="0" width="165" height="265" fill="#EFECE6" />

            {/* Vías Logísticas desde el Interior (Pamplona / Bucaramanga) */}
            <path
              d="M 15 245 Q 75 225 115 215 L 135 135 L 155 72"
              fill="none"
              stroke="#CBD5E1"
              strokeWidth="4"
              strokeLinecap="round"
            />
            <path
              d="M 135 135 L 245 195"
              fill="none"
              stroke="#CBD5E1"
              strokeWidth="3.5"
            />

            {/* Río Táchira (Línea Fronteriza Natural) */}
            <path
              d="M 285 0 C 275 55, 305 105, 290 155 C 280 195, 302 230, 292 265"
              fill="none"
              stroke="#0284C7"
              strokeWidth="6"
              strokeOpacity="0.35"
            />
            <path
              d="M 285 0 C 275 55, 305 105, 290 155 C 280 195, 302 230, 292 265"
              fill="none"
              stroke="#0284C7"
              strokeWidth="2"
              strokeDasharray="5 3"
            />

            {/* 4 Puentes Internacionales (Cruces sobre el Río Táchira) */}
            {/* 1. Puente Unión (Norte - Puerto Santander) */}
            <g>
              <line
                x1="260"
                y1="34"
                x2="320"
                y2="34"
                stroke="#D97706"
                strokeWidth="4"
              />
              <circle cx="290" cy="34" r="5" fill="#D97706" stroke="#FFF" strokeWidth="1.5" />
              <text x="326" y="37" className="text-[9px] fill-[#334155] font-semibold">
                Pte. Unión (Boca de Grita)
              </text>
            </g>

            {/* 2. Puente Francisco de Paula Santander (Ureña) */}
            <g>
              <line
                x1="155"
                y1="72"
                x2="325"
                y2="92"
                stroke="#94A3B8"
                strokeWidth="1.5"
                strokeDasharray="3 3"
              />
              <line
                x1="265"
                y1="92"
                x2="325"
                y2="92"
                stroke="#15803D"
                strokeWidth="5"
              />
              <circle cx="295" cy="92" r="5.5" fill="#15803D" stroke="#FFF" strokeWidth="1.5" />
              <text x="330" y="90" className="text-[9px] fill-[#0F172A] font-bold">
                Pte. Fco. de Paula
              </text>
              <text x="330" y="100" className="text-[8px] fill-[#64748B]">
                El Escobal ↔ Ureña
              </text>
            </g>

            {/* 3. Puente Atanasio Girardot - Tienditas */}
            <g>
              <line
                x1="265"
                y1="142"
                x2="325"
                y2="142"
                stroke="#0284C7"
                strokeWidth="5"
              />
              <circle cx="292" cy="142" r="5.5" fill="#0284C7" stroke="#FFF" strokeWidth="1.5" />
              <text x="330" y="140" className="text-[9px] fill-[#0F172A] font-bold">
                Pte. Tienditas (Carga)
              </text>
              <text x="330" y="150" className="text-[8px] fill-[#64748B]">
                Atanasio Girardot
              </text>
            </g>

            {/* 4. Puente Internacional Simón Bolívar (Principal) */}
            <g>
              <line
                x1="245"
                y1="195"
                x2="325"
                y2="195"
                stroke="#B45309"
                strokeWidth="6"
              />
              <circle cx="290" cy="195" r="6.5" fill="#B45309" stroke="#FFF" strokeWidth="2" />
              <text x="330" y="193" className="text-[9.5px] fill-[#B45309] font-bold">
                Pte. Simón Bolívar
              </text>
              <text x="330" y="204" className="text-[8px] fill-[#475569] font-medium">
                La Parada ↔ San Antonio
              </text>
            </g>

            {/* Nodos de Zonas Comerciales Interactivas en Norte de Santander */}
            {COMMERCIAL_ZONES.map((z) => {
              const isSelected = selectedZone === z.name;
              return (
                <g
                  key={z.name}
                  className="cursor-pointer"
                  onClick={() =>
                    onSelectZone(isSelected ? "Todas las Zonas" : z.name)
                  }
                >
                  {isSelected && (
                    <circle
                      cx={z.x}
                      cy={z.y}
                      r={15}
                      fill="#B45309"
                      fillOpacity="0.18"
                    />
                  )}
                  <circle
                    cx={z.x}
                    cy={z.y}
                    r={isSelected ? 8.5 : 7}
                    fill={isSelected ? "#B45309" : "#0F172A"}
                    stroke="#FFFFFF"
                    strokeWidth="2"
                  />
                  <rect
                    x={z.x - 68}
                    y={z.y - 26}
                    width={136}
                    height={16}
                    rx={3}
                    fill={isSelected ? "#B45309" : "#FFFFFF"}
                    stroke={isSelected ? "#B45309" : "#CBD5E1"}
                    strokeWidth="1"
                  />
                  <text
                    x={z.x}
                    y={z.y - 15}
                    textAnchor="middle"
                    className={`text-[8.5px] font-bold ${
                      isSelected ? "fill-white" : "fill-[#0F172A]"
                    }`}
                  >
                    {z.shortLabel}
                  </text>
                </g>
              );
            })}

            {/* Etiqueta Ruta de Abastecimiento Interior */}
            <text x="12" y="256" className="text-[8.5px] fill-[#64748B] font-mono-tabular">
              ← Ruta Abastecimiento: Bucaramanga / Pamplona
            </text>
          </svg>

          <p className="text-[11px] text-[#64748B] mt-2 flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-[#B45309] shrink-0" />
            <span>
              Haga clic en un nodo comercial del mapa para filtrar el pronóstico y los SKUs por zona.
            </span>
          </p>
        </div>

        {/* Tarjetas de Estado Operativo de los 4 Puentes Internacionales (Columna 7/12) */}
        <div className="xl:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {bridges.map((bridge) => {
            const simPedestrians = Math.round(
              bridge.dailyPedestrians * flowMultiplier
            );
            const simVehicles = Math.round(bridge.dailyVehicles * flowMultiplier);

            const statusBadge =
              bridgeFlowPct < 60
                ? {
                    label: "PASO RESTRINGIDO",
                    bg: "bg-[#FEE2E2] text-[#B91C1C]",
                  }
                : bridge.status === "FLUJO_DENSO" || bridgeFlowPct > 115
                ? {
                    label: "FLUJO ALTO COMERCIAL",
                    bg: "bg-[#FEF3C7] text-[#B45309]",
                  }
                : bridge.status === "RESTRICCION_PARCIAL"
                ? {
                    label: "CONTROL ADUANERO",
                    bg: "bg-[#FEF3C7] text-[#D97706]",
                  }
                : {
                    label: "OPERATIVO NORMAL",
                    bg: "bg-[#DCFCE7] text-[#15803D]",
                  };

            return (
              <div
                key={bridge.id}
                className="p-3.5 rounded-md border border-[#E2E8F0] bg-[#F8F7F4]/60 hover:bg-white transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-sm font-bold text-[#0F172A] leading-snug">
                      {bridge.name}
                    </h4>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider shrink-0 ${statusBadge.bg}`}
                    >
                      {statusBadge.label}
                    </span>
                  </div>
                  <p className="text-xs text-[#475569] mt-0.5">
                    {bridge.municipality} ↔{" "}
                    <span className="font-medium text-[#0F172A]">
                      {bridge.venezuelanCounterpart}
                    </span>
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2 my-3 pt-2.5 border-t border-[#E2E8F0] text-xs">
                  <div>
                    <span className="text-[10px] text-[#64748B] flex items-center gap-1 uppercase">
                      <Users className="w-3 h-3 text-[#B45309]" /> Peatones/Día
                    </span>
                    <span className="font-mono-tabular font-bold text-[#0F172A] text-sm">
                      {formatNumberCo(simPedestrians)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#64748B] flex items-center gap-1 uppercase">
                      <Truck className="w-3 h-3 text-[#0284C7]" /> Vehículos/Día
                    </span>
                    <span className="font-mono-tabular font-bold text-[#0F172A] text-sm">
                      {formatNumberCo(simVehicles)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#64748B] flex items-center gap-1 uppercase">
                      <Clock className="w-3 h-3 text-[#475569]" /> Peso Comercial
                    </span>
                    <span className="font-mono-tabular font-bold text-[#B45309] text-sm">
                      {bridge.commercialSharePct}%
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-[#475569] leading-relaxed">
                  {bridge.notes}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

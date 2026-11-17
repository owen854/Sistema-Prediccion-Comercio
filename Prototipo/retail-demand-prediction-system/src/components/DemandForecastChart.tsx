"use client";

import React, { useState } from "react";
import type { SimulatedSeriesPoint } from "@/lib/forecast-engine";
import { formatNumberCo } from "@/lib/forecast-engine";
import { Activity, Calendar, TrendingUp, AlertCircle } from "lucide-react";

interface DemandForecastChartProps {
  series: SimulatedSeriesPoint[];
  horizonDays: 7 | 14 | 30;
  onHorizonChange: (h: 7 | 14 | 30) => void;
  selectedCategory: string;
  selectedZone: string;
}

export function DemandForecastChart({
  series,
  horizonDays,
  onHorizonChange,
  selectedCategory,
  selectedZone,
}: DemandForecastChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (!series || series.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center bg-[#F8F7F4] rounded-md border border-[#E2E8F0] text-sm text-[#475569]">
        Sin datos de serie temporal para los filtros seleccionados.
      </div>
    );
  }

  // Dimensiones del lienzo SVG
  const width = 920;
  const height = 340;
  const padLeft = 58;
  const padRight = 24;
  const padTop = 28;
  const padBottom = 42;
  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  // Escala Y dinámica con margen de respiro del 12%
  const allValues: number[] = [];
  series.forEach((pt) => {
    if (pt.actualUnits !== null) allValues.push(pt.actualUnits);
    allValues.push(pt.baselineForecastUnits);
    allValues.push(pt.simulatedForecastUnits);
    allValues.push(pt.confidenceUpper);
    allValues.push(pt.confidenceLower);
  });

  const rawMin = Math.min(...allValues, 0);
  const rawMax = Math.max(...allValues, 100);
  const yMin = Math.max(0, Math.floor((rawMin * 0.85) / 10) * 10);
  const yMax = Math.ceil((rawMax * 1.1) / 10) * 10 || 100;

  const getX = (idx: number) => {
    if (series.length <= 1) return padLeft;
    return padLeft + (idx / (series.length - 1)) * plotW;
  };

  const getY = (val: number) => {
    const ratio = (val - yMin) / Math.max(1, yMax - yMin);
    return padTop + plotH - ratio * plotH;
  };

  // Índices donde termina el pasado (dayOffset === 0) y empieza el pronóstico
  const todayIdx = series.findIndex((p) => p.dayOffset === 0);
  const splitX = todayIdx >= 0 ? getX(todayIdx) : padLeft + plotW * 0.5;

  // Construcción de rutas SVG
  // 1. Curva Histórica Real (dayOffset <= 0)
  const actualPoints = series
    .map((pt, idx) =>
      pt.actualUnits !== null ? { x: getX(idx), y: getY(pt.actualUnits), idx } : null
    )
    .filter((p): p is { x: number; y: number; idx: number } => p !== null);

  const actualPath = actualPoints
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  // 2. Curva Pronóstico Base (completa para mostrar ajuste histórico + futuro base)
  const baselinePath = series
    .map(
      (pt, i) =>
        `${i === 0 ? "M" : "L"} ${getX(i).toFixed(1)} ${getY(
          pt.baselineForecastUnits
        ).toFixed(1)}`
    )
    .join(" ");

  // 3. Curva Pronóstico Simulado (desde dayOffset >= 0)
  const forecastPoints = series
    .map((pt, idx) =>
      pt.dayOffset >= 0
        ? {
            x: getX(idx),
            y: getY(pt.simulatedForecastUnits),
            upperY: getY(pt.confidenceUpper),
            lowerY: getY(pt.confidenceLower),
            idx,
          }
        : null
    )
    .filter(
      (
        p
      ): p is {
        x: number;
        y: number;
        upperY: number;
        lowerY: number;
        idx: number;
      } => p !== null
    );

  const simulatedPath = forecastPoints
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  // 4. Polígono de Banda de Confianza al 95% (futuro)
  const confidenceAreaPath =
    forecastPoints.length > 1
      ? [
          ...forecastPoints.map(
            (p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.upperY.toFixed(1)}`
          ),
          ...[...forecastPoints]
            .reverse()
            .map((p) => `L ${p.x.toFixed(1)} ${p.lowerY.toFixed(1)}`),
          "Z",
        ].join(" ")
      : "";

  // Ticks del eje Y
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) =>
    Math.round(yMin + t * (yMax - yMin))
  );

  // Punto activo en hover (o el día de hoy por defecto)
  const activeIdx =
    hoveredIndex !== null
      ? hoveredIndex
      : todayIdx >= 0
      ? todayIdx
      : series.length - 1;
  const activePoint = series[activeIdx] || series[0];

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-md shadow-xs p-5">
      {/* Cabecera del Gráfico */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-4 border-b border-[#E2E8F0]">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[11px] font-semibold uppercase tracking-wider bg-[#B45309]/10 text-[#B45309]">
              <Activity className="w-3.5 h-3.5" />
              Modelo Híbrido ARIMAX(1,1,1) + Variables Exógenas
            </span>
            <span className="text-xs text-[#64748B] font-mono-tabular">
              IC 95% • {selectedCategory} • {selectedZone}
            </span>
          </div>
          <h2 className="text-lg font-bold text-[#0F172A] mt-1 font-heading">
            Curva de Demanda Histórica vs. Proyección bajo Choques Fronterizos (Unidades/Día)
          </h2>
        </div>

        {/* Selector de Horizonte Temporal */}
        <div className="flex items-center gap-1.5 bg-[#F1EFEA] p-1 rounded-md border border-[#E2E8F0] self-start">
          <span className="text-xs font-medium text-[#475569] px-2 flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-[#B45309]" />
            Horizonte:
          </span>
          {([7, 14, 30] as const).map((h) => (
            <button
              key={h}
              type="button"
              onClick={() => onHorizonChange(h)}
              className={`px-3 py-1.5 rounded text-xs font-semibold font-mono-tabular transition-colors cursor-pointer ${
                horizonDays === h
                  ? "bg-[#B45309] text-white shadow-xs"
                  : "text-[#475569] hover:text-[#0F172A] hover:bg-white/60"
              }`}
            >
              +{h} Días
            </button>
          ))}
        </div>
      </div>

      {/* Cinta de Inspección en Tiempo Real del Punto Seleccionado */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 my-3 p-3 rounded-md bg-[#F8F7F4] border border-[#E2E8F0] text-xs">
        <div>
          <span className="text-[#64748B] block text-[11px] uppercase tracking-wider">
            Fecha ({activePoint.dayOffset === 0 ? "HOY" : activePoint.dayOffset > 0 ? `T+${activePoint.dayOffset}` : `T${activePoint.dayOffset}`})
          </span>
          <span className="font-mono-tabular font-semibold text-[#0F172A] text-sm">
            {activePoint.recordDate}
          </span>
        </div>
        <div>
          <span className="text-[#64748B] block text-[11px] uppercase tracking-wider">
            Demanda Real
          </span>
          <span className="font-mono-tabular font-semibold text-[#0F172A] text-sm">
            {activePoint.actualUnits !== null
              ? `${formatNumberCo(activePoint.actualUnits)} u.`
              : "Proyección Futura"}
          </span>
        </div>
        <div>
          <span className="text-[#64748B] block text-[11px] uppercase tracking-wider">
            Pronóstico Base
          </span>
          <span className="font-mono-tabular font-semibold text-[#475569] text-sm">
            {formatNumberCo(activePoint.baselineForecastUnits)} u.
          </span>
        </div>
        <div>
          <span className="text-[#0284C7] block text-[11px] font-semibold uppercase tracking-wider">
            Pronóstico Simulado
          </span>
          <span className="font-mono-tabular font-bold text-[#0284C7] text-sm">
            {formatNumberCo(activePoint.simulatedForecastUnits)} u.
          </span>
        </div>
        <div>
          <span className="text-[#64748B] block text-[11px] uppercase tracking-wider">
            Banda IC 95%
          </span>
          <span className="font-mono-tabular font-medium text-[#475569] text-sm">
            [{formatNumberCo(activePoint.confidenceLower)} – {formatNumberCo(activePoint.confidenceUpper)}]
          </span>
        </div>
        <div>
          <span className="text-[#64748B] block text-[11px] uppercase tracking-wider">
            Cruces Puentes / Spread VES
          </span>
          <span className="font-mono-tabular font-semibold text-[#B45309] text-sm">
            {formatNumberCo(activePoint.simulatedCrossings)} • {activePoint.vesUsdSpreadPct}%
          </span>
        </div>
      </div>

      {/* Lienzo SVG Principal */}
      <div className="relative w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto select-none overflow-visible"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <defs>
            <linearGradient id="confidenceRibbon" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0284C7" stopOpacity="0.24" />
              <stop offset="100%" stopColor="#0284C7" stopOpacity="0.05" />
            </linearGradient>
            <linearGradient id="futureZoneBg" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#0284C7" stopOpacity="0.04" />
              <stop offset="100%" stopColor="#B45309" stopOpacity="0.06" />
            </linearGradient>
          </defs>

          {/* Zona Sombreada de Proyección Futura */}
          <rect
            x={splitX}
            y={padTop}
            width={Math.max(0, width - padRight - splitX)}
            height={plotH}
            fill="url(#futureZoneBg)"
          />

          {/* Líneas Horizontales de Retícula + Etiquetas Eje Y */}
          {yTicks.map((tickVal, i) => {
            const yPos = getY(tickVal);
            return (
              <g key={i}>
                <line
                  x1={padLeft}
                  y1={yPos}
                  x2={width - padRight}
                  y2={yPos}
                  stroke="#E2E8F0"
                  strokeDasharray={i === 0 ? undefined : "3 3"}
                  strokeWidth="1"
                />
                <text
                  x={padLeft - 8}
                  y={yPos + 4}
                  textAnchor="end"
                  className="fill-[#64748B] text-[10px] font-mono-tabular"
                >
                  {formatNumberCo(tickVal)}
                </text>
              </g>
            );
          })}

          {/* Línea Divisoria Vertical "HOY (Corte de Inventario)" */}
          {todayIdx >= 0 && (
            <g>
              <line
                x1={splitX}
                y1={padTop}
                x2={splitX}
                y2={padTop + plotH}
                stroke="#B45309"
                strokeWidth="1.5"
                strokeDasharray="4 3"
              />
              <rect
                x={splitX - 46}
                y={padTop - 18}
                width={92}
                height={16}
                rx={3}
                fill="#B45309"
              />
              <text
                x={splitX}
                y={padTop - 7}
                textAnchor="middle"
                className="fill-white text-[9px] font-bold uppercase tracking-wider"
              >
                HOY • PRONÓSTICO →
              </text>
            </g>
          )}

          {/* Polígono de Intervalo de Confianza al 95% */}
          {confidenceAreaPath && (
            <path d={confidenceAreaPath} fill="url(#confidenceRibbon)" />
          )}

          {/* Curva de Pronóstico Base (Gris Pizarra) */}
          <path
            d={baselinePath}
            fill="none"
            stroke="#94A3B8"
            strokeWidth="1.75"
            strokeDasharray="3 3"
          />

          {/* Curva de Demanda Histórica Real (Obsidiana Sólida) */}
          {actualPath && (
            <path
              d={actualPath}
              fill="none"
              stroke="#0F172A"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Curva de Pronóstico Simulado con Choques Exógenos (Cian Río Táchira) */}
          {simulatedPath && (
            <path
              d={simulatedPath}
              fill="none"
              stroke="#0284C7"
              strokeWidth="2.8"
              strokeDasharray="6 3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Nodos de Eventos Fronterizos Destacados */}
          {series.map((pt, idx) => {
            if (!pt.eventAnnotation) return null;
            const cx = getX(idx);
            const cy =
              pt.dayOffset <= 0 && pt.actualUnits !== null
                ? getY(pt.actualUnits)
                : getY(pt.simulatedForecastUnits);
            return (
              <g key={`evt-${idx}`}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={4.5}
                  fill="#B45309"
                  stroke="#FFFFFF"
                  strokeWidth="1.5"
                />
              </g>
            );
          })}

          {/* Línea Guía de Hover Activo */}
          {activeIdx >= 0 && (
            <g>
              <line
                x1={getX(activeIdx)}
                y1={padTop}
                x2={getX(activeIdx)}
                y2={padTop + plotH}
                stroke="#0F172A"
                strokeOpacity="0.25"
                strokeWidth="1"
              />
              {activePoint.actualUnits !== null && (
                <circle
                  cx={getX(activeIdx)}
                  cy={getY(activePoint.actualUnits)}
                  r={5}
                  fill="#0F172A"
                  stroke="#FFFFFF"
                  strokeWidth="2"
                />
              )}
              {activePoint.dayOffset >= 0 && (
                <circle
                  cx={getX(activeIdx)}
                  cy={getY(activePoint.simulatedForecastUnits)}
                  r={5.5}
                  fill="#0284C7"
                  stroke="#FFFFFF"
                  strokeWidth="2"
                />
              )}
            </g>
          )}

          {/* Etiquetas del Eje X (Fechas espaciadas) */}
          {series.map((pt, idx) => {
            const step = series.length > 35 ? 5 : series.length > 25 ? 4 : 3;
            if (idx % step !== 0 && pt.dayOffset !== 0) return null;
            const xPos = getX(idx);
            return (
              <text
                key={`xlab-${idx}`}
                x={xPos}
                y={height - 12}
                textAnchor="middle"
                className={`text-[10px] font-mono-tabular ${
                  pt.dayOffset === 0
                    ? "fill-[#B45309] font-bold"
                    : "fill-[#64748B]"
                }`}
              >
                {pt.recordDate.slice(5)}
              </text>
            );
          })}

          {/* Franjas Invisibles para Interacción Fluida con el Ratón */}
          {series.map((_, idx) => {
            const colW = plotW / series.length;
            return (
              <rect
                key={`hit-${idx}`}
                x={getX(idx) - colW / 2}
                y={padTop}
                width={colW}
                height={plotH}
                fill="transparent"
                className="cursor-crosshair"
                onMouseEnter={() => setHoveredIndex(idx)}
              />
            );
          })}
        </svg>
      </div>

      {/* Leyenda y Anotación de Eventos Fronterizos */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-3 mt-2 border-t border-[#E2E8F0] text-xs">
        <div className="flex flex-wrap items-center gap-5">
          <div className="flex items-center gap-2">
            <span className="w-5 h-0.5 bg-[#0F172A] inline-block" />
            <span className="text-[#0F172A] font-medium">
              Demanda Real Histórica (POS Cúcuta)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-5 h-0.5 border-b-2 border-dashed border-[#0284C7] inline-block" />
            <span className="text-[#0284C7] font-semibold">
              Pronóstico Simulado (Choques Fronterizos)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-5 h-0.5 border-b border-dashed border-[#94A3B8] inline-block" />
            <span className="text-[#64748B]">Pronóstico Base (Sin Choque)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-2.5 bg-[#0284C7]/20 border border-[#0284C7]/40 rounded-xs inline-block" />
            <span className="text-[#64748B]">Banda de Confianza IC 95%</span>
          </div>
        </div>

        {activePoint.eventAnnotation ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#FEF3C7] text-[#B45309] font-medium">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>Hito en Fecha: {activePoint.eventAnnotation}</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-[#64748B]">
            <TrendingUp className="w-3.5 h-3.5 text-[#0284C7]" />
            <span>Pase el cursor sobre la curva para inspeccionar tasas y cruces diarios</span>
          </div>
        )}
      </div>
    </div>
  );
}

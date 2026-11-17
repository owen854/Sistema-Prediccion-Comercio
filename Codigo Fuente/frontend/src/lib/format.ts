// Formato de moneda y números para Colombia (migrado de forecast-engine.ts del prototipo).

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

export function formatNumberCo(value: number, maximumFractionDigits = 0): string {
  return new Intl.NumberFormat("es-CO", { maximumFractionDigits }).format(value);
}

export function formatPercent(value: number, fractionDigits = 1): string {
  return `${value.toFixed(fractionDigits).replace(".", ",")} %`;
}

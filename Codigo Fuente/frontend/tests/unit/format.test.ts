import { describe, expect, it } from "vitest";

import { formatCop, formatNumberCo, formatPercent } from "@/lib/format";
import { findNavItem, NAV_ITEMS } from "@/lib/navigation";

describe("formato colombiano", () => {
  it("formatea pesos sin decimales", () => {
    expect(formatCop(1234567)).toMatch(/1\.234\.567/);
  });

  it("compacta millones y miles de millones", () => {
    expect(formatCop(2_500_000, true)).toBe("$2.5 M");
    expect(formatCop(1_250_000_000, true)).toBe("$1.25 mil M");
  });

  it("usa punto de miles y coma decimal", () => {
    expect(formatNumberCo(12345.678, 1)).toBe("12.345,7");
    expect(formatPercent(3.82, 2)).toBe("3,82 %");
  });
});

describe("navegación", () => {
  it("cada vista tiene requerimientos y fase", () => {
    for (const item of NAV_ITEMS) {
      expect(item.requirements).not.toHaveLength(0);
      expect(item.phase).not.toHaveLength(0);
    }
  });

  it("falla con rutas no configuradas", () => {
    expect(() => findNavItem("/no-existe")).toThrow(/NAV_ITEMS/);
  });
});

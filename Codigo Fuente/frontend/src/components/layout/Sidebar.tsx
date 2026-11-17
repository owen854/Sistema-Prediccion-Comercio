"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  Boxes,
  Cpu,
  Database,
  FlaskConical,
  LayoutDashboard,
  LineChart,
  SlidersHorizontal,
  type LucideIcon,
} from "lucide-react";

import { NAV_ITEMS } from "@/lib/navigation";

const ICONS: Record<string, LucideIcon> = {
  "/": LayoutDashboard,
  "/pronosticos": LineChart,
  "/inventario": Boxes,
  "/patrones": BarChart3,
  "/escenarios": SlidersHorizontal,
  "/datos": Database,
  "/modelos": FlaskConical,
  "/rendimiento": Cpu,
  "/metodologia": BookOpen,
};

export function Sidebar() {
  const pathname = usePathname();
  return (
    <nav aria-label="Navegación principal" className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const Icon = ICONS[item.href] ?? LayoutDashboard;
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              active
                ? "bg-[#B45309]/10 text-[#92400E]"
                : "text-[#475569] hover:bg-white hover:text-[#0F172A]"
            }`}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

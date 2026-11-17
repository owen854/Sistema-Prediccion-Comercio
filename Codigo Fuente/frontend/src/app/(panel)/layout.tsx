import type { ReactNode } from "react";

import { ApiStatus } from "@/components/layout/ApiStatus";
import { Sidebar } from "@/components/layout/Sidebar";

export default function PanelLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen md:grid md:grid-cols-[240px_1fr]">
      <aside className="border-b border-[#E2E8F0] bg-[#F1F0EC] p-4 md:min-h-screen md:border-r md:border-b-0">
        <div className="mb-6 flex flex-col gap-1 px-3">
          <span className="text-xs font-bold tracking-wider text-[#B45309] uppercase">
            Norte de Santander
          </span>
          <span className="font-heading text-lg leading-tight font-bold">Predicción de Demanda</span>
        </div>
        <Sidebar />
      </aside>
      <div className="flex min-w-0 flex-col">
        <div className="flex items-center justify-end border-b border-[#E2E8F0] bg-white px-4 py-2 sm:px-6">
          <ApiStatus />
        </div>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">{children}</main>
        <footer className="border-t border-[#E2E8F0] px-4 py-3 text-xs text-[#64748B] sm:px-6">
          Los pronósticos son resultados automatizados de apoyo a la decisión; la decisión final es
          del comerciante.
        </footer>
      </div>
    </div>
  );
}

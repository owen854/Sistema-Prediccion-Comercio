import { Database } from "lucide-react";

import { ApiStatus } from "@/components/layout/ApiStatus";
import { PageHeader } from "@/components/ui/PageHeader";
import { findNavItem } from "@/lib/navigation";

export default function PanelPrincipal() {
  const item = findNavItem("/");
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title={item.label} description={item.description} />

      <section className="rounded-md border border-[#E2E8F0] bg-white p-5">
        <h2 className="mb-3 text-sm font-semibold text-[#0F172A]">Estado del sistema</h2>
        <ApiStatus detailed />
      </section>

      <section className="flex items-start gap-4 rounded-md border border-dashed border-[#CBD5E1] bg-white p-6">
        <Database className="mt-0.5 h-5 w-5 shrink-0 text-[#B45309]" aria-hidden />
        <div className="flex flex-col gap-1 text-sm text-[#475569]">
          <p className="font-semibold text-[#0F172A]">Todavía no hay pronósticos.</p>
          <p>
            Aparecerán aquí cuando se carguen datos de ventas (Fase 1) y se entrene y publique un
            modelo (Fase 2). Cada cifra indicará su origen de datos y el modelo que la produjo.
          </p>
        </div>
      </section>
    </div>
  );
}

import { Hammer } from "lucide-react";

import { PageHeader } from "@/components/ui/PageHeader";
import { findNavItem } from "@/lib/navigation";

/**
 * Vista aún no implementada. Muestra qué hará, qué requerimientos atiende y en qué
 * fase se construye. Nunca muestra cifras de ejemplo (regla "ninguna cifra sin origen").
 */
export function PendingView({ href }: { href: string }) {
  const item = findNavItem(href);
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title={item.label} description={item.description} />
      <section className="flex items-start gap-4 rounded-md border border-dashed border-[#CBD5E1] bg-white p-6">
        <Hammer className="mt-0.5 h-5 w-5 shrink-0 text-[#B45309]" aria-hidden />
        <div className="flex flex-col gap-1 text-sm">
          <p className="font-semibold text-[#0F172A]">Esta vista está en construcción.</p>
          <p className="text-[#475569]">
            Se implementa en la <strong>{item.phase}</strong> y atiende los requerimientos{" "}
            <span className="font-mono-tabular">{item.requirements}</span>.
          </p>
          <p className="text-[#475569]">
            Mostrará solo resultados calculados por el sistema a partir de datos cargados.
          </p>
        </div>
      </section>
    </div>
  );
}

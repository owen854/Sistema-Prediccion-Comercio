import { DatosView } from "@/components/datos/DatosView";
import { PageHeader } from "@/components/ui/PageHeader";
import { findNavItem } from "@/lib/navigation";

export default function DatosPage() {
  const item = findNavItem("/datos");
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title={item.label} description={item.description} />
      <DatosView />
    </div>
  );
}

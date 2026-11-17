import type { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <header className="flex flex-col gap-2 border-b border-[#E2E8F0] pb-5">
      <h1 className="text-2xl font-bold text-[#0F172A]">{title}</h1>
      <p className="max-w-2xl text-sm text-[#475569]">{description}</p>
      {children}
    </header>
  );
}

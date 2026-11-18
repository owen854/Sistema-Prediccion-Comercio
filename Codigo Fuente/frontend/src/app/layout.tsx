import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Predicción de Demanda — Comercio Fronterizo",
  description:
    "Pronósticos de demanda y recomendaciones de inventario para MIPYMES del comercio minorista de Norte de Santander.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-[#F8F7F4] text-[#0F172A] antialiased">{children}</body>
    </html>
  );
}

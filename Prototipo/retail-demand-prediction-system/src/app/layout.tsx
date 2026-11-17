import type { Metadata } from "next";
import type { ReactNode } from "react";
import {
  Space_Grotesk,
  Plus_Jakarta_Sans,
  JetBrains_Mono,
} from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-heading",
});

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title:
    "FronteraForecast NdS | Sistema de Predicción de Demanda Minorista Fronteriza - Norte de Santander",
  description:
    "Plataforma econométrica ARIMAX y simulador de choques cambiarios (COP/USD/VES) y tránsito en puentes internacionales para el comercio minorista en Cúcuta, Villa del Rosario y Los Patios.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="es"
      className={`${spaceGrotesk.variable} ${plusJakarta.variable} ${jetbrainsMono.variable}`}
    >
      <body className="bg-[#F8F7F4] text-[#0F172A] antialiased selection:bg-[#B45309]/15 selection:text-[#B45309]">
        {children}
      </body>
    </html>
  );
}

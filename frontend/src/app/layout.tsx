import type { Metadata, Viewport } from "next";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";
import { Navbar } from "@/components/navigation/navbar";
import { OfflineBanner } from "@/components/offline/offline-banner";
import { RealtimeListener } from "@/components/realtime/realtime-listener";

export const metadata: Metadata = {
  title: "DeskFlow — Gestão Inteligente de Espaços Híbridos",
  description:
    "Plataforma completa de agendamento de postos e salas com check-in via QR Code dinâmico, cotas por centro de custo, fila de espera automática e relatórios de utilização.",
  keywords: [
    "deskflow",
    "coworking",
    "hot desking",
    "gestão de espaços",
    "trabalho híbrido",
    "reserva de salas",
    "cotas",
  ],
  authors: [{ name: "DeskFlow Team" }],
  openGraph: {
    title: "DeskFlow — Gestão de Espaços Híbridos",
    description: "Reserva de estações e salas com controle de cotas e QR Code.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#2563eb",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased selection:bg-blue-500 selection:text-white">
        <QueryProvider>
          <div className="flex min-h-screen flex-col">
            <OfflineBanner />
            <Navbar />
            <main className="flex-1">{children}</main>
            <RealtimeListener />
            <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
              DeskFlow &copy; {new Date().getFullYear()} — Plataforma Corporativa de Espaços Híbridos
            </footer>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}


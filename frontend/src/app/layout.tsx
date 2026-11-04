import type { Metadata, Viewport } from "next";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";
import { Navbar } from "@/components/navigation/navbar";
import { Footer } from "@/components/navigation/footer";
import { OfflineBanner } from "@/components/offline/offline-banner";
import { RealtimeListener } from "@/components/realtime/realtime-listener";
import { AuthGuard } from "@/features/auth/components/auth-guard";

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
    <html lang="pt-BR" className="light" style={{ colorScheme: "light" }}>
      <body className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased selection:bg-blue-500 selection:text-white">
        <QueryProvider>
          <div className="flex min-h-screen flex-col">
            <OfflineBanner />
            <Navbar />
            <main className="flex-1">
              <AuthGuard>{children}</AuthGuard>
            </main>
            <RealtimeListener />
            <Footer />
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}

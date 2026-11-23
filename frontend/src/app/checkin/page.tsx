"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, XCircle, Loader2, QrCode, ArrowRight, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { getApiBaseUrl } from "@/lib/api-client";

function CheckinContent() {
  const searchParams = useSearchParams();
  const bookingId = searchParams.get("id");
  const qrToken = searchParams.get("token");

  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const performCheckin = async () => {
    if (!bookingId || !qrToken) {
      setStatus("error");
      setErrorMessage("Parâmetros de check-in ausentes ou inválidos no QR Code.");
      return;
    }

    setStatus("loading");
    setErrorMessage("");

    try {
      const url = `${getApiBaseUrl()}/api/v1/bookings/${bookingId}/checkin?qr_token=${encodeURIComponent(
        qrToken
      )}`;

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const rawMsg = data.detail || data.message;
        const msg =
          typeof rawMsg === "string"
            ? rawMsg
            : Array.isArray(rawMsg)
              ? rawMsg.map((d: any) => d.msg || d.message || JSON.stringify(d)).join(", ")
              : rawMsg && typeof rawMsg === "object"
                ? (rawMsg as any).msg || (rawMsg as any).message || JSON.stringify(rawMsg)
                : "Falha ao validar check-in.";
        setErrorMessage(msg);
        setStatus("error");
        return;
      }

      setStatus("success");
    } catch {
      setStatus("error");
      setErrorMessage("Erro de conexão ao servidor. Verifique se o backend está acessível.");
    }
  };

  useEffect(() => {
    if (bookingId && qrToken) {
      performCheckin();
    } else {
      setStatus("error");
      setErrorMessage("Código de reserva ou token não encontrado no link.");
    }
  }, [bookingId, qrToken]);

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md border-slate-200 shadow-xl bg-white text-center">
        <CardHeader className="pb-4">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 shadow-sm border border-blue-100">
            <QrCode className="h-7 w-7" />
          </div>
          <CardTitle className="text-xl font-bold text-slate-900">
            DeskFlow Check-in
          </CardTitle>
          <CardDescription className="text-xs text-slate-600">
            Validação de presença em posto de trabalho via QR Code
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4 py-2">
          {status === "loading" && (
            <div className="py-8 flex flex-col items-center justify-center gap-3">
              <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
              <p className="text-sm font-semibold text-slate-700">
                Validando seu QR Code no sistema...
              </p>
              <p className="text-xs text-slate-500">
                Aguarde um momento enquanto confirmamos sua reserva.
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="py-6 flex flex-col items-center justify-center gap-3 animate-in fade-in zoom-in-95">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <CheckCircle2 className="h-10 w-10" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">
                Presença Confirmada!
              </h3>
              <p className="text-xs text-slate-600 max-w-xs">
                Seu check-in foi validado com sucesso. Sua reserva agora está ativa e o status foi atualizado em tempo real.
              </p>
              <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200 font-medium">
                <ShieldCheck className="h-4 w-4" />
                <span>Assento garantido no DeskFlow</span>
              </div>
            </div>
          )}

          {status === "error" && (
            <div className="py-4 flex flex-col items-center justify-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600">
                <XCircle className="h-8 w-8" />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Não foi possível confirmar
              </h3>
              <p className="text-xs text-red-700 bg-red-50 p-3 rounded-lg border border-red-200 max-w-sm font-medium">
                {errorMessage}
              </p>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex flex-col gap-2 pt-2 border-t border-slate-100">
          <Link
            href="/my-bookings"
            className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white py-2 text-xs font-semibold shadow-xs transition-colors"
          >
            <span>Ver Minhas Reservas</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/"
            className="text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors"
          >
            Voltar para o Início
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}

export default function CheckinPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[70vh] flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      }
    >
      <CheckinContent />
    </Suspense>
  );
}

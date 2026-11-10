"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertCircle, Bell, X } from "lucide-react";
import { useRealtimeEvents } from "@/features/realtime/hooks/use-realtime-events";

export function RealtimeListener() {
  const [quotaToast, setQuotaToast] = useState<string | null>(null);
  const [waitlistAlert, setWaitlistAlert] = useState<{
    message: string;
    waitlistId?: string;
  } | null>(null);

  useRealtimeEvents((event) => {
    if (event.type === "quota.alert" && typeof event.message === "string") {
      setQuotaToast(event.message);
      setTimeout(() => setQuotaToast(null), 6000);
    }

    if (event.type === "waitlist.notified") {
      const msg =
        typeof event.message === "string"
          ? event.message
          : "Vaga liberada na fila de espera! Você tem 5 minutos para confirmar sua reserva.";
      setWaitlistAlert({
        message: msg,
        waitlistId: typeof event.waitlist_id === "string" ? event.waitlist_id : undefined,
      });
    }
  });

  return (
    <>
      {quotaToast && (
        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-lg bg-red-600 px-4 py-3 text-sm text-white shadow-xl animate-in slide-in-from-bottom">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{quotaToast}</span>
        </div>
      )}

      {waitlistAlert && (
        <div className="fixed top-16 right-4 z-50 max-w-sm rounded-xl bg-blue-600 p-4 text-white shadow-2xl animate-in slide-in-from-top-4 border border-blue-400">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <Bell className="h-5 w-5 shrink-0 text-amber-300 animate-bounce mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-white">Vaga Liberada!</h4>
                <p className="text-xs text-blue-100 mt-0.5">{waitlistAlert.message}</p>
                <div className="mt-3 flex items-center gap-2">
                  <Link
                    href="/waitlist"
                    onClick={() => setWaitlistAlert(null)}
                    className="inline-flex items-center rounded-md bg-white px-3 py-1 text-xs font-bold text-blue-700 shadow-xs hover:bg-blue-50 transition-colors"
                  >
                    Ver Fila de Espera
                  </Link>
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setWaitlistAlert(null)}
              className="text-blue-200 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}

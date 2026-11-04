"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  CalendarCheck,
  CheckCircle2,
  Clock,
  Trash2,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCurrentUser } from "@/features/auth/hooks/use-auth";
import { useCreateBooking } from "@/features/bookings/hooks/use-bookings";
import {
  useCancelWaitlist,
  useMyWaitlist,
} from "@/features/waitlist/hooks/use-waitlist";

export default function WaitlistPage() {
  const { data: user } = useCurrentUser();
  const { data: waitlist, isLoading } = useMyWaitlist();
  const cancelWaitlistMutation = useCancelWaitlist();
  const createBookingMutation = useCreateBooking();

  const [mounted, setMounted] = useState(false);
  const [currentTime, setCurrentTime] = useState(() => new Date());
  const [actionMessage, setActionMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    setMounted(true);
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleClaimSeat = async (entry: {
    workspaceId: string;
    desiredSlot: { start: Date; end: Date };
  }) => {
    if (!user) return;
    setActionMessage(null);

    try {
      await createBookingMutation.mutateAsync({
        workspace_id: entry.workspaceId,
        employee_id: user.id,
        cost_center_id: user.costCenterId || "",
        slot_start: entry.desiredSlot.start.toISOString(),
        slot_end: entry.desiredSlot.end.toISOString(),
      });
      setActionMessage({
        type: "success",
        text: "Vaga garantida com sucesso! Sua entrada na fila de espera foi consumida.",
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao garantir vaga.";
      setActionMessage({ type: "error", text: msg });
    }
  };

  const handleLeaveWaitlist = async (waitlistId: string) => {
    setActionMessage(null);
    try {
      await cancelWaitlistMutation.mutateAsync(waitlistId);
      setActionMessage({ type: "success", text: "Você saiu da fila de espera." });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao sair da fila.";
      setActionMessage({ type: "error", text: msg });
    }
  };

  const formatSlotTime = (date: Date) => {
    return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" });
  };

  const formatSlotDate = (date: Date) => {
    return date.toLocaleDateString("pt-BR", { timeZone: "UTC" });
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <Clock className="h-6 w-6 text-blue-600" />
          Fila de Espera Automática
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Quando uma reserva for cancelada, o próximo da fila é notificado em tempo real com prioridade exclusiva de 5 minutos para confirmação.
        </p>
      </div>

      {actionMessage && (
        <div
          className={`mt-4 rounded-md p-3 text-sm border flex items-center gap-2 ${
            actionMessage.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-red-50 text-red-700 border-red-200"
          }`}
        >
          {actionMessage.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          ) : (
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
          )}
          <span>{actionMessage.text}</span>
        </div>
      )}

      <div className="mt-6 space-y-4">
        {isLoading || !mounted ? (
          <div className="space-y-3">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-lg bg-slate-200" />
            ))}
          </div>
        ) : waitlist?.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center">
            <CalendarCheck className="mx-auto h-10 w-10 text-slate-400" />
            <h3 className="mt-2 text-sm font-semibold text-slate-900">
              Você não está em nenhuma fila de espera
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Caso um posto desejado esteja ocupado, você pode entrar na fila diretamente pelo modal de reserva.
            </p>
          </div>
        ) : (
          waitlist?.map((entry) => {
            const isHoldActive = entry.isHoldActive(currentTime);
            const remainingSec = entry.remainingHoldSeconds(currentTime);
            const minutes = Math.floor(remainingSec / 60);
            const seconds = remainingSec % 60;

            return (
              <Card
                key={entry.id}
                className={`shadow-xs transition-all ${
                  isHoldActive
                    ? "border-emerald-400 bg-emerald-50/30 ring-1 ring-emerald-400"
                    : "hover:border-slate-300"
                }`}
              >
                <CardHeader className="pb-2">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <CardTitle className="text-base text-slate-900 flex items-center gap-2">
                        {isHoldActive && <Zap className="h-4 w-4 text-emerald-600 fill-emerald-600 animate-pulse" />}
                        {formatSlotDate(entry.desiredSlot.start)} &bull; {formatSlotTime(entry.desiredSlot.start)} até {formatSlotTime(entry.desiredSlot.end)}
                      </CardTitle>
                      <CardDescription className="text-xs mt-0.5">
                        Espaço ID: {entry.workspaceId.slice(0, 8)}... &bull; Solicitado em:{" "}
                        {entry.createdAt.toLocaleTimeString("pt-BR")}
                      </CardDescription>
                    </div>

                    <div>
                      {isHoldActive ? (
                        <Badge variant="success" className="animate-pulse">
                          VAGA LIBERADA! ({minutes}:{seconds.toString().padStart(2, "0")})
                        </Badge>
                      ) : (
                        <Badge variant="secondary">AGUARDANDO NA FILA</Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100">
                  <div className="text-xs text-slate-500">
                    {isHoldActive ? (
                      <span className="text-emerald-700 font-medium">
                        Apenas você pode reservar esta vaga durante a contagem regressiva!
                      </span>
                    ) : (
                      <span>Aguardando liberação por cancelamento de outro colaborador.</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {isHoldActive && (
                      <Button
                        size="sm"
                        onClick={() => handleClaimSeat(entry)}
                        disabled={createBookingMutation.isPending}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        Garantir Minha Vaga
                      </Button>
                    )}

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleLeaveWaitlist(entry.id)}
                      disabled={cancelWaitlistMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4 mr-1 text-slate-500" />
                      Sair da Fila
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}


"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CalendarDays,
  Check,
  CheckCircle2,
  Clock,
  Copy,
  QrCode,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Booking, BookingStatus } from "@/domain/entities/booking";
import {
  useCancelBooking,
  useCheckIn,
  useMyBookings,
} from "@/features/bookings/hooks/use-bookings";
import { API_BASE_URL, apiClient, getToken } from "@/lib/api-client";

export default function MyBookingsPage() {
  const { data: bookings, isLoading } = useMyBookings();
  const cancelMutation = useCancelBooking();
  const checkinMutation = useCheckIn();

  const [selectedBookingForQr, setSelectedBookingForQr] = useState<Booking | null>(null);
  const [mounted, setMounted] = useState(false);
  const [qrTokenInput, setQrTokenInput] = useState("");
  const [rawToken, setRawToken] = useState<string | null>(null);
  const [isCopied, setIsCopied] = useState(false);
  const [imgLoadError, setImgLoadError] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!selectedBookingForQr) {
      setRawToken(null);
      setQrTokenInput("");
      setImgLoadError(false);
      return;
    }
    setImgLoadError(false);
    apiClient<{ qr_token: string }>(`/api/v1/bookings/${selectedBookingForQr.id}/checkin-token`)
      .then((res) => {
        setRawToken(res.qr_token);
        setQrTokenInput(res.qr_token);
      })
      .catch(() => {
        setRawToken(null);
      });
  }, [selectedBookingForQr]);

  const handleCancel = async (booking: Booking) => {
    setFeedback(null);
    try {
      booking.cancel(new Date());
      await cancelMutation.mutateAsync(booking.id);
      setFeedback({ type: "success", text: "Reserva cancelada com sucesso. Cota devolvida!" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao cancelar reserva.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handlePerformCheckIn = async (bookingId: string, simulate: boolean = false) => {
    setFeedback(null);
    try {
      await checkinMutation.mutateAsync({
        bookingId,
        qrToken: qrTokenInput.trim(),
        simulate,
      });
      setFeedback({ type: "success", text: "Check-in confirmado com sucesso! Presença validada." });
      setSelectedBookingForQr(null);
      setQrTokenInput("");
    } catch (err: unknown) {
      let msg = err instanceof Error ? err.message : "Token de check-in inválido ou fora do horário.";
      if (
        msg.includes("outside the allowed time window") ||
        msg.includes("permitido entre")
      ) {
        msg =
          "O check-in só é permitido entre 10 minutos antes e 10 minutos após o início da reserva. Use o botão 'Simular Check-in (Demonstração)' para validar agora.";
      }
      setFeedback({ type: "error", text: msg });
    }
  };

  const getCheckinWindowInfo = (booking: Booking | null) => {
    if (!booking) return null;
    const now = Date.now();
    const startTime = booking.slot.start.getTime();
    const windowStart = startTime - 10 * 60 * 1000;
    const windowEnd = startTime + 15 * 60 * 1000;
    const isWithinWindow = now >= windowStart && now <= windowEnd;
    const isTooEarly = now < windowStart;
    const isTooLate = now > windowEnd;

    const startStr = booking.slot.start.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    });
    const dateStr = booking.slot.start.toLocaleDateString("pt-BR", {
      timeZone: "UTC",
    });
    const openTimeStr = new Date(windowStart).toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    });

    return {
      isWithinWindow,
      isTooEarly,
      isTooLate,
      startStr,
      dateStr,
      openTimeStr,
    };
  };

  const getStatusBadge = (status: BookingStatus) => {
    switch (status) {
      case BookingStatus.CONFIRMED:
        return <Badge variant="success">CONFIRMADA</Badge>;
      case BookingStatus.PENDING:
        return <Badge variant="warning">PENDENTE (Aguardando Check-in)</Badge>;
      case BookingStatus.CANCELLED:
        return <Badge variant="destructive">CANCELADA</Badge>;
      case BookingStatus.EXPIRED:
        return <Badge variant="secondary">EXPIRADA (No-Show)</Badge>;
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
          <CalendarDays className="h-6 w-6 text-blue-600" />
          Minhas Reservas
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Acompanhe suas reservas ativas, realize check-in por QR Code dinâmico ou gerencie cancelamentos (antecedência mínima de 2 horas).
        </p>
      </div>

      {feedback && (
        <div
          className={`mt-4 rounded-md p-3 text-sm border flex items-center gap-2 ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-red-50 text-red-700 border-red-200"
          }`}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 shrink-0 text-red-600" />
          )}
          <span>{feedback.text}</span>
        </div>
      )}

      <div className="mt-6 space-y-4">
        {isLoading || !mounted ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-lg bg-slate-200" />
            ))}
          </div>
        ) : bookings?.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center">
            <CalendarDays className="mx-auto h-10 w-10 text-slate-400" />
            <h3 className="mt-2 text-sm font-semibold text-slate-900">
              Nenhuma reserva encontrada
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Reserve um posto ou sala para visualizar seus agendamentos aqui.
            </p>
          </div>
        ) : (
          bookings?.map((booking) => {
            const isPending = booking.status === BookingStatus.PENDING;
            const isConfirmed = booking.status === BookingStatus.CONFIRMED;
            const canCancelNow = (booking.slot.start.getTime() - Date.now()) >= 2 * 60 * 60 * 1000;

            return (
              <Card key={booking.id} className="shadow-xs hover:border-slate-300 transition-all">
                <CardHeader className="pb-2">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <CardTitle className="text-base text-slate-900">
                        {formatSlotDate(booking.slot.start)} &bull; {formatSlotTime(booking.slot.start)} às {formatSlotTime(booking.slot.end)}
                      </CardTitle>
                      <CardDescription className="text-xs mt-0.5">
                        Duração: {booking.slot.durationHours}h &bull; ID: {booking.id.slice(0, 8)}...
                      </CardDescription>
                    </div>
                    <div>{getStatusBadge(booking.status)}</div>
                  </div>
                </CardHeader>
                <CardContent className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100">
                  <div className="text-xs text-slate-500">
                    {isPending && (
                      <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 inline-flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Tolerância de check-in: 15min para estações / 30min para salas
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {isPending && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedBookingForQr(booking)}
                        className="gap-1.5"
                      >
                        <QrCode className="h-4 w-4 text-blue-600" />
                        Check-in QR
                      </Button>
                    )}

                    {(isPending || isConfirmed) && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleCancel(booking)}
                        disabled={cancelMutation.isPending || !canCancelNow}
                        title={
                          !canCancelNow
                            ? "Cancelamentos são permitidos somente com antecedência mínima de 2 horas."
                            : "Cancelar Reserva"
                        }
                      >
                        <XCircle className="h-4 w-4 mr-1" />
                        Cancelar
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      <Dialog
        open={!!selectedBookingForQr}
        onOpenChange={(open) => !open && setSelectedBookingForQr(null)}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5 text-blue-600" />
              Check-in com QR Code Dinâmico
            </DialogTitle>
            <DialogDescription>
              Apresente o QR Code na câmera do totem ou insira o token assinado.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col items-center justify-center py-3 space-y-4">
            {selectedBookingForQr && (
              <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-col items-center justify-center">
                {!imgLoadError ? (
                  <img
                    src={`${API_BASE_URL}/api/v1/bookings/${selectedBookingForQr.id}/qr?token=${getToken()}`}
                    alt="QR Code de Check-in"
                    className="h-48 w-48 object-contain"
                    onError={() => setImgLoadError(true)}
                  />
                ) : (
                  <div className="h-48 w-48 flex flex-col items-center justify-center p-3 text-center bg-slate-50 rounded-lg text-xs text-slate-500">
                    <QrCode className="h-10 w-10 text-slate-400 mb-2" />
                    <span>Use o token digital abaixo para confirmar o check-in</span>
                  </div>
                )}
                <span className="text-[11px] text-slate-400 mt-2 font-mono">
                  ID: {selectedBookingForQr.id.slice(0, 13)}...
                </span>
              </div>
            )}

            {(() => {
              const winInfo = getCheckinWindowInfo(selectedBookingForQr);
              if (!winInfo) return null;

              if (winInfo.isTooEarly) {
                return (
                  <div className="w-full rounded-lg bg-amber-50 p-3 text-xs text-amber-900 border border-amber-200 flex items-start gap-2">
                    <Clock className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold block">Check-in ainda não liberado</span>
                      A reserva está agendada para <b>{winInfo.dateStr} às {winInfo.startStr}</b>. A janela oficial abrirá às <b>{winInfo.openTimeStr}</b> (10 min antes).
                      <div className="mt-1 text-slate-500">
                        Para testes e validação no ambiente de demonstração, você pode clicar em <b>Simular Check-in</b> abaixo.
                      </div>
                    </div>
                  </div>
                );
              }

              if (winInfo.isTooLate) {
                return (
                  <div className="w-full rounded-lg bg-red-50 p-3 text-xs text-red-900 border border-red-200 flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold block">Janela de Check-in Expirada</span>
                      O horário de tolerância desta reserva encerrou.
                      <div className="mt-1 text-slate-500">
                        Você pode simular a confirmação para fins de teste no ambiente de demonstração.
                      </div>
                    </div>
                  </div>
                );
              }

              return (
                <div className="w-full rounded-lg bg-emerald-50 p-3 text-xs text-emerald-900 border border-emerald-200 flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block">Janela de Check-in Aberta!</span>
                    Você está no horário permitido para validar sua presença na estação/sala.
                  </div>
                </div>
              );
            })()}

            <div className="w-full space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-700 block">
                  Token de confirmação de check-in:
                </label>
                {rawToken && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs text-blue-600 hover:text-blue-700 px-1.5"
                    onClick={() => {
                      navigator.clipboard.writeText(rawToken);
                      setIsCopied(true);
                      setTimeout(() => setIsCopied(false), 2000);
                    }}
                  >
                    {isCopied ? (
                      <>
                        <Check className="h-3 w-3 mr-1 text-emerald-600" />
                        Copiado!
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3 mr-1" />
                        Copiar Token
                      </>
                    )}
                  </Button>
                )}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Cole aqui o token JWT de check-in"
                  value={qrTokenInput}
                  onChange={(e) => setQrTokenInput(e.target.value)}
                  className="font-mono text-xs"
                />
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                <Button
                  onClick={() =>
                    selectedBookingForQr &&
                    handlePerformCheckIn(selectedBookingForQr.id, false)
                  }
                  disabled={!qrTokenInput.trim() || checkinMutation.isPending}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs"
                >
                  Confirmar Check-in
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() =>
                    selectedBookingForQr &&
                    handlePerformCheckIn(selectedBookingForQr.id, true)
                  }
                  disabled={!qrTokenInput.trim() || checkinMutation.isPending}
                  className="border-blue-300 text-blue-700 hover:bg-blue-50 text-xs font-semibold"
                  title="Valida o check-in imediatamente para testes sem esperar o horário da reserva"
                >
                  Simular Check-in (Demonstração)
                </Button>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSelectedBookingForQr(null)}
            >
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

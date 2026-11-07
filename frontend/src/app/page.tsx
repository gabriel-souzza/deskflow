"use client";

import { useEffect, useState } from "react";
import {
  Calendar,
  CheckCircle2,
  Clock,
  Filter,
  Layers,
  MapPin,
  Monitor,
  Sparkles,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Workspace } from "@/domain/entities/workspace";
import { useCurrentUser } from "@/features/auth/hooks/use-auth";
import { useCreateBooking } from "@/features/bookings/hooks/use-bookings";
import { useJoinWaitlist } from "@/features/waitlist/hooks/use-waitlist";
import {
  useWorkspaceAvailability,
  useWorkspaces,
} from "@/features/workspaces/hooks/use-workspaces";

const RESOURCE_LABELS: Record<string, string> = {
  monitor: "Monitor",
  monitor_duplo: "Monitor Duplo",
  tomada: "Tomada",
  usb_c: "USB-C PD",
  dock_station: "Dock Station",
  cadeira_ergonomica: "Cadeira Ergonômica",
  fone_noise_cancelling: "Headset ANC",
  isolamento_acustico: "Isolamento Acústico",
  tv_4k: "TV 4K",
  whiteboard: "Quadro Branco",
  videoconferencia: "Videoconferência",
  videoconferencia_zoom: "Zoom Rooms",
  projetor: "Projetor",
  sistema_audio: "Sistema de Áudio",
};

export default function WorkspacesPage() {
  const { data: user } = useCurrentUser();
  const [mounted, setMounted] = useState(false);
  const [selectedDay, setSelectedDay] = useState(() => {
    const today = new Date();
    return today.toISOString().split("T")[0]!;
  });

  useEffect(() => {
    setMounted(true);
  }, []);
  const [floorFilter, setFloorFilter] = useState<string>("");
  const [zoneFilter, setZoneFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");

  const [bookingModalWs, setBookingModalWs] = useState<Workspace | null>(null);
  const [selectedStartTime, setSelectedStartTime] = useState("09:00");
  const [selectedEndTime, setSelectedEndTime] = useState("10:00");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: workspaces, isLoading } = useWorkspaces({
    floor: floorFilter || undefined,
    zone: zoneFilter || undefined,
    type: typeFilter || undefined,
  });

  const { data: availability } = useWorkspaceAvailability(
    bookingModalWs?.id || "",
    selectedDay
  );

  const createBookingMutation = useCreateBooking();
  const joinWaitlistMutation = useJoinWaitlist();

  const timeOptions: string[] = [];
  for (let hour = 8; hour <= 18; hour++) {
    for (let min = 0; min < 60; min += 15) {
      if (hour === 18 && min > 0) break;
      const hh = hour.toString().padStart(2, "0");
      const mm = min.toString().padStart(2, "0");
      timeOptions.push(`${hh}:${mm}`);
    }
  }

  const handleOpenBookingModal = (ws: Workspace) => {
    setBookingModalWs(ws);
    setSelectedStartTime("09:00");
    setSelectedEndTime("10:00");
    setActionSuccess(null);
    setActionError(null);
  };

  const handleStartTimeChange = (newStart: string) => {
    setSelectedStartTime(newStart);
    setActionError(null);
    if (selectedEndTime <= newStart) {
      const startIdx = timeOptions.indexOf(newStart);
      const nextTime =
        startIdx + 4 < timeOptions.length
          ? timeOptions[startIdx + 4]!
          : startIdx + 1 < timeOptions.length
            ? timeOptions[startIdx + 1]!
            : newStart;
      setSelectedEndTime(nextTime);
    }
  };

  const handleConfirmBooking = async () => {
    if (!bookingModalWs || !user) return;
    setActionError(null);
    setActionSuccess(null);

    const effectiveEndTime =
      selectedEndTime > selectedStartTime
        ? selectedEndTime
        : timeOptions.find((t) => t > selectedStartTime) || selectedEndTime;

    if (effectiveEndTime <= selectedStartTime) {
      setActionError("O horário de término deve ser posterior ao horário de início.");
      return;
    }

    const slotStartIso = `${selectedDay}T${selectedStartTime}:00Z`;
    const slotEndIso = `${selectedDay}T${effectiveEndTime}:00Z`;

    try {
      await createBookingMutation.mutateAsync({
        workspace_id: bookingModalWs.id,
        employee_id: user.id,
        cost_center_id: user.costCenterId || "",
        slot_start: slotStartIso,
        slot_end: slotEndIso,
      });
      setActionSuccess("Reserva confirmada com sucesso! Lembre-se de realizar o check-in no horário.");
      setTimeout(() => {
        setBookingModalWs(null);
      }, 1500);
    } catch (err: unknown) {
      let msg = err instanceof Error ? err.message : "Falha ao criar reserva.";
      if (msg.includes("Start time must be before end time") || msg.includes("before")) {
        msg = "O horário de término deve ser posterior ao horário de início.";
      } else if (msg.includes("Invalid employee or time slot")) {
        msg = "Colaborador ou intervalo de horário inválido.";
      } else if (msg.includes("QuotaExceededError") || msg.toLowerCase().includes("quota")) {
        msg = "Cota mensal de horas do centro de custo excedida.";
      }
      setActionError(msg);
    }
  };

  const handleJoinWaitlist = async () => {
    if (!bookingModalWs || !user) return;
    setActionError(null);
    setActionSuccess(null);

    const effectiveEndTime =
      selectedEndTime > selectedStartTime
        ? selectedEndTime
        : timeOptions.find((t) => t > selectedStartTime) || selectedEndTime;

    if (effectiveEndTime <= selectedStartTime) {
      setActionError("O horário de término deve ser posterior ao horário de início.");
      return;
    }

    const selectedSlots =
      availability?.slots?.filter(
        (slot) => slot.time >= selectedStartTime && slot.time < effectiveEndTime
      ) || [];
    const isOccupied = selectedSlots.length > 0 && selectedSlots.some((s) => s.is_full);

    if (!isOccupied) {
      setActionError(
        "O espaço possui vagas disponíveis para este horário! Clique em 'Confirmar Reserva' para garantir seu posto."
      );
      return;
    }

    const slotStartIso = `${selectedDay}T${selectedStartTime}:00Z`;
    const slotEndIso = `${selectedDay}T${effectiveEndTime}:00Z`;

    try {
      await joinWaitlistMutation.mutateAsync({
        workspace_id: bookingModalWs.id,
        slot_start: slotStartIso,
        slot_end: slotEndIso,
      });
      setActionSuccess("Você entrou na fila de espera! Notificaremos assim que uma vaga for liberada.");
      setTimeout(() => {
        setBookingModalWs(null);
      }, 1800);
    } catch (err: unknown) {
      let msg = err instanceof Error ? err.message : "Falha ao entrar na fila.";
      if (msg.includes("Start time must be before end time") || msg.includes("before")) {
        msg = "O horário de término deve ser posterior ao horário de início.";
      } else if (msg.includes("Invalid employee or time slot")) {
        msg = "Colaborador ou intervalo de horário inválido.";
      }
      setActionError(msg);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {mounted && user && !user.isEligibleForBooking && (
        <div className="mb-6 rounded-lg bg-amber-50 p-4 border border-amber-200 flex items-start gap-3">
          <Clock className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <h4 className="font-semibold text-amber-900 text-sm">Política Híbrida — Presença Não Registrada</h4>
            <p className="text-xs text-amber-800 mt-0.5">
              Conforme a regra corporativa de 3 dias de presença presencial semanal, sua elegibilidade para reservar novos postos está bloqueada até a próxima sincronização de ponto.
            </p>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Reserva de Estações e Salas
          </h1>
          <p className="text-sm font-medium text-slate-600 mt-1">
            Selecione o dia e consulte a disponibilidade em tempo real com controle de cotas e fila.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-slate-600" />
          <input
            type="date"
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-900 shadow-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700 uppercase tracking-wider mr-2">
          <Filter className="h-4 w-4 text-blue-600" />
          <span>Filtros</span>
        </div>

        <select
          value={floorFilter}
          onChange={(e) => setFloorFilter(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-xs focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Todos os Andares</option>
          <option value="1">1º Andar</option>
          <option value="2">2º Andar</option>
          <option value="3">3º Andar</option>
          <option value="4">4º Andar</option>
        </select>

        <select
          value={zoneFilter}
          onChange={(e) => setZoneFilter(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-xs focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Todas as Zonas</option>
          <option value="open">Open Space</option>
          <option value="quiet">Quiet Zone</option>
          <option value="meeting">Meeting Zone</option>
          <option value="executive">Executiva</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-xs focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Todos os Tipos</option>
          <option value="estacao">Estação Individual</option>
          <option value="sala">Sala de Reunião</option>
        </select>

        {(floorFilter || zoneFilter || typeFilter) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setFloorFilter("");
              setZoneFilter("");
              setTypeFilter("");
            }}
            className="text-xs font-semibold text-slate-600 hover:text-slate-900 h-8 px-2.5"
          >
            Limpar filtros
          </Button>
        )}
      </div>

      <div className="mt-6">
        {isLoading || !mounted ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-44 animate-pulse rounded-xl bg-slate-200" />
            ))}
          </div>
        ) : workspaces?.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center bg-white">
            <Monitor className="mx-auto h-10 w-10 text-slate-400" />
            <h3 className="mt-2 text-sm font-bold text-slate-900">Nenhum espaço encontrado</h3>
            <p className="mt-1 text-xs text-slate-600">Tente ajustar os filtros de andar ou zona.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workspaces?.map((ws) => (
              <Card
                key={ws.id}
                className="hover:border-blue-400 hover:shadow-md transition-all border-slate-200 bg-white overflow-hidden"
              >
                <CardHeader className="pb-3.5">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2.5">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-lg border ${
                          ws.isStation()
                            ? "bg-blue-50 text-blue-700 border-blue-200"
                            : "bg-emerald-50 text-emerald-700 border-emerald-200"
                        }`}
                      >
                        {ws.isStation() ? (
                          <Monitor className="h-4 w-4" />
                        ) : (
                          <Users className="h-4 w-4" />
                        )}
                      </div>
                      <span className="tracking-tight text-slate-900">{ws.code}</span>
                    </CardTitle>

                    {ws.isStation() ? (
                      <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-800 border border-blue-200 shadow-2xs">
                        Estação
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200 shadow-2xs">
                        Sala ({ws.capacity} lug.)
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 pt-2.5">
                    <span className="inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 border border-slate-200/80">
                      <Layers className="h-3.5 w-3.5 text-slate-500" />
                      {ws.floor}º Andar
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 border border-slate-200/80 capitalize">
                      <MapPin className="h-3.5 w-3.5 text-slate-500" />
                      Zona {ws.zone}
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 border border-slate-200/80">
                      <Users className="h-3.5 w-3.5 text-slate-500" />
                      {ws.capacity} {ws.capacity === 1 ? "lugar" : "lugares"}
                    </span>
                  </div>

                  {ws.getResourceList().length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-2">
                      {ws.getResourceList().map((res) => (
                        <span
                          key={res}
                          className="inline-flex items-center gap-1 rounded bg-slate-50 px-2 py-0.5 text-[11px] font-medium text-slate-600 border border-slate-200"
                        >
                          <Sparkles className="h-3 w-3 text-blue-500" />
                          {RESOURCE_LABELS[res] || res.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  )}
                </CardHeader>

                <CardContent className="pt-0 pb-4">
                  <div className="flex items-center justify-between border-t border-slate-200 pt-3">
                    <span className="text-xs font-semibold text-slate-600 flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-blue-600" />
                      08:00 – 18:00 (15m)
                    </span>
                    <Button
                      size="sm"
                      onClick={() => {
                        if (!user) {
                          window.location.href = "/login";
                          return;
                        }
                        handleOpenBookingModal(ws);
                      }}
                      disabled={Boolean(mounted && user && !user.isEligibleForBooking)}
                      className={
                        mounted && user && !user.isEligibleForBooking
                          ? "bg-slate-100 text-slate-400 border border-slate-200 text-xs px-3 py-1.5 cursor-not-allowed font-medium"
                          : "bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4 py-1.5 shadow-xs transition-colors"
                      }
                    >
                      {mounted && user && !user.isEligibleForBooking ? "Bloqueado" : "Reservar"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog open={!!bookingModalWs} onOpenChange={(open) => !open && setBookingModalWs(null)}>
        <DialogContent className="sm:max-w-md bg-white border border-slate-200 shadow-xl text-slate-900">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-slate-900">
              <Calendar className="h-5 w-5 text-blue-600" />
              <span>Reserva — {bookingModalWs?.code}</span>
            </DialogTitle>
            <DialogDescription className="text-sm font-semibold text-slate-600">
              Dia {selectedDay} &bull; {bookingModalWs?.floor}º Andar &bull; Zona {bookingModalWs?.zone}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {actionSuccess && (
              <div className="rounded-lg bg-emerald-50 p-3 text-sm font-semibold text-emerald-800 border border-emerald-200 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                <span>{actionSuccess}</span>
              </div>
            )}

            {actionError && (
              <div className="rounded-lg bg-red-50 p-3 text-sm font-semibold text-red-800 border border-red-200">
                {actionError}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">
                  Horário Início
                </label>
                <select
                  value={selectedStartTime}
                  onChange={(e) => handleStartTimeChange(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white p-2 text-sm font-medium text-slate-900 shadow-xs focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {timeOptions.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">
                  Horário Fim
                </label>
                <select
                  value={selectedEndTime}
                  onChange={(e) => setSelectedEndTime(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white p-2 text-sm font-medium text-slate-900 shadow-xs focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {timeOptions
                    .filter((t) => t > selectedStartTime)
                    .map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            {(() => {
              const selectedSlots =
                availability?.slots?.filter(
                  (slot) => slot.time >= selectedStartTime && slot.time < selectedEndTime
                ) || [];
              const isSelectedRangeOccupied =
                selectedSlots.length > 0 && selectedSlots.some((s) => s.is_full);

              return isSelectedRangeOccupied ? (
                <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-900 border border-amber-200 flex items-start gap-2">
                  <Clock className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block">Horário com Ocupação Completa</span>
                    O espaço já está ocupado no período selecionado ({selectedStartTime} às {selectedEndTime}). Você pode entrar na fila de espera para ser notificado com prioridade assim que uma vaga for liberada.
                  </div>
                </div>
              ) : null;
            })()}

            <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-xs font-bold text-slate-800">
                  Disponibilidade das Janelas (15 minutos):
                </span>
                <span className="text-[11px] text-slate-500">
                  Clique para selecionar o horário
                </span>
              </div>
              <div className="grid grid-cols-4 gap-1.5 max-h-44 overflow-y-auto pr-1">
                {availability?.slots?.map((slot) => {
                  const isSelected =
                    slot.time >= selectedStartTime && slot.time < selectedEndTime;
                  return (
                    <button
                      key={slot.slot_index}
                      type="button"
                      disabled={slot.is_full}
                      onClick={() => handleStartTimeChange(slot.time)}
                      className={`rounded-md p-1.5 text-center text-xs font-mono border transition-all ${
                        slot.is_full
                          ? "bg-red-50 text-red-900 border-red-200 cursor-not-allowed opacity-75 font-semibold"
                          : isSelected
                            ? "bg-blue-600 text-white border-blue-600 font-bold shadow-xs scale-102 ring-2 ring-blue-300"
                            : "bg-emerald-50 text-emerald-900 border-emerald-200 hover:border-emerald-400 hover:bg-emerald-100 font-semibold cursor-pointer"
                      }`}
                      title={
                        slot.is_full
                          ? "Horário ocupado"
                          : `Clique para selecionar ${slot.time}`
                      }
                    >
                      <div className="font-bold">{slot.time}</div>
                      <div
                        className={`text-[10px] font-sans font-medium mt-0.5 ${
                          isSelected ? "text-blue-100" : ""
                        }`}
                      >
                        {slot.is_full
                          ? "Ocupado"
                          : isSelected
                            ? "Selecionado"
                            : `${slot.seats_available} vaga`}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 border-t border-slate-100 pt-3">
            {(() => {
              const selectedSlots =
                availability?.slots?.filter(
                  (slot) => slot.time >= selectedStartTime && slot.time < selectedEndTime
                ) || [];
              const isSelectedRangeOccupied =
                selectedSlots.length > 0 && selectedSlots.some((s) => s.is_full);

              if (isSelectedRangeOccupied) {
                return (
                  <>
                    <Button
                      variant="outline"
                      onClick={() => setBookingModalWs(null)}
                      className="text-xs font-semibold text-slate-700 border-slate-300 hover:bg-slate-100"
                    >
                      Fechar
                    </Button>
                    <Button
                      onClick={handleJoinWaitlist}
                      disabled={joinWaitlistMutation.isPending}
                      className="bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs shadow-xs"
                    >
                      {joinWaitlistMutation.isPending ? "Entrando na Fila..." : "Entrar na Fila de Espera"}
                    </Button>
                  </>
                );
              }

              return (
                <>
                  <Button
                    variant="outline"
                    onClick={handleJoinWaitlist}
                    disabled={joinWaitlistMutation.isPending}
                    className="text-xs font-semibold text-slate-700 border-slate-300 hover:bg-slate-100"
                    title="Fila de espera disponível quando o posto estiver ocupado"
                  >
                    Fila de Espera
                  </Button>
                  <Button
                    onClick={handleConfirmBooking}
                    disabled={createBookingMutation.isPending}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs"
                  >
                    {createBookingMutation.isPending ? "Reservando..." : "Confirmar Reserva"}
                  </Button>
                </>
              );
            })()}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

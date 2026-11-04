"use client";

import { useState } from "react";
import {
  Calendar,
  CheckCircle2,
  Clock,
  Filter,
  Layers,
  MapPin,
  Monitor,
  Users,
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
import { Workspace, WorkspaceType } from "@/domain/entities/workspace";
import { useCurrentUser } from "@/features/auth/hooks/use-auth";
import { useCreateBooking } from "@/features/bookings/hooks/use-bookings";
import { useJoinWaitlist } from "@/features/waitlist/hooks/use-waitlist";
import {
  useWorkspaceAvailability,
  useWorkspaces,
} from "@/features/workspaces/hooks/use-workspaces";

export default function WorkspacesPage() {
  const { data: user } = useCurrentUser();
  const [selectedDay, setSelectedDay] = useState(() => {
    const today = new Date();
    return today.toISOString().split("T")[0]!;
  });
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
    setActionSuccess(null);
    setActionError(null);
  };

  const handleConfirmBooking = async () => {
    if (!bookingModalWs || !user) return;
    setActionError(null);
    setActionSuccess(null);

    const slotStartIso = `${selectedDay}T${selectedStartTime}:00Z`;
    const slotEndIso = `${selectedDay}T${selectedEndTime}:00Z`;

    try {
      await createBookingMutation.mutateAsync({
        workspace_id: bookingModalWs.id,
        employee_id: user.id,
        cost_center_id: user.costCenterId || "",
        slot_start: slotStartIso,
        slot_end: slotEndIso,
      });
      setActionSuccess("Reserva confirmada com sucesso! (Status: PENDING)");
      setTimeout(() => {
        setBookingModalWs(null);
      }, 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao criar reserva.";
      setActionError(msg);
    }
  };

  const handleJoinWaitlist = async () => {
    if (!bookingModalWs || !user) return;
    setActionError(null);
    setActionSuccess(null);

    const slotStartIso = `${selectedDay}T${selectedStartTime}:00Z`;
    const slotEndIso = `${selectedDay}T${selectedEndTime}:00Z`;

    try {
      await joinWaitlistMutation.mutateAsync({
        workspace_id: bookingModalWs.id,
        slot_start: slotStartIso,
        slot_end: slotEndIso,
      });
      setActionSuccess("Você entrou na fila de espera! Notificaremos via SSE quando liberar.");
      setTimeout(() => {
        setBookingModalWs(null);
      }, 1800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao entrar na fila.";
      setActionError(msg);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {user && !user.isEligibleForBooking && (
        <div className="mb-6 rounded-lg bg-amber-50 p-4 border border-amber-200 flex items-start gap-3">
          <Clock className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <h4 className="font-semibold text-amber-800 text-sm">Política Híbrida — Presença Não Registrada</h4>
            <p className="text-xs text-amber-700 mt-0.5">
              Conforme a regra corporativa de 3 dias de presença presencial semanal (RF03), sua elegibilidade para reservar novos postos está bloqueada até a próxima sincronização de ponto.
            </p>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Reserva de Estações e Salas
          </h1>
          <p className="text-sm text-slate-500">
            Selecione o dia e consulte a disponibilidade em tempo real com controle de cotas e fila.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-slate-500" />
          <input
            type="date"
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm shadow-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3 bg-white p-3.5 rounded-lg border border-slate-200 shadow-xs">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider mr-2">
          <Filter className="h-3.5 w-3.5" />
          <span>Filtros</span>
        </div>

        <select
          value={floorFilter}
          onChange={(e) => setFloorFilter(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs shadow-xs"
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
          className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs shadow-xs"
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
          className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs shadow-xs"
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
            className="text-xs text-slate-500 h-7 px-2"
          >
            Limpar
          </Button>
        )}
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-44 animate-pulse rounded-xl bg-slate-200" />
            ))}
          </div>
        ) : workspaces?.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center">
            <Monitor className="mx-auto h-10 w-10 text-slate-400" />
            <h3 className="mt-2 text-sm font-semibold text-slate-900">Nenhum espaço encontrado</h3>
            <p className="mt-1 text-xs text-slate-500">Tente ajustar os filtros de andar ou zona.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workspaces?.map((ws) => (
              <Card key={ws.id} className="hover:border-blue-300 transition-all shadow-xs">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-1.5">
                      {ws.isStation() ? (
                        <Monitor className="h-4 w-4 text-blue-600" />
                      ) : (
                        <Users className="h-4 w-4 text-emerald-600" />
                      )}
                      {ws.code}
                    </CardTitle>
                    <Badge variant={ws.isStation() ? "secondary" : "default"}>
                      {ws.isStation() ? "Estação" : `Sala (${ws.capacity} lug.)`}
                    </Badge>
                  </div>
                  <CardDescription className="flex items-center gap-3 text-xs pt-1">
                    <span className="flex items-center gap-1">
                      <Layers className="h-3.5 w-3.5 text-slate-400" />
                      {ws.floor}º Andar
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" />
                      Zona {ws.zone}
                    </span>
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0 pb-4">
                  <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                    <span className="text-xs text-slate-500">
                      Grade de 15min (08:00–18:00)
                    </span>
                    <Button
                      size="sm"
                      onClick={() => handleOpenBookingModal(ws)}
                      disabled={!user?.isEligibleForBooking}
                    >
                      Reservar
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog open={!!bookingModalWs} onOpenChange={(open) => !open && setBookingModalWs(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              <span>Reserva — {bookingModalWs?.code}</span>
            </DialogTitle>
            <DialogDescription>
              Dia {selectedDay} &bull; {bookingModalWs?.floor}º Andar &bull; Zona {bookingModalWs?.zone}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {actionSuccess && (
              <div className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-800 border border-emerald-200 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                <span>{actionSuccess}</span>
              </div>
            )}

            {actionError && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 border border-red-200">
                {actionError}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Horário Início
                </label>
                <select
                  value={selectedStartTime}
                  onChange={(e) => setSelectedStartTime(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white p-2 text-sm"
                >
                  {timeOptions.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Horário Fim
                </label>
                <select
                  value={selectedEndTime}
                  onChange={(e) => setSelectedEndTime(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white p-2 text-sm"
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

            <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
              <span className="text-xs font-semibold text-slate-700 block mb-2">
                Status das Janelas de 15 Minutos:
              </span>
              <div className="grid grid-cols-4 gap-1.5 max-h-36 overflow-y-auto pr-1">
                {availability?.slots?.map((slot) => (
                  <div
                    key={slot.slot_index}
                    className={`rounded p-1 text-center text-[10px] font-mono border ${
                      slot.is_full
                        ? "bg-red-50 text-red-700 border-red-200"
                        : "bg-emerald-50 text-emerald-700 border-emerald-200"
                    }`}
                  >
                    <div>{slot.time}</div>
                    <div className="text-[9px]">
                      {slot.is_full ? "Ocupado" : `${slot.seats_available} vaga`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={handleJoinWaitlist}
              disabled={joinWaitlistMutation.isPending}
            >
              Fila de Espera
            </Button>
            <Button
              onClick={handleConfirmBooking}
              disabled={createBookingMutation.isPending}
            >
              {createBookingMutation.isPending ? "Reservando..." : "Confirmar Reserva"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}


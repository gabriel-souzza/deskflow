"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  BarChart3,
  Calendar,
  Clock,
  FileSpreadsheet,
  FileText,
  Layers,
  Lock,
  PieChart,
  RefreshCw,
  TrendingUp,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCurrentUser } from "@/features/auth/hooks/use-auth";
import {
  DimensionOccupancy,
  downloadReport,
  useUtilizationReport,
} from "@/features/reports/hooks/use-reports";

function getTodayLocalDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function ReportsPage() {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const [mounted, setMounted] = useState(false);
  const [startDate, setStartDate] = useState(getTodayLocalDate);
  const [endDate, setEndDate] = useState(getTodayLocalDate);

  useEffect(() => {
    setMounted(true);
  }, []);

  const {
    data: report,
    isLoading: reportLoading,
    error,
    refetch,
  } = useUtilizationReport(startDate, endDate);

  const handleExport = (format: "csv" | "pdf") => {
    downloadReport(startDate, endDate, format);
  };

  const setPresetToday = () => {
    const today = getTodayLocalDate();
    setStartDate(today);
    setEndDate(today);
  };

  const setPreset7Days = () => {
    const now = new Date();
    const d = new Date(now);
    d.setDate(d.getDate() - 6);
    const startStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    setStartDate(startStr);
    setEndDate(getTodayLocalDate());
  };

  const setPresetMonth = () => {
    const now = new Date();
    const startStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
    const lastDayDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    const endStr = `${lastDayDate.getFullYear()}-${String(lastDayDate.getMonth() + 1).padStart(2, "0")}-${String(lastDayDate.getDate()).padStart(2, "0")}`;
    setStartDate(startStr);
    setEndDate(endStr);
  };

  const parseOccupancyHours = (
    value: number | DimensionOccupancy | undefined
  ): string => {
    if (typeof value === "number") {
      return `${value % 1 === 0 ? value : value.toFixed(1)}h`;
    }
    if (value && typeof value === "object" && typeof value.occupied_slot_seats === "number") {
      const hours = value.occupied_slot_seats / 4;
      return `${hours % 1 === 0 ? hours : hours.toFixed(1)}h`;
    }
    return "0h";
  };

  if (!mounted || userLoading) {
    return (
      <div className="mx-auto max-w-7xl p-8">
        <div className="h-10 w-48 animate-pulse rounded bg-slate-200" />
      </div>
    );
  }

  if (!user?.isAdmin()) {
    return (
      <div className="mx-auto max-w-md py-20 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-50 text-amber-600 mb-4">
          <Lock className="h-7 w-7" />
        </div>
        <h2 className="text-lg font-bold text-slate-900">Acesso Restrito ao Administrador</h2>
        <p className="mt-1 text-sm text-slate-500">
          O Dashboard de Utilização e Rateio é exclusivo para usuários com perfil de Administrador.
        </p>
      </div>
    );
  }

  const summary = report?.summary ?? report;
  const utilizationRate = summary?.utilization_rate ?? summary?.occupancy_rate ?? 0;
  const noShowRate = summary?.no_show_rate ?? 0;
  const confirmedCount = summary?.bookings_confirmed ?? 0;
  const expiredCount = summary?.bookings_expired ?? 0;
  const totalStations = summary?.total_stations ?? 0;
  const totalMeetingRooms = summary?.total_meeting_rooms ?? 0;

  const byFloorEntries = Object.entries(report?.by_floor ?? {});
  const byZoneEntries = Object.entries(report?.by_zone ?? {});
  const costCenterEntries = Object.entries(report?.cost_center_hours ?? {});

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            Dashboard de Utilização e Rateio
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Métricas de ocupação, ociosidade, taxas de no-show e rateio de custos por departamento.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Presets */}
          <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600">
            <button
              type="button"
              onClick={setPresetToday}
              className={`px-2.5 py-1 rounded-md transition-colors ${startDate === endDate && startDate === getTodayLocalDate() ? "bg-white text-slate-900 shadow-xs" : "hover:text-slate-900"}`}
            >
              Hoje
            </button>
            <button
              type="button"
              onClick={setPreset7Days}
              className="px-2.5 py-1 rounded-md hover:text-slate-900 transition-colors"
            >
              7 dias
            </button>
            <button
              type="button"
              onClick={setPresetMonth}
              className="px-2.5 py-1 rounded-md hover:text-slate-900 transition-colors"
            >
              Mês
            </button>
          </div>

          {/* Date range pickers */}
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 px-3 py-1.5 rounded-md shadow-xs text-xs">
            <Calendar className="h-4 w-4 text-slate-400" />
            <span className="text-slate-400">De</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="outline-none bg-transparent"
            />
            <span className="text-slate-400">Até</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="outline-none bg-transparent"
            />
          </div>

          <Button
            size="sm"
            variant="outline"
            onClick={() => handleExport("csv")}
            className="gap-1.5"
          >
            <FileSpreadsheet className="h-4 w-4 text-emerald-600" />
            CSV
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={() => handleExport("pdf")}
            className="gap-1.5"
          >
            <FileText className="h-4 w-4 text-red-600" />
            PDF
          </Button>
        </div>
      </div>

      {error ? (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-700">
              Não foi possível carregar os dados do relatório para a data selecionada.
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={() => refetch()}
              className="ml-auto gap-1 text-xs"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Tentar novamente
            </Button>
          </div>
        </div>
      ) : null}

      {reportLoading ? (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-slate-200" />
          ))}
        </div>
      ) : (
        <>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="text-xs">Taxa de Ocupação</CardDescription>
                <CardTitle className="text-2xl font-bold text-blue-600 flex items-center justify-between">
                  <span>{(utilizationRate * 100).toFixed(0)}%</span>
                  <TrendingUp className="h-5 w-5 text-blue-500" />
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-slate-500">
                {confirmedCount} {confirmedCount === 1 ? "reserva confirmada" : "reservas confirmadas"}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="text-xs">Taxa de No-Show</CardDescription>
                <CardTitle className="text-2xl font-bold text-amber-600 flex items-center justify-between">
                  <span>{(noShowRate * 100).toFixed(1)}%</span>
                  <Clock className="h-5 w-5 text-amber-500" />
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-slate-500">
                {expiredCount} expiradas por tolerância
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="text-xs">Estações Disponíveis</CardDescription>
                <CardTitle className="text-2xl font-bold text-slate-900 flex items-center justify-between">
                  <span>{totalStations}</span>
                  <Layers className="h-5 w-5 text-slate-400" />
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-slate-500">
                Postos de trabalho individuais
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="text-xs">Salas de Reunião</CardDescription>
                <CardTitle className="text-2xl font-bold text-slate-900 flex items-center justify-between">
                  <span>{totalMeetingRooms}</span>
                  <Users className="h-5 w-5 text-slate-400" />
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-slate-500">
                Capacidade multi-assento
              </CardContent>
            </Card>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="h-4 w-4 text-blue-600" />
                  Ocupação por Andar
                </CardTitle>
                <CardDescription className="text-xs">Horas reservadas no dia</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {byFloorEntries.map(([floor, val]) => (
                    <div key={floor} className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">{floor}º Andar</span>
                      <span className="font-semibold text-slate-900 font-mono">
                        {parseOccupancyHours(val)}
                      </span>
                    </div>
                  ))}
                  {byFloorEntries.length === 0 && (
                    <span className="text-xs text-slate-400">Sem registros para o dia.</span>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <PieChart className="h-4 w-4 text-emerald-600" />
                  Ocupação por Zona
                </CardTitle>
                <CardDescription className="text-xs">Distribuição de espaços</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {byZoneEntries.map(([zone, val]) => (
                    <div key={zone} className="flex items-center justify-between text-sm">
                      <span className="text-slate-600 capitalize">Zona {zone}</span>
                      <span className="font-semibold text-slate-900 font-mono">
                        {parseOccupancyHours(val)}
                      </span>
                    </div>
                  ))}
                  {byZoneEntries.length === 0 && (
                    <span className="text-xs text-slate-400">Sem registros para o dia.</span>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-purple-600" />
                  Consumo por Centro de Custo
                </CardTitle>
                <CardDescription className="text-xs">Rateio de horas-estação</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {costCenterEntries.map(([ccId, hours]) => {
                    const name =
                      report?.cost_center_names?.[ccId] ||
                      (ccId.length > 13 ? `${ccId.slice(0, 13)}...` : ccId);
                    return (
                      <div key={ccId} className="flex items-center justify-between text-sm">
                        <span className="text-slate-600 text-xs truncate max-w-[180px]" title={name}>
                          {name}
                        </span>
                        <span className="font-semibold text-slate-900 font-mono">{hours}h</span>
                      </div>
                    );
                  })}
                  {costCenterEntries.length === 0 && (
                    <span className="text-xs text-slate-400">Sem registros para o período.</span>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

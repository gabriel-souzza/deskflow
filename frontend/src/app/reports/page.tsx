"use client";

import { useState } from "react";
import {
  BarChart3,
  Calendar,
  Clock,
  FileSpreadsheet,
  FileText,
  Layers,
  PieChart,
  TrendingUp,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  downloadReport,
  useUtilizationReport,
} from "@/features/reports/hooks/use-reports";

export default function ReportsPage() {
  const [selectedDay, setSelectedDay] = useState(() => {
    return new Date().toISOString().split("T")[0]!;
  });

  const { data: report, isLoading } = useUtilizationReport(selectedDay);

  const handleExport = (format: "csv" | "pdf") => {
    downloadReport(selectedDay, selectedDay, format);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            Dashboard de Utilização e Rateio
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Métricas de ocupação, ociosidade, taxas de no-show e rateio de custos por departamento (RF07–RF10).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 px-3 py-1.5 rounded-md shadow-xs">
            <Calendar className="h-4 w-4 text-slate-400" />
            <input
              type="date"
              value={selectedDay}
              onChange={(e) => setSelectedDay(e.target.value)}
              className="text-sm outline-none"
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

      {isLoading ? (
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
                  <span>{(report?.summary.utilization_rate ?? 0) * 100}%</span>
                  <TrendingUp className="h-5 w-5 text-blue-500" />
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-slate-500">
                {report?.summary.bookings_confirmed ?? 0} reservas confirmadas
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="text-xs">Taxa de No-Show</CardDescription>
                <CardTitle className="text-2xl font-bold text-amber-600 flex items-center justify-between">
                  <span>{((report?.summary.no_show_rate ?? 0) * 100).toFixed(1)}%</span>
                  <Clock className="h-5 w-5 text-amber-500" />
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-slate-500">
                {report?.summary.bookings_expired ?? 0} expiradas por tolerância
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="text-xs">Estações Disponíveis</CardDescription>
                <CardTitle className="text-2xl font-bold text-slate-900 flex items-center justify-between">
                  <span>{report?.summary.total_stations ?? 0}</span>
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
                  <span>{report?.summary.total_meeting_rooms ?? 0}</span>
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
                  {Object.entries(report?.by_floor || {}).map(([floor, hours]) => (
                    <div key={floor} className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">{floor}º Andar</span>
                      <span className="font-semibold text-slate-900 font-mono">{hours}h</span>
                    </div>
                  ))}
                  {Object.keys(report?.by_floor || {}).length === 0 && (
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
                  {Object.entries(report?.by_zone || {}).map(([zone, hours]) => (
                    <div key={zone} className="flex items-center justify-between text-sm">
                      <span className="text-slate-600 capitalize">Zona {zone}</span>
                      <span className="font-semibold text-slate-900 font-mono">{hours}h</span>
                    </div>
                  ))}
                  {Object.keys(report?.by_zone || {}).length === 0 && (
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
                  {Object.entries(report?.cost_center_hours || {}).map(([ccId, hours]) => (
                    <div key={ccId} className="flex items-center justify-between text-sm">
                      <span className="text-slate-600 text-xs truncate max-w-[150px]">
                        {ccId.slice(0, 13)}...
                      </span>
                      <span className="font-semibold text-slate-900 font-mono">{hours}h</span>
                    </div>
                  ))}
                  {Object.keys(report?.cost_center_hours || {}).length === 0 && (
                    <span className="text-xs text-slate-400">Sem registros para o dia.</span>
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


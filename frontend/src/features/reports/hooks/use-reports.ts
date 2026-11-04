"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, apiClient, getToken } from "@/lib/api-client";

export interface ReportSummaryMetrics {
  total_stations?: number;
  total_meeting_rooms?: number;
  bookings_pending?: number;
  bookings_confirmed?: number;
  bookings_cancelled?: number;
  bookings_expired?: number;
  utilization_rate?: number;
  occupancy_rate?: number;
  no_show_rate?: number;
  occupied_slot_seats?: number;
  total_slot_seats?: number;
  available_spots?: number;
  period?: string;
}

export interface DimensionOccupancy {
  bookings_confirmed?: number;
  occupied_slot_seats?: number;
}

export interface UtilizationReportData extends Partial<ReportSummaryMetrics> {
  summary?: ReportSummaryMetrics;
  by_floor?: Record<string, number | DimensionOccupancy>;
  by_zone?: Record<string, number | DimensionOccupancy>;
  cost_center_hours?: Record<string, number>;
}

export function useUtilizationReport(day: string) {
  const token = typeof window !== "undefined" ? getToken() : null;

  return useQuery({
    queryKey: ["reports", "utilization", day, token],
    queryFn: () =>
      apiClient<UtilizationReportData>(`/api/v1/reports/utilization?day=${day}`),
    enabled: !!day && !!token,
  });
}

export function downloadReport(
  startDate: string,
  endDate: string,
  format: "csv" | "pdf"
): void {
  const token = getToken();
  const url = `${API_BASE_URL}/api/v1/reports/export?start_date=${startDate}&end_date=${endDate}&format=${format}`;

  fetch(url, {
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
    },
  })
    .then((res) => res.blob())
    .then((blob) => {
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `relatorio-deskflow-${startDate}-${endDate}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    });
}


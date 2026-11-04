"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, apiClient, getToken } from "@/lib/api-client";

export interface UtilizationReportData {
  summary: {
    total_stations: number;
    total_meeting_rooms: number;
    bookings_pending: number;
    bookings_confirmed: number;
    bookings_cancelled: number;
    bookings_expired: number;
    utilization_rate: number;
    no_show_rate: number;
  };
  by_floor: Record<string, number>;
  by_zone: Record<string, number>;
  cost_center_hours: Record<string, number>;
}

export function useUtilizationReport(day: string) {
  return useQuery({
    queryKey: ["reports", "utilization", day],
    queryFn: () =>
      apiClient<UtilizationReportData>(`/api/v1/reports/utilization?day=${day}`),
    enabled: !!day,
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


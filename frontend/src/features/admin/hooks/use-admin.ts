"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface CostCenterApiItem {
  id: string;
  name: string;
  monthly_quota_hours: number;
}

export interface AccountApiItem {
  id: string;
  name: string;
  email: string;
  role: string;
  cost_center_id?: string | null;
  cost_center_name?: string | null;
  is_eligible_for_booking: boolean;
}

export interface QuotaApiItem {
  id: string;
  cost_center_id: string;
  cost_center_name: string;
  period_start: string;
  period_end: string;
  monthly_quota_hours: number;
  used_hours: number;
}

export interface HolidayApiItem {
  day: string;
  description: string;
}

export function useAdminCostCenters() {
  return useQuery({
    queryKey: ["admin", "cost-centers"],
    queryFn: () => apiClient<{ items: CostCenterApiItem[] }>("/api/v1/admin/cost-centers"),
  });
}

export function useUpdateCostCenter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      name,
      monthly_quota_hours,
    }: {
      id: string;
      name?: string;
      monthly_quota_hours?: number;
    }) => {
      return apiClient<CostCenterApiItem>(`/api/v1/admin/cost-centers/${id}`, {
        method: "PUT",
        body: JSON.stringify({ name, monthly_quota_hours }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "cost-centers"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "quotas"] });
    },
  });
}

export function useAdminAccounts() {
  return useQuery({
    queryKey: ["admin", "accounts"],
    queryFn: () => apiClient<{ items: AccountApiItem[] }>("/api/v1/admin/accounts"),
  });
}

export function useUpdateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      name,
      email,
      role,
      cost_center_id,
      is_eligible_for_booking,
    }: {
      id: string;
      name?: string;
      email?: string;
      role?: string;
      cost_center_id?: string;
      is_eligible_for_booking?: boolean;
    }) => {
      return apiClient<AccountApiItem>(`/api/v1/admin/accounts/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          name,
          email,
          role,
          cost_center_id,
          is_eligible_for_booking,
        }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "accounts"] });
    },
  });
}

export function useAdminQuotas() {
  return useQuery({
    queryKey: ["admin", "quotas"],
    queryFn: () => apiClient<{ items: QuotaApiItem[] }>("/api/v1/admin/quotas"),
  });
}

export function useAdminHolidays() {
  return useQuery({
    queryKey: ["admin", "holidays"],
    queryFn: () => apiClient<{ items: HolidayApiItem[] }>("/api/v1/admin/holidays"),
  });
}


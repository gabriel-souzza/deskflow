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

export interface CreateAccountPayload {
  name: string;
  email: string;
  password: string;
  cost_center_id: string;
  role: "employee" | "admin";
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

export function useCreateCostCenter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { name: string; monthly_quota_hours: number }) => {
      return apiClient<CostCenterApiItem>("/api/v1/admin/cost-centers", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "cost-centers"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "quotas"] });
    },
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

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateAccountPayload) => {
      return apiClient<AccountApiItem>("/api/v1/admin/accounts", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "accounts"] });
    },
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

export function useDeleteAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      return apiClient<{ id: string; deleted: boolean }>(`/api/v1/admin/accounts/${id}`, {
        method: "DELETE",
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

export function useCreateHoliday() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { day: string; description: string }) => {
      return apiClient<HolidayApiItem>("/api/v1/admin/holidays", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "holidays"] });
    },
  });
}

export function useDeleteHoliday() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (day: string) => {
      return apiClient<{ day: string; deleted: boolean }>(`/api/v1/admin/holidays/${day}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "holidays"] });
    },
  });
}

export interface AdminWorkspaceApiItem {
  id: string;
  code: string;
  floor: string;
  zone: string;
  type: "estacao" | "sala";
  capacity: number;
  resources: string[];
  is_active?: boolean;
}

export function useAdminWorkspaces() {
  return useQuery({
    queryKey: ["admin", "workspaces"],
    queryFn: () => apiClient<{ items: AdminWorkspaceApiItem[] }>("/api/v1/workspaces"),
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      code: string;
      floor: string;
      zone: string;
      type: "estacao" | "sala";
      capacity: number;
      resources: string[];
    }) => {
      return apiClient<AdminWorkspaceApiItem>("/api/v1/admin/workspaces", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "workspaces"] });
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },
  });
}

export function useUpdateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: {
      id: string;
      code?: string;
      floor?: string;
      zone?: string;
      type?: "estacao" | "sala";
      capacity?: number;
      resources?: string[];
      is_active?: boolean;
    }) => {
      return apiClient<AdminWorkspaceApiItem>(`/api/v1/admin/workspaces/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "workspaces"] });
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      return apiClient<void>(`/api/v1/admin/workspaces/${id}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "workspaces"] });
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },
  });
}

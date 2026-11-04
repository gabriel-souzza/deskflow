"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Employee, EmployeeRole } from "@/domain/entities/employee";
import { apiClient, clearToken, getToken, setToken } from "@/lib/api-client";

interface LoginCredentials {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface UserProfileResponse {
  id: string;
  name: string;
  email: string;
  role: string;
  cost_center_id?: string | null;
  cost_center_name?: string | null;
  is_eligible_for_booking: boolean;
}

export function useCurrentUser() {
  const token = typeof window !== "undefined" ? getToken() : null;

  return useQuery({
    queryKey: ["auth", "me", token],
    queryFn: async () => {
      if (!token) return null;
      const data = await apiClient<UserProfileResponse>("/api/v1/auth/me");
      return new Employee({
        id: data.id,
        name: data.name,
        email: data.email,
        role: data.role === "admin" ? EmployeeRole.ADMIN : EmployeeRole.EMPLOYEE,
        costCenterId: data.cost_center_id ?? null,
        costCenterName: data.cost_center_name ?? null,
        isEligibleForBooking: data.is_eligible_for_booking,
      });
    },
    enabled: !!token,
    staleTime: 1000 * 60 * 5,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const data = await apiClient<LoginResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      });
      setToken(data.access_token);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return () => {
    clearToken();
    queryClient.clear();
    window.location.href = "/login";
  };
}


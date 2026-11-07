"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Booking, BookingStatus } from "@/domain/entities/booking";
import { TimeSlot } from "@/domain/value-objects/time-slot";
import { apiClient } from "@/lib/api-client";

interface CreateBookingPayload {
  workspace_id: string;
  employee_id: string;
  cost_center_id: string;
  slot_start: string;
  slot_end: string;
}

interface BookingApiItem {
  id: string;
  workspace_id: string;
  employee_id: string;
  cost_center_id: string;
  slot_start: string;
  slot_end: string;
  status: string;
  qr_token?: string;
  created_at?: string;
}

export function useMyBookings() {
  return useQuery({
    queryKey: ["bookings", "my"],
    queryFn: async () => {
      const data = await apiClient<{ items: BookingApiItem[] }>("/api/v1/bookings");
      return data.items.map((item) =>
        Booking.create({
          id: item.id,
          workspaceId: item.workspace_id,
          employeeId: item.employee_id,
          costCenterId: item.cost_center_id,
          slot: TimeSlot.create(item.slot_start, item.slot_end),
          status: item.status as BookingStatus,
          createdAt: item.created_at ? new Date(item.created_at) : undefined,
        })
      );
    },
    refetchInterval: 1000 * 20,
  });
}

export function useCreateBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateBookingPayload) => {
      return apiClient<BookingApiItem>("/api/v1/bookings", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
      queryClient.invalidateQueries({ queryKey: ["quotas"] });
    },
  });
}

export function useCancelBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (bookingId: string) => {
      return apiClient<{ id: string; status: string }>(
        `/api/v1/bookings/${bookingId}`,
        { method: "DELETE" }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
      queryClient.invalidateQueries({ queryKey: ["quotas"] });
    },
  });
}

export function useCheckIn() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      bookingId,
      qrToken,
      simulate = false,
    }: {
      bookingId: string;
      qrToken: string;
      simulate?: boolean;
    }) => {
      const simParam = simulate ? "&simulate=true" : "";
      return apiClient<{ id: string; status: string }>(
        `/api/v1/bookings/${bookingId}/checkin?qr_token=${encodeURIComponent(qrToken)}${simParam}`,
        { method: "POST" }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}


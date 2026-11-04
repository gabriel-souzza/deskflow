"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { WaitlistEntry } from "@/domain/entities/waitlist";
import { TimeSlot } from "@/domain/value-objects/time-slot";
import { apiClient } from "@/lib/api-client";

interface JoinWaitlistPayload {
  workspace_id: string;
  slot_start: string;
  slot_end: string;
}

interface WaitlistApiItem {
  id: string;
  workspace_id: string;
  employee_id: string;
  slot_start?: string;
  slot_end?: string;
  desired_start?: string;
  desired_end?: string;
  created_at: string;
  notified_at?: string | null;
}

export function useMyWaitlist() {
  return useQuery({
    queryKey: ["waitlist", "my"],
    queryFn: async () => {
      const data = await apiClient<{ items: WaitlistApiItem[] }>("/api/v1/waitlist");
      return data.items.map((item) => {
        const start = item.slot_start || item.desired_start || "";
        const end = item.slot_end || item.desired_end || "";
        return WaitlistEntry.create({
          id: item.id,
          workspaceId: item.workspace_id,
          employeeId: item.employee_id,
          desiredSlot: TimeSlot.create(start, end),
          createdAt: new Date(item.created_at),
          notifiedAt: item.notified_at ? new Date(item.notified_at) : null,
        });
      });
    },
    refetchInterval: 1000 * 10,
  });
}

export function useJoinWaitlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: JoinWaitlistPayload) => {
      return apiClient<WaitlistApiItem>("/api/v1/waitlist", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["waitlist"] });
    },
  });
}

export function useCancelWaitlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (waitlistId: string) => {
      return apiClient<{ id: string; deleted: boolean }>(
        `/api/v1/waitlist/${waitlistId}`,
        { method: "DELETE" }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["waitlist"] });
    },
  });
}

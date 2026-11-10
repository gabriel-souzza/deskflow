"use client";

import { useQuery } from "@tanstack/react-query";
import { Workspace, WorkspaceType } from "@/domain/entities/workspace";
import { apiClient } from "@/lib/api-client";

export interface WorkspaceFilters {
  floor?: string;
  zone?: string;
  type?: WorkspaceType | string;
  resource?: string;
}

interface WorkspaceApiItem {
  id: string;
  code: string;
  floor: string;
  zone: string;
  type: string;
  capacity: number;
  resources?: string[] | Record<string, unknown>;
  is_active?: boolean;
}

export interface AvailabilitySlotApi {
  slot_index: number;
  time: string;
  start?: string;
  end?: string;
  seats_available: number;
  capacity: number;
  is_full: boolean;
}

export interface WorkspaceAvailabilityApiResponse {
  workspace_id: string;
  day: string;
  slots: AvailabilitySlotApi[];
}

export function useWorkspaces(filters: WorkspaceFilters = {}) {
  const params = new URLSearchParams();
  if (filters.floor) params.set("floor", filters.floor);
  if (filters.zone) params.set("zone", filters.zone);
  if (filters.type) params.set("type", filters.type);
  if (filters.resource) params.set("resource", filters.resource);

  const queryString = params.toString();
  const endpoint = `/api/v1/workspaces${queryString ? `?${queryString}` : ""}`;

  return useQuery({
    queryKey: ["workspaces", filters],
    queryFn: async () => {
      const data = await apiClient<{ items: WorkspaceApiItem[] }>(endpoint);
      return data.items.map((item) =>
        Workspace.create({
          id: item.id,
          code: item.code,
          floor: item.floor,
          zone: item.zone,
          type:
            item.type === "sala"
              ? WorkspaceType.MEETING_ROOM
              : WorkspaceType.STATION,
          capacity: item.capacity,
          resources: item.resources,
          isActive: item.is_active ?? true,
        })
      );
    },
  });
}

export function useWorkspaceAvailability(workspaceId: string, day: string) {
  return useQuery({
    queryKey: ["availability", workspaceId, day],
    queryFn: async () => {
      const data = await apiClient<WorkspaceAvailabilityApiResponse>(
        `/api/v1/workspaces/${workspaceId}/availability?day=${day}`
      );
      const normalizedSlots = (data.slots || []).map((slot) => {
        const time =
          slot.time ||
          (slot.start ? slot.start.slice(11, 16) : "") ||
          `${String(8 + Math.floor((slot.slot_index * 15) / 60)).padStart(2, "0")}:${String(
            (slot.slot_index * 15) % 60
          ).padStart(2, "0")}`;
        const is_full =
          slot.is_full !== undefined ? slot.is_full : slot.seats_available <= 0;
        return {
          ...slot,
          time,
          is_full,
        };
      });
      return {
        ...data,
        slots: normalizedSlots,
      };
    },
    enabled: !!workspaceId && !!day,
    refetchInterval: 1000 * 15,
  });
}


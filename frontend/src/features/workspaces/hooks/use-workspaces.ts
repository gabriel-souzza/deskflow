"use client";

import { useQuery } from "@tanstack/react-query";
import { Workspace, WorkspaceType } from "@/domain/entities/workspace";
import { apiClient } from "@/lib/api-client";

export interface WorkspaceFilters {
  floor?: string;
  zone?: string;
  type?: WorkspaceType | string;
}

interface WorkspaceApiItem {
  id: string;
  code: string;
  floor: string;
  zone: string;
  type: string;
  capacity: number;
  resources?: Record<string, unknown>;
  is_active?: boolean;
}

interface AvailabilitySlotApi {
  slot_index: number;
  time: string;
  seats_available: number;
  capacity: number;
  is_full: boolean;
}

interface WorkspaceAvailabilityApiResponse {
  workspace_id: string;
  day: string;
  slots: AvailabilitySlotApi[];
}

export function useWorkspaces(filters: WorkspaceFilters = {}) {
  const params = new URLSearchParams();
  if (filters.floor) params.set("floor", filters.floor);
  if (filters.zone) params.set("zone", filters.zone);
  if (filters.type) params.set("type", filters.type);

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
      return apiClient<WorkspaceAvailabilityApiResponse>(
        `/api/v1/workspaces/${workspaceId}/availability?day=${day}`
      );
    },
    enabled: !!workspaceId && !!day,
    refetchInterval: 1000 * 15,
  });
}


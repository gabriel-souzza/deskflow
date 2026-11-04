"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/api-client";

export interface RealtimeEventPayload {
  type: string;
  [key: string]: unknown;
}

export function useRealtimeEvents(onEvent?: (event: RealtimeEventPayload) => void) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (typeof window === "undefined") return;

    const streamUrl = `${API_BASE_URL}/api/v1/availability/stream`;
    let eventSource: EventSource | null = null;

    try {
      eventSource = new EventSource(streamUrl);

      eventSource.onmessage = (e) => {
        try {
          const data: RealtimeEventPayload = JSON.parse(e.data);

          if (onEvent) {
            onEvent(data);
          }

          // Automatically synchronize TanStack Query cache on domain events
          switch (data.type) {
            case "booking.created":
            case "booking.confirmed":
            case "booking.cancelled":
            case "booking.expired":
            case "availability.changed":
              queryClient.invalidateQueries({ queryKey: ["availability"] });
              queryClient.invalidateQueries({ queryKey: ["workspaces"] });
              queryClient.invalidateQueries({ queryKey: ["bookings"] });
              queryClient.invalidateQueries({ queryKey: ["reports"] });
              break;

            case "waitlist.joined":
            case "waitlist.notified":
              queryClient.invalidateQueries({ queryKey: ["waitlist"] });
              queryClient.invalidateQueries({ queryKey: ["availability"] });
              break;

            case "quota.alert":
            case "quota.consumed":
              queryClient.invalidateQueries({ queryKey: ["quotas"] });
              queryClient.invalidateQueries({ queryKey: ["admin", "quotas"] });
              break;
          }
        } catch {
          // Ignore heartbeat or non-JSON comments
        }
      };

      eventSource.onerror = () => {
        // EventSource will auto-reconnect
      };
    } catch {
      // Stream unavailable
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [queryClient, onEvent]);
}

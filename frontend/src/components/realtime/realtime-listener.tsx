"use client";

import { useState } from "react";
import { AlertCircle } from "lucide-react";
import { useRealtimeEvents } from "@/features/realtime/hooks/use-realtime-events";

export function RealtimeListener() {
  const [quotaToast, setQuotaToast] = useState<string | null>(null);

  useRealtimeEvents((event) => {
    if (event.type === "quota.alert" && typeof event.message === "string") {
      setQuotaToast(event.message);
      setTimeout(() => setQuotaToast(null), 6000);
    }
  });

  return (
    <>
      {quotaToast && (
        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-lg bg-red-600 px-4 py-3 text-sm text-white shadow-xl animate-in slide-in-from-bottom">
          <AlertCircle className="h-4 w-4" />
          <span>{quotaToast}</span>
        </div>
      )}
    </>
  );
}

"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useState } from "react";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 30, // 30 seconds
            gcTime: 1000 * 60 * 60 * 24, // 24 hours
            retry: (failureCount, error) => {
              if (error instanceof Error && "status" in error) {
                const status = (error as { status: number }).status;
                if (status >= 400 && status < 500) return false;
              }
              return failureCount < 2;
            },
            networkMode: "offlineFirst",
          },
          mutations: {
            networkMode: "offlineFirst",
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}


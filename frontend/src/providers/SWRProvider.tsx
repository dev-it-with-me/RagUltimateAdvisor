import { SWRConfig } from "swr";
import { fetcher } from "@/lib/api-client";

interface SWRProviderProps {
  children: React.ReactNode;
}

export const SWRProvider = ({ children }: SWRProviderProps) => {
  return (
    <SWRConfig
      value={{
        fetcher,
        revalidateOnFocus: false,
        revalidateOnReconnect: true,
        dedupingInterval: 5000,
        errorRetryCount: 3,
        errorRetryInterval: 1000,
        shouldRetryOnError: (error) => {
          // Don't retry on 4xx errors (client errors)
          return !error?.message?.includes("HTTP 4");
        },
        onError: (error) => {
          console.error("SWR Error:", error);
        },
      }}
    >
      {children}
    </SWRConfig>
  );
};

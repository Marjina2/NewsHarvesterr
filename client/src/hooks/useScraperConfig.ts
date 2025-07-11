import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { ScraperConfig, UpdateScraperConfig } from "@shared/schema";

export function useScraperConfig() {
  return useQuery<ScraperConfig>({
    queryKey: ["/api/config"],
    staleTime: 30000,
  });
}

export function useUpdateScraperConfig() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (config: UpdateScraperConfig) => 
      apiRequest("POST", "/api/config", config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/config"] });
      queryClient.invalidateQueries({ queryKey: ["/api/scraper/status"] });
    },
  });
}

export function useScraperControls() {
  const queryClient = useQueryClient();
  
  const startScraper = useMutation({
    mutationFn: () => apiRequest("POST", "/api/scraper/start"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/scraper/status"] });
      queryClient.invalidateQueries({ queryKey: ["/api/config"] });
    },
  });

  const stopScraper = useMutation({
    mutationFn: () => apiRequest("POST", "/api/scraper/stop"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/scraper/status"] });
      queryClient.invalidateQueries({ queryKey: ["/api/config"] });
    },
  });

  return { startScraper, stopScraper };
}

import { useQuery } from "@tanstack/react-query";
import { NewsArticle } from "@shared/schema";

export function useNews(limit = 50, offset = 0) {
  return useQuery<NewsArticle[]>({
    queryKey: ["/api/news", { limit, offset }],
    staleTime: 30000, // Consider data fresh for 30 seconds
  });
}

export function useNewsStats() {
  return useQuery({
    queryKey: ["/api/stats"],
    staleTime: 60000, // Consider stats fresh for 1 minute
  });
}

import { useQuery } from "@tanstack/react-query";
import { NewsArticle } from "@shared/schema";

export function useNews(limit = 50, offset = 0) {
  return useQuery<NewsArticle[]>({
    queryKey: ["/api/news", limit, offset],
    queryFn: async () => {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/news?limit=${limit}&offset=${offset}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Failed to fetch news articles');
      }
      return response.json();
    },
    staleTime: 30000, // Consider data fresh for 30 seconds
  });
}

export function useNewsStats() {
  return useQuery({
    queryKey: ["/api/stats"],
    queryFn: async () => {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }
      return response.json();
    },
    staleTime: 60000, // Consider stats fresh for 1 minute
  });
}

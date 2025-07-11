import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { NewsStats } from "@shared/schema";

export default function StatisticsPanel() {
  const { data: stats, isLoading } = useQuery<NewsStats>({
    queryKey: ["/api/stats"],
    refetchInterval: 60000, // Refresh every minute
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-slate-200 rounded w-3/4" />
            <div className="grid grid-cols-2 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="text-center">
                  <div className="h-8 bg-slate-200 rounded mb-2" />
                  <div className="h-3 bg-slate-200 rounded" />
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-500">
              {stats?.totalArticles || 0}
            </div>
            <div className="text-xs text-slate-500">Total Articles</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-500">
              {stats?.todayArticles || 0}
            </div>
            <div className="text-xs text-slate-500">Today</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-500">
              {stats?.activeSources || 0}
            </div>
            <div className="text-xs text-slate-500">Sources</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-500">
              {stats?.avgPerHour || 0}
            </div>
            <div className="text-xs text-slate-500">Avg/Hour</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

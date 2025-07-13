import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Newspaper, Play, Square, RefreshCw } from "lucide-react";
import ScraperControls from "@/components/ScraperControls";
import NewsSourcesManager from "@/components/NewsSourcesManager";
import NewsDisplay from "@/components/NewsDisplay";
import StatisticsPanel from "@/components/StatisticsPanel";
import { ScraperStatus } from "@shared/schema";

export default function Dashboard() {
  const [lastUpdate, setLastUpdate] = useState<string>("Never");

  const { data: scraperStatus, isLoading } = useQuery<ScraperStatus>({
    queryKey: ["/api/scraper/status"],
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  useEffect(() => {
    const updateLastUpdate = () => {
      setLastUpdate(new Date().toLocaleTimeString());
    };

    const interval = setInterval(updateLastUpdate, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  const getStatusIndicator = () => {
    if (isLoading) return { color: "bg-gray-500", text: "Loading..." };
    if (scraperStatus?.isActive) return { color: "bg-green-500 animate-pulse", text: "Running" };
    return { color: "bg-red-500 animate-pulse", text: "Stopped" };
  };

  const status = getStatusIndicator();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Newspaper className="h-8 w-8 text-blue-500" />
              <div>
                <h1 className="text-2xl font-semibold text-slate-800">News Scraper Dashboard</h1>
                <p className="text-sm text-slate-500">AI-powered news aggregation and rephrasing</p>
              </div>
            </div>
            {/* API URL Display */}
            <div className="mt-4 p-3 bg-white/70 rounded-lg inline-block">
              <p className="text-sm text-gray-700">
                <span className="font-semibold">API Base URL:</span>{" "}
                <code className="bg-gray-100 px-2 py-1 rounded text-blue-600 font-mono">
                  {window.location.origin}/api
                </code>
              </p>
              <p className="text-xs text-gray-500 mt-1">
                All Articles JSON: <code className="bg-gray-100 px-1 rounded">/api/articles/all</code>
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${status.color}`} />
                <span className="text-sm font-medium text-slate-600">{status.text}</span>
              </div>
              <div className="text-sm text-slate-500">
                <span>Last update: {lastUpdate}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <ScraperControls />
            <NewsSourcesManager />
            <StatisticsPanel />
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2">
            <NewsDisplay />
          </div>
        </div>
      </div>
    </div>
  );
}
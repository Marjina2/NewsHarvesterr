import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Newspaper, RefreshCw, ExternalLink, MoreHorizontal, Loader2 } from "lucide-react";
import { NewsArticle } from "@shared/schema";

export default function NewsDisplay() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [limit, setLimit] = useState(15);

  const { data: articles, isLoading, refetch, isFetching } = useQuery<NewsArticle[]>({
    queryKey: ["/api/news"],
    refetchInterval: autoRefresh ? 60000 : false, // Auto-refresh every minute if enabled
  });

  const handleRefresh = () => {
    refetch();
  };

  const handleLoadMore = () => {
    setLimit(prev => prev + 15);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-700";
      case "processing":
        return "bg-yellow-100 text-yellow-700";
      case "failed":
        return "bg-red-100 text-red-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "Rephrased";
      case "processing":
        return "Processing";
      case "failed":
        return "Failed";
      default:
        return "Pending";
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} hours ago`;
    return `${Math.floor(diffInMinutes / 1440)} days ago`;
  };

  const getSourceIconColor = (sourceName: string) => {
    const colors = {
      "BBC News": "bg-red-100 text-red-500",
      "Reuters": "bg-orange-100 text-orange-500",
      "CNN": "bg-blue-100 text-blue-500",
    };
    return colors[sourceName as keyof typeof colors] || "bg-gray-100 text-gray-500";
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-slate-200 rounded w-3/4" />
              <div className="h-8 bg-slate-200 rounded" />
              <div className="h-4 bg-slate-200 rounded w-1/2" />
            </div>
          </CardContent>
        </Card>
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-slate-200 rounded w-1/4" />
                <div className="h-16 bg-slate-200 rounded" />
                <div className="h-16 bg-slate-200 rounded" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* News Feed Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800">Latest News</h2>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-slate-500">Auto-refresh:</span>
                <Switch
                  checked={autoRefresh}
                  onCheckedChange={setAutoRefresh}
                />
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={isFetching}
                className="text-slate-500 hover:text-slate-700"
              >
                <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-slate-500">
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
            <span>Showing {Math.min(limit, articles?.length || 0)} of {articles?.length || 0} articles</span>
          </div>
        </CardContent>
      </Card>

      {/* News Articles */}
      <div className="space-y-4">
        {articles?.slice(0, limit).map((article) => (
          <Card key={article.id} className="hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getSourceIconColor(article.sourceName)}`}>
                    <Newspaper className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-slate-800">{article.sourceName}</span>
                    <span className="text-xs text-slate-500 ml-2">
                      {formatTimeAgo(article.scrapedAt!.toString())}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(article.status)}>
                    {getStatusText(article.status)}
                  </Badge>
                  <Button variant="ghost" size="sm" className="text-slate-400 hover:text-slate-600">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="bg-slate-50 rounded-lg p-4">
                  <h3 className="font-medium text-slate-800 mb-2">{article.originalTitle}</h3>
                  <p className="text-sm text-slate-600">Original headline</p>
                  {article.originalUrl && (
                    <Button 
                      variant="link" 
                      size="sm" 
                      className="p-0 h-auto text-xs text-blue-600 hover:text-blue-800 mt-1"
                      onClick={() => window.open(article.originalUrl, '_blank')}
                    >
                      <ExternalLink className="w-3 h-3 mr-1" />
                      View source
                    </Button>
                  )}
                </div>
                
                <div className="bg-blue-50 rounded-lg p-4">
                  {article.status === "processing" ? (
                    <div className="flex items-center justify-center text-slate-500">
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      <span className="text-sm">Processing with AI...</span>
                    </div>
                  ) : article.status === "completed" && article.rephrasedTitle ? (
                    <>
                      <h3 className="font-medium text-slate-800 mb-2">{article.rephrasedTitle}</h3>
                      <p className="text-sm text-blue-600">AI-rephrased version</p>
                    </>
                  ) : article.status === "failed" ? (
                    <div className="text-center text-red-500">
                      <p className="text-sm">Failed to rephrase this article</p>
                    </div>
                  ) : (
                    <div className="text-center text-slate-500">
                      <p className="text-sm">Waiting for AI processing...</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {articles?.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <Newspaper className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-800 mb-2">No news articles yet</h3>
              <p className="text-slate-500 mb-4">Start the scraper to begin collecting news articles</p>
              <Button onClick={handleRefresh} disabled={isFetching}>
                <RefreshCw className={`w-4 h-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </CardContent>
          </Card>
        )}

        {articles && articles.length > limit && (
          <div className="flex justify-center">
            <Button
              variant="outline"
              onClick={handleLoadMore}
              className="bg-white border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              Load More Articles
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Newspaper, RefreshCw, ExternalLink, Loader2, Eye, Download, User, Calendar, Clock } from "lucide-react";
import { NewsArticle } from "@shared/schema";

export default function NewsDisplay() {
  const [showRephrasedOnly, setShowRephrasedOnly] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);

  const { data: articles, isLoading, refetch, isFetching } = useQuery<NewsArticle[]>({
    queryKey: ["/api/news"],
    refetchInterval: 5000,
  });

  const filteredArticles = articles?.filter((article: NewsArticle) => 
    !showRephrasedOnly || article.rephrasedTitle
  ) || [];

  const handleRefresh = () => {
    refetch();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "processing":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "completed":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "failed":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const handleDownloadJSON = async (articleId: number) => {
    try {
      const response = await fetch(`/api/articles/${articleId}/json`);
      const data = await response.json();
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `article-${articleId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download article JSON:', error);
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading news articles...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Newspaper className="h-6 w-6" />
          News Articles ({filteredArticles.length})
        </h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label htmlFor="rephrased-only" className="text-sm font-medium">
              Show rephrased only
            </label>
            <Switch
              id="rephrased-only"
              checked={showRephrasedOnly}
              onCheckedChange={setShowRephrasedOnly}
            />
          </div>
          <Button onClick={handleRefresh} variant="outline" size="sm" disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {filteredArticles.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Newspaper className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-500">No news articles found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredArticles.map((article: NewsArticle) => (
            <Card key={article.id} className="hover:shadow-lg transition-shadow cursor-pointer group h-full flex flex-col">
              <div className="relative">
                {article.imageUrl && (
                  <div className="aspect-video w-full overflow-hidden rounded-t-lg">
                    <img 
                      src={article.imageUrl} 
                      alt={article.originalTitle}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  </div>
                )}
                <div className="absolute top-2 right-2">
                  <Badge className={getStatusColor(article.status)}>
                    {article.status}
                  </Badge>
                </div>
              </div>
              
              <CardHeader className="pb-2 flex-grow">
                <CardTitle className="text-lg leading-tight line-clamp-2 mb-2">
                  {article.rephrasedTitle || article.originalTitle}
                </CardTitle>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className="font-medium">{article.sourceName}</span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatTimeAgo(article.scrapedAt!.toString())}
                  </span>
                </div>
              </CardHeader>
              
              <CardContent className="pt-0">
                {article.excerpt && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                    {article.excerpt}
                  </p>
                )}
                
                {article.author && (
                  <div className="flex items-center gap-1 text-sm text-gray-500 mb-3">
                    <User className="h-3 w-3" />
                    <span className="truncate">{article.author}</span>
                  </div>
                )}
                
                {article.rephrasedTitle && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-2 rounded-lg mb-3">
                    <p className="text-xs text-blue-600 dark:text-blue-400 mb-1">AI Rephrased</p>
                  </div>
                )}
                
                <div className="flex items-center gap-2 mt-auto">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedArticle(article)}
                        className="flex items-center gap-1 flex-1"
                      >
                        <Eye className="h-3 w-3" />
                        View Full Article
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle className="text-xl leading-tight pr-6">
                          {article.rephrasedTitle || article.originalTitle}
                        </DialogTitle>
                      </DialogHeader>
                      
                      <div className="space-y-4">
                        <div className="flex items-center gap-4 text-sm text-gray-500 flex-wrap">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatTimeAgo(article.scrapedAt!.toString())}
                          </span>
                          {article.author && (
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {article.author}
                            </span>
                          )}
                          <span className="font-medium">{article.sourceName}</span>
                          <Badge className={getStatusColor(article.status)}>
                            {article.status}
                          </Badge>
                        </div>
                        
                        {article.imageUrl && (
                          <div className="aspect-video w-full overflow-hidden rounded-lg">
                            <img 
                              src={article.imageUrl} 
                              alt={article.originalTitle}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        )}
                        
                        {article.rephrasedTitle && (
                          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                            <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">AI Rephrased Title:</p>
                            <p className="text-blue-800 dark:text-blue-200 font-medium">{article.rephrasedTitle}</p>
                            <p className="text-sm text-blue-700 dark:text-blue-300 mt-2">
                              <span className="font-medium">Original:</span> {article.originalTitle}
                            </p>
                          </div>
                        )}
                        
                        {article.fullContent && (
                          <div className="prose max-w-none dark:prose-invert">
                            <h3 className="text-lg font-semibold mb-3">Full Article Content</h3>
                            <div className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
                              {article.fullContent}
                            </div>
                          </div>
                        )}
                        
                        {!article.fullContent && article.excerpt && (
                          <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                            <h3 className="text-lg font-semibold mb-2">Article Excerpt</h3>
                            <p className="text-gray-700 dark:text-gray-300">{article.excerpt}</p>
                          </div>
                        )}
                        
                        <div className="flex items-center gap-2 pt-4 border-t">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(article.originalUrl, '_blank')}
                            className="flex items-center gap-1"
                          >
                            <ExternalLink className="h-3 w-3" />
                            Read Original Article
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownloadJSON(article.id)}
                            className="flex items-center gap-1"
                          >
                            <Download className="h-3 w-3" />
                            Download JSON
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDownloadJSON(article.id)}
                    className="flex items-center gap-1"
                    title="Download JSON"
                  >
                    <Download className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
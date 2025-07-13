import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Newspaper, RefreshCw, ExternalLink, Loader2, Eye, Download, User, Calendar, Clock, Filter, Globe, MapPin } from "lucide-react";
import { NewsArticle } from "@shared/schema";

export default function NewsDisplay() {
  const [showRephrasedOnly, setShowRephrasedOnly] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedRegion, setSelectedRegion] = useState<string>("all");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [articlesPerPage] = useState(20); // Show 20 articles per page

  const { data: articles, isLoading, refetch, isFetching } =
    useQuery<NewsArticle[]>({
      queryKey: ["/api/news", articlesPerPage, (currentPage - 1) * articlesPerPage],
      queryFn: async () => {
        const limit = articlesPerPage;
        const offset = (currentPage - 1) * articlesPerPage;
        const response = await fetch(`/api/news?limit=${limit}&offset=${offset}`);
        if (!response.ok) {
          throw new Error('Failed to fetch news articles');
        }
        return response.json();
      },
      staleTime: 30000,
    });

  // Get total articles count for pagination
  const { data: allArticlesData } = useQuery({
    queryKey: ["/api/articles/all", 1],
    queryFn: async () => {
      const response = await fetch(`/api/news?limit=1000`); // Get a large number to count
      if (!response.ok) {
        throw new Error('Failed to fetch articles count');
      }
      const data = await response.json();
      return { total: data.length };
    },
    select: (data: any) => ({ total: data.total }),
    staleTime: 60000,
  });

  const filteredArticles = articles?.filter((article: NewsArticle) => {
    const matchesRephrased = !showRephrasedOnly || article.rephrasedTitle;
    const matchesCategory = selectedCategory === "all" || article.category === selectedCategory;
    const matchesRegion = selectedRegion === "all" || article.region === selectedRegion;
    return matchesRephrased && matchesCategory && matchesRegion;
  }) || [];

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "technology":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "business":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "politics":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
      case "sports":
        return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200";
      case "science":
        return "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200";
      case "entertainment":
        return "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const getRegionColor = (region: string) => {
    switch (region) {
      case "indian":
        return "bg-saffron-100 text-saffron-800 dark:bg-saffron-900 dark:text-saffron-200";
      case "international":
        return "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

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

  // Handle page changes
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const totalArticles = allArticlesData?.total || 0;
  const totalPages = Math.ceil(totalArticles / articlesPerPage);

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
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Newspaper className="h-6 w-6" />
            News Articles ({filteredArticles.length})
          </h2>
          <Button onClick={handleRefresh} variant="outline" size="sm" disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filters:</span>
          </div>

          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-gray-500" />
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="general">General</SelectItem>
                <SelectItem value="technology">Technology</SelectItem>
                <SelectItem value="business">Business</SelectItem>
                <SelectItem value="politics">Politics</SelectItem>
                <SelectItem value="sports">Sports</SelectItem>
                <SelectItem value="science">Science</SelectItem>
                <SelectItem value="entertainment">Entertainment</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-gray-500" />
            <Select value={selectedRegion} onValueChange={setSelectedRegion}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Region" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Regions</SelectItem>
                <SelectItem value="indian">Indian News</SelectItem>
                <SelectItem value="international">International</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Switch
              id="rephrased-only"
              checked={showRephrasedOnly}
              onCheckedChange={setShowRephrasedOnly}
            />
            <label htmlFor="rephrased-only" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Show rephrased only
            </label>
          </div>
        </div>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mb-6">
          <div className="text-sm text-gray-500">
            Page {currentPage} of {totalPages} ({totalArticles} total articles)
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              Previous
            </Button>

            {/* Page numbers */}
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <Button
                    key={pageNum}
                    variant={currentPage === pageNum ? "default" : "outline"}
                    size="sm"
                    onClick={() => handlePageChange(pageNum)}
                    className="w-8 h-8 p-0"
                  >
                    {pageNum}
                  </Button>
                );
              })}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}

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
                <div className="flex items-center gap-1 text-sm text-gray-500 mb-2">
                  <Clock className="h-3 w-3" />
                  {formatTimeAgo(article.scrapedAt!.toString())}
                </div>

                <div className="flex items-center gap-2 mb-2">
                  <Badge className={getCategoryColor(article.category || 'general')}>
                    {article.category || 'general'}
                  </Badge>
                  <Badge className={getRegionColor(article.region || 'international')}>
                    {article.region === 'indian' ? '🇮🇳 Indian' : '🌍 International'}
                  </Badge>
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

      {/* Bottom Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center mt-8">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              ← Previous
            </Button>
            <span className="px-4 py-2 text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              Next →
            </Button>
          </div>
        </div>
      )}

      {/* Article Details Modal */}
    </div>
  );
}
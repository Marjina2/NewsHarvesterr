
import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Plus, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { NewsSource } from "@shared/schema";

export default function NewsSourcesManager() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [newSourceName, setNewSourceName] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const { data: sources, isLoading } = useQuery<NewsSource[]>({
    queryKey: ["/api/sources"],
  });

  const addSourceMutation = useMutation({
    mutationFn: (source: { name: string; url: string; isActive: boolean }) =>
      apiRequest("POST", "/api/sources", source),
    onSuccess: () => {
      toast({
        title: "Success",
        description: "News source added successfully",
      });
      setNewSourceUrl("");
      setNewSourceName("");
      queryClient.invalidateQueries({ queryKey: ["/api/sources"] });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to add news source",
        variant: "destructive",
      });
    },
  });

  const removeSourceMutation = useMutation({
    mutationFn: (id: number) => apiRequest("DELETE", `/api/sources/${id}`),
    onSuccess: () => {
      toast({
        title: "Success",
        description: "News source removed successfully",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/sources"] });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to remove news source",
        variant: "destructive",
      });
    },
  });

  const handleAddSource = () => {
    if (!newSourceUrl || !newSourceName) {
      toast({
        title: "Error",
        description: "Please enter both name and URL",
        variant: "destructive",
      });
      return;
    }

    try {
      new URL(newSourceUrl); // Validate URL
      addSourceMutation.mutate({
        name: newSourceName,
        url: newSourceUrl,
        isActive: true,
      });
    } catch {
      toast({
        title: "Error",
        description: "Please enter a valid URL",
        variant: "destructive",
      });
    }
  };

  const extractDomainName = (url: string) => {
    try {
      const domain = new URL(url).hostname;
      return domain.replace("www.", "");
    } catch {
      return url;
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-slate-200 rounded w-3/4" />
            <div className="h-8 bg-slate-200 rounded" />
            <div className="h-16 bg-slate-200 rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-slate-50">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                News Sources ({sources?.length || 0})
                {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </CardTitle>
              <Button 
                size="sm" 
                className="bg-blue-500 hover:bg-blue-600"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsOpen(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1" />
                Add
              </Button>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Input
                placeholder="Source name (e.g., BBC News)"
                value={newSourceName}
                onChange={(e) => setNewSourceName(e.target.value)}
              />
              <div className="flex space-x-2">
                <Input
                  placeholder="https://example.com/news"
                  value={newSourceUrl}
                  onChange={(e) => setNewSourceUrl(e.target.value)}
                  className="flex-1"
                />
                <Button
                  onClick={handleAddSource}
                  disabled={addSourceMutation.isPending}
                  className="bg-green-500 hover:bg-green-600"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="space-y-3">
              {sources?.map((source) => (
                <div
                  key={source.id}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${source.isActive ? 'bg-green-500' : 'bg-gray-400'}`} />
                    <div>
                      <p className="text-sm font-medium text-slate-800">{source.name}</p>
                      <p className="text-xs text-slate-500">{extractDomainName(source.url)}</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeSourceMutation.mutate(source.id)}
                    disabled={removeSourceMutation.isPending}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
              {sources?.length === 0 && (
                <div className="text-center py-8 text-slate-500">
                  <p>No news sources configured</p>
                  <p className="text-sm">Add your first source above</p>
                </div>
              )}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

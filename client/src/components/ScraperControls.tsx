import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Play, Square } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { ScraperConfig } from "@shared/schema";

export default function ScraperControls() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [intervalMinutes, setIntervalMinutes] = useState(20);

  const { data: config, isLoading } = useQuery<ScraperConfig>({
    queryKey: ["/api/config"],
    onSuccess: (data) => {
      if (data) {
        setIntervalMinutes(data.intervalMinutes);
      }
    },
  });

  const startMutation = useMutation({
    mutationFn: () => apiRequest("POST", "/api/scraper/start"),
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Scraper started successfully",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/scraper/status"] });
      queryClient.invalidateQueries({ queryKey: ["/api/config"] });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to start scraper",
        variant: "destructive",
      });
    },
  });

  const stopMutation = useMutation({
    mutationFn: () => apiRequest("POST", "/api/scraper/stop"),
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Scraper stopped successfully",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/scraper/status"] });
      queryClient.invalidateQueries({ queryKey: ["/api/config"] });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to stop scraper",
        variant: "destructive",
      });
    },
  });

  const updateConfigMutation = useMutation({
    mutationFn: (newConfig: { intervalMinutes: number }) =>
      apiRequest("POST", "/api/config", newConfig),
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Configuration updated successfully",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/config"] });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to update configuration",
        variant: "destructive",
      });
    },
  });

  const handleIntervalChange = (value: number[]) => {
    const newInterval = value[0];
    setIntervalMinutes(newInterval);
    updateConfigMutation.mutate({ intervalMinutes: newInterval });
  };

  const formatInterval = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} minutes`;
    }
    return `${Math.round(minutes / 60)} hours`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-slate-200 rounded w-3/4" />
            <div className="h-8 bg-slate-200 rounded" />
            <div className="h-4 bg-slate-200 rounded w-1/2" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scraper Controls</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex space-x-3">
          <Button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending || config?.isActive}
            className="flex-1 bg-green-500 hover:bg-green-600"
          >
            <Play className="w-4 h-4 mr-2" />
            Start
          </Button>
          <Button
            onClick={() => stopMutation.mutate()}
            disabled={stopMutation.isPending || !config?.isActive}
            variant="destructive"
            className="flex-1"
          >
            <Square className="w-4 h-4 mr-2" />
            Stop
          </Button>
        </div>

        <div className="bg-slate-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-600">Scraping Interval</span>
            <span className="text-sm text-slate-500">{formatInterval(intervalMinutes)}</span>
          </div>
          <Slider
            value={[intervalMinutes]}
            onValueChange={handleIntervalChange}
            min={5}
            max={120}
            step={5}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>5 min</span>
            <span>60 min</span>
            <span>120 min</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

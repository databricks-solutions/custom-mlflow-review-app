import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Palette, Sparkles } from "lucide-react";
import { rendererRegistry } from "@/components/session-renderer/renderers";
import { useRendererName, useSetRendererTag } from "@/hooks/api-hooks";

interface RendererSelectorProps {
  runId: string;
  sessionName?: string;
}

export function RendererSelector({ runId, sessionName }: RendererSelectorProps) {
  const [selectedRenderer, setSelectedRenderer] = useState<string>("");
  
  const { rendererName: currentRenderer, isLoading } = useRendererName(runId, !!runId);
  const setRendererTag = useSetRendererTag();
  
  const availableRenderers = rendererRegistry.listRenderers();
  const currentRendererInfo = currentRenderer 
    ? rendererRegistry.getRenderer(currentRenderer)
    : rendererRegistry.getRenderer(); // Gets default

  const handleRendererChange = (newRenderer: string) => {
    setSelectedRenderer(newRenderer);
  };

  const handleApplyRenderer = () => {
    if (selectedRenderer && runId) {
      setRendererTag.mutate({ runId, rendererName: selectedRenderer });
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Custom Renderer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">Loading renderer settings...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Palette className="h-5 w-5" />
          Custom Renderer
        </CardTitle>
        <CardDescription>
          Choose how traces and labeling schemas are displayed in this session
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Renderer Display */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Current Renderer</div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <Sparkles className="h-3 w-3" />
              {currentRendererInfo.displayName}
            </Badge>
          </div>
          <div className="text-sm text-muted-foreground">
            {currentRendererInfo.description}
          </div>
        </div>

        {/* Renderer Selection */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Change Renderer</div>
          <Select value={selectedRenderer} onValueChange={handleRendererChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select a renderer..." />
            </SelectTrigger>
            <SelectContent>
              {availableRenderers.map((renderer) => (
                <SelectItem key={renderer.name} value={renderer.name}>
                  <div className="flex flex-col">
                    <span>{renderer.displayName}</span>
                    <span className="text-xs text-muted-foreground">
                      {renderer.description}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Apply Button */}
        {selectedRenderer && selectedRenderer !== currentRenderer && (
          <Button 
            onClick={handleApplyRenderer}
            disabled={setRendererTag.isPending}
            className="w-full"
          >
            {setRendererTag.isPending ? "Applying..." : `Apply ${rendererRegistry.getRenderer(selectedRenderer).displayName}`}
          </Button>
        )}

        {/* Session Info */}
        {sessionName && (
          <div className="text-xs text-muted-foreground pt-2 border-t">
            Session: {sessionName}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
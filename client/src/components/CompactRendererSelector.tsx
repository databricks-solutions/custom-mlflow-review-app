import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { rendererRegistry } from "@/components/session-renderer/renderers";
import { useRendererName, useSetRendererTag } from "@/hooks/api-hooks";

interface CompactRendererSelectorProps {
  runId: string;
  sessionName?: string;
}

export function CompactRendererSelector({ runId, sessionName }: CompactRendererSelectorProps) {
  const rendererQuery = useRendererName(runId, !!runId);
  const setRendererTag = useSetRendererTag();
  
  const currentRenderer = rendererQuery.data?.rendererName;
  const isLoading = rendererQuery.isLoading;
  
  const availableRenderers = rendererRegistry.listRenderers();
  const currentRendererInfo = currentRenderer 
    ? rendererRegistry.getRenderer(currentRenderer)
    : rendererRegistry.getRenderer(); // Gets default

  const handleRendererChange = (newRenderer: string) => {
    if (newRenderer && runId && newRenderer !== currentRenderer) {
      setRendererTag.mutate({ runId, rendererName: newRenderer });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        Loading renderer settings...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <Select 
          value={currentRenderer || ""} 
          onValueChange={handleRendererChange}
          disabled={setRendererTag.isPending}
        >
          <SelectTrigger className="w-48">
            <div className="flex items-center gap-2">
              <SelectValue placeholder={currentRendererInfo.displayName} />
              {setRendererTag.isPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
            </div>
          </SelectTrigger>
          <SelectContent>
            {availableRenderers.map((renderer) => (
              <SelectItem key={renderer.name} value={renderer.name}>
                {renderer.displayName}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
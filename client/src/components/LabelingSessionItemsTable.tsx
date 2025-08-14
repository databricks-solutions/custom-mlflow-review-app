import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Edit } from "lucide-react";
import { LabelingItem, ReviewApp, LabelingSession } from "@/types/renderers";

interface LabelingSessionItemsTableProps {
  items: LabelingItem[];
  reviewApp: ReviewApp | null | undefined;
  reviewAppId: string;
  sessionId: string;
  session?: LabelingSession;
  onTraceClick?: (traceId: string) => void;
  showProgress?: boolean;
  maxHeight?: string;
  showActions?: boolean;
}

export function LabelingSessionItemsTable({
  items,
  reviewApp,
  reviewAppId,
  sessionId,
  session,
  onTraceClick,
  showProgress = true,
  maxHeight = "max-h-96",
  showActions = true,
}: LabelingSessionItemsTableProps) {
  const navigate = useNavigate();

  const completedCount = items.filter((i) => i.state === "COMPLETED").length;
  const progressPercentage = items.length > 0 ? (completedCount / items.length) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      {showProgress && items.length > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>
              {completedCount} / {items.length} completed
            </span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>
      )}

      {/* Items Table */}
      <div className={`border rounded-lg overflow-x-auto ${maxHeight}`}>
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead>Status</TableHead>
              <TableHead>Request</TableHead>
              <TableHead>Response</TableHead>
              {/* Use session-specific schemas if available, otherwise use review app schemas */}
              {(session?.labeling_schemas || reviewApp?.labeling_schemas || []).map((schema: any) => (
                <TableHead key={schema.name}>{schema.title || schema.name}</TableHead>
              ))}
              {showActions && <TableHead>Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.item_id}>
                <TableCell>
                  <Badge
                    variant={
                      item.state === "COMPLETED"
                        ? "default"
                        : item.state === "SKIPPED"
                          ? "secondary"
                          : item.state === "IN_PROGRESS"
                            ? "outline"
                            : "secondary"
                    }
                  >
                    {item.state}
                  </Badge>
                </TableCell>
                <TableCell className="max-w-xs text-xs align-top">
                  <div
                    className="text-blue-600 hover:text-blue-800 hover:underline cursor-pointer text-left overflow-hidden max-h-12"
                    onClick={() => {
                      if (item.source && 'trace_id' in item.source) {
                        onTraceClick?.(item.source.trace_id || "");
                      }
                    }}
                    style={{
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                    }}
                    title={item.request_preview || ""}
                  >
                    {item.request_preview || "-"}
                  </div>
                </TableCell>
                <TableCell className="max-w-xs text-xs align-top">
                  <div
                    className="overflow-hidden max-h-12"
                    style={{
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                    }}
                    title={item.response_preview || ""}
                  >
                    {item.response_preview || "-"}
                  </div>
                </TableCell>
                {/* Use session-specific schemas if available, otherwise use review app schemas */}
                {(session?.labeling_schemas || reviewApp?.labeling_schemas || []).map((schema: any) => {
                  const label = item.labels?.[schema.name];
                  let labelValue = "-";
                  
                  if (label !== undefined && label !== null) {
                    if (typeof label === 'object' && 'value' in label) {
                      labelValue = String(label.value);
                    } else {
                      labelValue = String(label);
                    }
                  }
                  
                  return (
                    <TableCell key={schema.name} className="max-w-xs text-sm align-top">
                      <div
                        className="overflow-hidden max-h-12"
                        style={{
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                        }}
                        title={labelValue}
                      >
                        {labelValue}
                      </div>
                    </TableCell>
                  );
                })}
                {showActions && (
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (item.source && 'trace_id' in item.source) {
                          navigate(
                            `/review-app/${reviewAppId}?session=${sessionId}&trace=${item.source.trace_id}`
                          );
                        }
                      }}
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Label
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

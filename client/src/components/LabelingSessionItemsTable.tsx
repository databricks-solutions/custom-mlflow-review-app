import { useState } from "react";
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

interface LabelingSessionItemsTableProps {
  items: any[];
  reviewApp: any;
  reviewAppId: string;
  sessionId: string;
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
  onTraceClick,
  showProgress = true,
  maxHeight = "max-h-96",
  showActions = true,
}: LabelingSessionItemsTableProps) {
  const navigate = useNavigate();

  const truncate = (text: string, maxLength: number = 100) => {
    if (!text) return "-";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  const completedCount = items.filter((i) => i.state === "COMPLETED").length;
  const inProgressCount = items.filter((i) => i.state === "IN_PROGRESS").length;
  const pendingCount = items.filter((i) => i.state === "PENDING").length;
  const skippedCount = items.filter((i) => i.state === "SKIPPED").length;
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
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Completed: {completedCount}</span>
            <span>In Progress: {inProgressCount}</span>
            <span>Pending: {pendingCount}</span>
            <span>Skipped: {skippedCount}</span>
          </div>
        </div>
      )}

      {/* Items Table */}
      <div className={`border rounded-lg overflow-x-auto ${maxHeight}`}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Status</TableHead>
              <TableHead>Request</TableHead>
              <TableHead>Response</TableHead>
              {reviewApp?.labeling_schemas?.map((schema: any) => (
                <TableHead key={schema.name}>{schema.title || schema.name}</TableHead>
              ))}
              <TableHead>Comment</TableHead>
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
                <TableCell className="max-w-xs text-xs">
                  <button
                    onClick={() => onTraceClick?.(item.source?.trace_id || "")}
                    className="text-blue-600 hover:text-blue-800 hover:underline cursor-pointer text-left truncate block w-full"
                    title={item.request_preview || ""}
                  >
                    {truncate(item.request_preview || "-")}
                  </button>
                </TableCell>
                <TableCell
                  className="max-w-xs truncate text-xs"
                  title={item.response_preview || ""}
                >
                  {truncate(item.response_preview || "-")}
                </TableCell>
                {reviewApp?.labeling_schemas?.map((schema: any) => (
                  <TableCell key={schema.name} className="text-sm">
                    {item.labels?.[schema.name] !== undefined
                      ? String(item.labels[schema.name]?.value || item.labels[schema.name])
                      : "-"}
                  </TableCell>
                ))}
                <TableCell className="max-w-xs truncate text-xs" title={item.comment || ""}>
                  {item.comment || "-"}
                </TableCell>
                {showActions && (
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigate(
                          `/review-app/${reviewAppId}?session=${sessionId}&trace=${item.source?.trace_id}`
                        );
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

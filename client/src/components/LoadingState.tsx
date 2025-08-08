import { Skeleton } from "@/components/ui/skeleton";

export function LoadingState() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <Skeleton className="h-12 w-64" />
      <div className="grid gap-4">
        <Skeleton className="h-64" />
        <Skeleton className="h-32" />
      </div>
    </div>
  );
}

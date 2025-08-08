import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, CheckCircle, XCircle } from "lucide-react";

interface NavigationButtonsProps {
  currentIndex: number;
  totalItems: number;
  isSubmitting: boolean;
  hasAssessments: boolean;
  onPrevious: () => void;
  onSkip: () => Promise<void>;
  onSubmit: () => Promise<void>;
}

/**
 * Reusable navigation buttons for item renderers
 * Provides Previous, Skip, and Submit & Next functionality
 */
export function NavigationButtons({
  currentIndex,
  totalItems,
  isSubmitting,
  hasAssessments,
  onPrevious,
  onSkip,
  onSubmit,
}: NavigationButtonsProps) {
  return (
    <div className="col-span-1 lg:col-span-2 flex items-center justify-between pt-6 border-t">
      <Button variant="outline" onClick={onPrevious} disabled={currentIndex === 0}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Previous
      </Button>

      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={onSkip} disabled={isSubmitting}>
          <XCircle className="h-4 w-4 mr-2" />
          Skip
        </Button>

        <Button onClick={onSubmit} disabled={isSubmitting || !hasAssessments}>
          <CheckCircle className="h-4 w-4 mr-2" />
          Submit & Next
        </Button>
      </div>
    </div>
  );
}

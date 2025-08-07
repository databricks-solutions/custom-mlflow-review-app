import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useUserRole } from "@/hooks/api-hooks";

interface DevModeHeaderProps {
  session?: { name: string } | null;
}

export function DevModeHeader({ session }: DevModeHeaderProps) {
  const navigate = useNavigate();
  const { data: userRole } = useUserRole();
  
  return (
    <div className="flex items-center gap-3">
      {userRole?.is_developer && (
        <Button variant="ghost" size="sm" onClick={() => navigate("/dev")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
      )}
      <h1 className="text-2xl font-bold">
        {session?.name || "Labeling Session"} - Developer Mode
      </h1>
    </div>
  );
}
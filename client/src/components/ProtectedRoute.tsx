import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useUserRole } from "@/hooks/api-hooks";
import { Skeleton } from "@/components/ui/skeleton";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireDeveloper?: boolean;
}

export function ProtectedRoute({ children, requireDeveloper = false }: ProtectedRouteProps) {
  const navigate = useNavigate();
  const { data: userRole, isLoading, error } = useUserRole();

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !userRole) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <CardTitle className="text-red-900">Authentication Error</CardTitle>
            </div>
            <CardDescription className="text-red-700">
              Unable to verify your permissions. Please try logging in again.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
              className="border-red-300 text-red-700 hover:bg-red-100"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (requireDeveloper && !userRole.is_developer) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-600" />
              <CardTitle className="text-orange-900">Access Denied</CardTitle>
            </div>
            <CardDescription className="text-orange-700">
              Developer role required to access this page. You are currently logged in as an SME
              (Subject Matter Expert).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-orange-800">
              This page is restricted to developers who can manage labeling sessions and configure
              the review app. If you believe you should have access, contact your system
              administrator.
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={() => navigate("/")}
                className="border-orange-300 text-orange-700 hover:bg-orange-100"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}

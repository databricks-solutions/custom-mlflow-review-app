import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function NoSessionSelected() {
  return (
    <div className="container mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>No Session Selected</CardTitle>
          <CardDescription>Please select a labeling session from the main page.</CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}

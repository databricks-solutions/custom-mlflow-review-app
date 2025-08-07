import React from "react";
import { Button } from "@/components/ui/button";
import { Tag } from "lucide-react";

interface SchemaButtonProps {
  schema: {
    name: string;
    title?: string;
  };
  onClick: (schemaName: string) => void;
  size?: "sm" | "default" | "lg";
  className?: string;
}

export function SchemaButton({ schema, onClick, size = "sm", className = "" }: SchemaButtonProps) {
  return (
    <Button
      variant="outline"
      size={size}
      className={`h-6 px-2 text-xs font-normal gap-1 ${className}`}
      onClick={() => onClick(schema.name)}
    >
      <Tag className="h-3 w-3" />
      {schema.title || schema.name}
    </Button>
  );
}
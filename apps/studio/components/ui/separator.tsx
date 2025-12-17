import * as React from "react";
import { cn } from "@/lib/utils";

function Separator({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("shrink-0 bg-gray-200 h-px w-full", className)} {...props} />;
}

export { Separator };

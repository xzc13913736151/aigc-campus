import { cn } from "@/lib/utils";


export function List({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("space-y-4", className)}>{children}</div>;
}

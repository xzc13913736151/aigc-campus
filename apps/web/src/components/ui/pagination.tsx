import { Button } from "@/components/ui/button";


export function Pagination() {
  return (
    <div className="flex items-center justify-between gap-3">
      <Button variant="ghost" size="sm" disabled>
        Previous
      </Button>
      <span className="text-sm text-slate-500">Page 1 of 1</span>
      <Button variant="ghost" size="sm" disabled>
        Next
      </Button>
    </div>
  );
}

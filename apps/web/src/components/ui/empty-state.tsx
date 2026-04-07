import { Card } from "@/components/ui/card";


export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <Card className="border-dashed bg-white/70 text-center">
      <div className="space-y-2 py-6">
        <h3 className="text-lg font-semibold text-ink">{title}</h3>
        <p className="mx-auto max-w-md text-sm leading-6 text-slate-500">{description}</p>
      </div>
    </Card>
  );
}

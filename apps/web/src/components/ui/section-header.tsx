export function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{eyebrow}</p>
      <h2 className="font-serif text-3xl text-ink md:text-4xl">{title}</h2>
      <p className="max-w-2xl text-sm leading-7 text-slate-600 md:text-base">{description}</p>
    </div>
  );
}

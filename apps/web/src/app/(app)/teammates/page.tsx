import { SectionHeader } from "@/components/ui/section-header";
import { TeammateBoard } from "@/features/teammates/teammate-board";


export default function TeammatesPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        eyebrow="Teammates"
        title="队友匹配广场"
        description="首版优先打通发帖、浏览和后台可见。更复杂的排序和擦亮规则后续再叠。"
      />
      <TeammateBoard />
    </div>
  );
}

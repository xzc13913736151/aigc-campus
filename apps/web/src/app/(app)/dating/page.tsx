import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";


const candidates = [
  { name: "晨曦", tags: ["阅读", "羽毛球", "INTJ"], score: 88 },
  { name: "言舟", tags: ["摄影", "保研", "ENFP"], score: 82 },
  { name: "松野", tags: ["电影", "夜跑", "INFJ"], score: 79 },
];


export default function DatingPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        eyebrow="Dating"
        title="恋爱交流模块"
        description="首版页面先展示候选人和匹配方向。真实推荐接口、双向匹配聊天、举报拉黑规则已在后端留出扩展位。"
      />
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card className="bg-white/85">
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-ink">当前待补完</h2>
            <ul className="space-y-3 text-sm leading-7 text-slate-600">
              <li>恋爱档案编辑页后续可直接对接后端 `/dating/profile/`。</li>
              <li>择偶偏好页后续可直接对接后端 `/dating/preferences/`。</li>
              <li>喜欢 / 无兴趣已由后端 `/dating/signals/` 预留。</li>
              <li>双向感兴趣后的聊天入口由 Channels 预埋，未在本轮前端做完。</li>
            </ul>
          </div>
        </Card>
        <div className="grid gap-4">
          {candidates.map((candidate) => (
            <Card key={candidate.name} className="bg-shell">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-3">
                  <h3 className="text-2xl font-semibold text-ink">{candidate.name}</h3>
                  <div className="flex flex-wrap gap-2">
                    {candidate.tags.map((tag) => (
                      <span key={tag} className="rounded-full bg-canvas px-3 py-1 text-xs font-medium text-ink">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-shell">匹配度 {candidate.score}</div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

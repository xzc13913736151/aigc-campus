import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";


const samplePosts = [
  { title: "2027 保研时间线互助帖", category: "保研", body: "整理夏令营、预推免和材料准备的节点。" },
  { title: "考研数学复习搭子招募", category: "考研", body: "希望找能坚持打卡和周总结的同学。" },
  { title: "考公岗位选择经验", category: "考公", body: "分享岗位筛选方法和信息差避坑。" },
];


export default function ForumPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        eyebrow="Forum"
        title="论坛模块"
        description="这里先给出论坛首页骨架，后端已经预留帖子、评论、点赞和搜索接口，后续可以继续把发帖和详情页补成完整功能。"
      />
      <div className="grid gap-4">
        {samplePosts.map((post) => (
          <Card key={post.title} className="bg-white/85">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-2xl font-semibold text-ink">{post.title}</h2>
                <span className="rounded-full bg-canvas px-3 py-1 text-xs font-semibold text-coral">{post.category}</span>
              </div>
              <p className="text-sm leading-7 text-slate-600">{post.body}</p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

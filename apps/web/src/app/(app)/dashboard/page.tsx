import Link from "next/link";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";


const cards = [
  {
    title: "个人资料",
    description: "编辑个人信息、兴趣标签和一句话介绍，为后续匹配与论坛发言提供基础资料。",
    href: "/profile",
  },
  {
    title: "队友匹配",
    description: "发布组队帖、管理申请、为“找队友”主流程提供第一条真实业务链路。",
    href: "/teammates",
  },
  {
    title: "恋爱交流",
    description: "查看恋爱档案、偏好和候选人入口，实时聊天部分只做了后端预埋。",
    href: "/dating",
  },
  {
    title: "论坛",
    description: "为保研、考研、考公等讨论预留帖子、评论和点赞页面入口。",
    href: "/forum",
  },
];


export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        eyebrow="Control Center"
        title="MVP 控制台"
        description="当前骨架优先保证路由、组件和核心表单可用。你可以从这里进入资料、组队、恋爱和论坛四条入口。"
      />

      <div className="grid gap-6 md:grid-cols-2">
        {cards.map((card) => (
          <Card key={card.href} className="flex h-full flex-col justify-between gap-5 bg-white/85">
            <div className="space-y-3">
              <h2 className="text-2xl font-semibold text-ink">{card.title}</h2>
              <p className="text-sm leading-7 text-slate-600">{card.description}</p>
            </div>
            <Link href={card.href} className={buttonVariants({ variant: "secondary" })}>
              进入 {card.title}
            </Link>
          </Card>
        ))}
      </div>

      <Card className="bg-ink text-shell">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="font-serif text-3xl">后台管理入口</h2>
            <p className="mt-2 text-sm leading-7 text-white/75">Django Admin 是首版审核、删帖、举报处理和数据可视化的主入口。</p>
          </div>
          <Link href="/admin" className={buttonVariants({ variant: "secondary", size: "lg" })}>
            打开后台入口页
          </Link>
        </div>
      </Card>
    </div>
  );
}

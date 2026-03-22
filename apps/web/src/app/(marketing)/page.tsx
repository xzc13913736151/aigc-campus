import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";


const modules = [
  {
    title: "恋爱交流",
    description: "建立完整档案、设置偏好、表达兴趣，并为双向匹配预留受限聊天入口。",
  },
  {
    title: "队友匹配",
    description: "发布组队帖、筛选队伍、申请加入，首版重点打通一次真实找队友流程。",
  },
  {
    title: "论坛",
    description: "围绕保研、考研、考公等主题发帖、评论、点赞和搜索，管理员可在后台审核。",
  },
];


export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-12 md:px-6 md:py-20">
      <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <div className="space-y-8">
          <p className="inline-flex rounded-full bg-white/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-coral">
            Campus Relationship OS
          </p>
          <div className="space-y-5">
            <h1 className="max-w-3xl font-serif text-5xl leading-tight text-ink md:text-7xl">
              把校园里的找对象、找队友和经验交流收进同一个协作平台。
            </h1>
            <p className="max-w-2xl text-base leading-8 text-slate-600 md:text-lg">
              PairUp 的首版目标不是把所有功能一次做满，而是尽快跑通注册、资料编辑、模块入口和一次真实行为闭环，让后台能够看到数据、团队能够继续迭代。
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <Link href="/register" className={buttonVariants({ variant: "secondary", size: "lg" })}>
              开始注册
            </Link>
            <Link href="/dashboard" className={buttonVariants({ variant: "ghost", size: "lg", className: "border border-line" })}>
              查看 MVP 入口
            </Link>
          </div>
        </div>

        <Card className="overflow-hidden bg-ink text-shell">
          <div className="space-y-8">
            <SectionHeader
              eyebrow="MVP Scope"
              title="第一轮先把主链路跑通"
              description="从首页到注册、资料、模块入口，再到一次找队友发帖和后台可见，这是当前脚手架明确覆盖的路径。"
            />
            <div className="grid gap-3">
              {["访问首页", "注册 / 登录", "编辑资料", "进入模块", "发起一次行为", "后台可见"].map((step, index) => (
                <div key={step} className="flex items-center gap-4 rounded-3xl border border-white/10 bg-white/5 px-4 py-4">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-coral text-sm font-semibold text-white">
                    {index + 1}
                  </span>
                  <span className="text-sm text-white/85">{step}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </section>

      <section className="mt-20 space-y-8">
        <SectionHeader eyebrow="Modules" title="三大业务入口" description="按产品文档收敛到三个用户价值最清晰的模块，同时保留 Django Admin 作为首版后台。" />
        <div className="grid gap-6 lg:grid-cols-3">
          {modules.map((module, index) => (
            <Card key={module.title} className="bg-white/85">
              <div className="space-y-4">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-canvas text-lg font-semibold text-coral">
                  0{index + 1}
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-semibold text-ink">{module.title}</h2>
                  <p className="text-sm leading-7 text-slate-600">{module.description}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}

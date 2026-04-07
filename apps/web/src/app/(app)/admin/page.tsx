import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { getAdminUrl } from "@/lib/api";


export default function AdminEntryPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        eyebrow="Admin"
        title="管理后台入口"
        description="首版不单独开发自定义运营后台，而是使用 Django Admin 处理用户、资料、帖子、举报和屏蔽关系。"
      />
      <Card className="space-y-4 bg-white/85">
        <p className="text-sm leading-7 text-slate-600">
          当 API 运行在本地默认地址时，点击下面的链接会进入 Django Admin。需要先执行 `createsuperuser`。
        </p>
        <Link href={getAdminUrl()} className={buttonVariants({ variant: "secondary", size: "lg" })}>
          打开 Django Admin
        </Link>
      </Card>
    </div>
  );
}

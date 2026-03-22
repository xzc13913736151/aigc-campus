"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Button, buttonVariants } from "@/components/ui/button";
import { clearAuthTokens } from "@/lib/api";
import { cn } from "@/lib/utils";


const links = [
  { href: "/dashboard", label: "控制台" },
  { href: "/profile", label: "个人资料" },
  { href: "/teammates", label: "队友匹配" },
  { href: "/dating", label: "恋爱交流" },
  { href: "/forum", label: "论坛" },
  { href: "/admin", label: "后台入口" },
];


export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-canvas/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-coral text-lg font-semibold text-white">P</span>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-500">PairUp</p>
            <p className="text-base font-semibold text-ink">校园关系与协作平台</p>
          </div>
        </Link>

        <nav className="hidden items-center gap-2 lg:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-full px-4 py-2 text-sm text-slate-600 transition hover:bg-white hover:text-ink",
                pathname === link.href && "bg-white text-ink shadow-sm",
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Link href="/login" className={buttonVariants({ variant: "ghost", size: "sm" })}>
            登录
          </Link>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              clearAuthTokens();
              router.push("/login");
            }}
          >
            退出
          </Button>
        </div>
      </div>
    </header>
  );
}

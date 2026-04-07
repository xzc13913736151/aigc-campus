import type { Metadata } from "next";

import { Providers } from "@/lib/providers";

import "./globals.css";


export const metadata: Metadata = {
  title: "PairUp",
  description: "校园关系与协作平台",
};


export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

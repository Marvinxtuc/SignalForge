import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppShell } from "../components/layout/AppShell";
import "./styles.css";

export const metadata: Metadata = {
  title: "SignalForge",
  description: "SignalForge 研究工作台"
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

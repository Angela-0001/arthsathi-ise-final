import type { Metadata } from "next";
import "./globals.css";
import BottomNav from "@/components/BottomNav";

export const metadata: Metadata = {
  title: "ArthSathi — Financial Companion",
  description: "AI-powered multilingual financial guidance for every Indian",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="hi">
      <body className="bg-slate-50 text-slate-900 min-h-screen pb-20 antialiased">
        {children}
        <BottomNav />
      </body>
    </html>
  );
}

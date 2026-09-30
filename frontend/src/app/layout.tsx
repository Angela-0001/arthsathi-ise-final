import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import BottomNav from "@/components/BottomNav";

export const metadata: Metadata = {
  title: "ArthSathi — Financial Companion",
  description: "AI-powered multilingual financial guidance for every Indian",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="hi">
      <body className="bg-slate-50 text-slate-900 min-h-screen antialiased">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 md:ml-56 pb-20 md:pb-0 min-h-screen overflow-x-hidden">
            {children}
          </main>
        </div>
        <BottomNav />
      </body>
    </html>
  );
}

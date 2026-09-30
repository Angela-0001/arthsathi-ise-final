"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/",         label: "Home",     icon: "🏠" },
  { href: "/schemes",  label: "Schemes",  icon: "📋" },
  { href: "/document", label: "Document", icon: "🔍" },
  { href: "/roadmap",  label: "Roadmap",  icon: "🗺️" },
  { href: "/profile",  label: "Profile",  icon: "👤" },
];

export default function BottomNav() {
  const pathname = usePathname();
  if (pathname === "/login") return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 shadow-lg flex z-50">
      {links.map(({ href, label, icon }) => {
        const active = pathname === href;
        return (
          <Link key={href} href={href}
            className={`flex flex-col items-center justify-center flex-1 py-2 gap-0.5 text-xs transition-colors ${
              active
                ? "text-blue-600 font-semibold"
                : "text-slate-400 hover:text-slate-600"
            }`}>
            <span className="text-xl leading-none">{icon}</span>
            <span className="text-[10px] font-medium">{label}</span>
            {active && <span className="absolute bottom-0 w-8 h-0.5 bg-blue-600 rounded-t-full" />}
          </Link>
        );
      })}
    </nav>
  );
}

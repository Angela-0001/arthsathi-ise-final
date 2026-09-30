"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

const features = [
  {
    href: "/schemes",
    title: "Government Schemes",
    subtitle: "सरकारी योजनाएँ",
    desc: "Discover welfare schemes you qualify for based on your income, occupation, and state.",
    icon: "📋",
    color: "bg-blue-50 border-blue-200 text-blue-700",
    btn: "bg-blue-600 hover:bg-blue-700",
  },
  {
    href: "/document",
    title: "Document Analysis",
    subtitle: "दस्तावेज़ जाँच",
    desc: "Upload any loan or contract document. We flag risky clauses before you sign.",
    icon: "🔍",
    color: "bg-red-50 border-red-200 text-red-700",
    btn: "bg-red-500 hover:bg-red-600",
  },
  {
    href: "/roadmap",
    title: "Financial Roadmap",
    subtitle: "वित्तीय रोडमैप",
    desc: "A step-by-step personalised plan to build savings, clear debt, and grow.",
    icon: "🗺️",
    color: "bg-indigo-50 border-indigo-200 text-indigo-700",
    btn: "bg-indigo-600 hover:bg-indigo-700",
  },
  {
    href: "/profile",
    title: "Your Profile",
    subtitle: "मेरी प्रोफ़ाइल",
    desc: "Set your income, state, and occupation to get personalised recommendations.",
    icon: "👤",
    color: "bg-slate-50 border-slate-200 text-slate-700",
    btn: "bg-slate-600 hover:bg-slate-700",
  },
];

export default function Home() {
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(!!localStorage.getItem("arthsathi_token"));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 shadow-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm">A</div>
            <span className="font-bold text-slate-900 text-lg">ArthSathi</span>
          </div>
          <div className="flex items-center gap-3">
            {loggedIn ? (
              <Link href="/profile" className="text-sm font-medium text-blue-600 hover:text-blue-700">My Profile</Link>
            ) : (
              <Link href="/login" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors">Sign In</Link>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            AI-Powered · Multilingual · Offline-First
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 leading-tight mb-4">
            Financial guidance<br />
            <span className="text-blue-600">for every Indian</span>
          </h1>
          <p className="text-slate-500 text-lg max-w-xl mx-auto leading-relaxed mb-8">
            Scheme matching, document risk detection, and financial planning — in Hindi, Marathi, and English.
          </p>
          <div className="flex gap-3 justify-center">
            <Link href={loggedIn ? "/schemes" : "/login"}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold text-sm transition-colors shadow-sm">
              {loggedIn ? "View My Schemes" : "Get Started"}
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
            <Link href="/profile"
              className="inline-flex items-center gap-2 bg-white border border-slate-200 hover:border-blue-300 text-slate-700 hover:text-blue-600 px-6 py-3 rounded-xl font-semibold text-sm transition-colors shadow-sm">
              Set Up Profile
            </Link>
          </div>
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {features.map((f) => (
            <Link key={f.href} href={f.href}
              className={`card-hover group flex flex-col gap-4 border ${f.color}`}>
              <div className="flex items-center gap-3">
                <span className="text-2xl">{f.icon}</span>
                <div>
                  <p className="font-bold text-slate-900 text-base leading-tight">{f.title}</p>
                  <p className="text-xs text-slate-500">{f.subtitle}</p>
                </div>
              </div>
              <p className="text-slate-600 text-sm leading-relaxed flex-1">{f.desc}</p>
              <div className="flex items-center gap-1 text-sm font-semibold text-blue-600 group-hover:gap-2 transition-all">
                Open
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          ))}
        </div>

        {/* Channels strip */}
        <div className="mt-12 text-center text-xs text-slate-400 space-y-1">
          <p>Available on: Web · Telegram · WhatsApp · IVR (Voice Call)</p>
          <p>Languages: हिंदी · मराठी · English</p>
        </div>
      </div>
    </div>
  );
}

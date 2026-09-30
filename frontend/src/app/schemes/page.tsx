"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Scheme {
  scheme_id: string;
  name: string;
  translated_name: string;
  translated_description: string;
  benefit_value: number | null;
  application_url: string | null;
  ministry: string | null;
  category: string | null;
}

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/schemes/match?lang=en")
      .then(r => setSchemes(r.data))
      .catch(() => setError("Could not load schemes. Make sure you are logged in."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white text-lg">📋</div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Eligible Schemes</h1>
          <p className="text-slate-500 text-sm">आपके लिए योजनाएँ — based on your profile</p>
        </div>
      </div>

      {loading && (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-slate-100 rounded w-1/3 mb-3" />
              <div className="h-3 bg-slate-100 rounded w-full mb-2" />
              <div className="h-3 bg-slate-100 rounded w-2/3" />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="card border-red-200 bg-red-50 text-red-600 text-sm flex items-center gap-2">
          <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}

      {!loading && !error && schemes.length === 0 && (
        <div className="card text-center py-14">
          <div className="text-4xl mb-3">📭</div>
          <p className="font-semibold text-slate-800 mb-1">No schemes found yet</p>
          <p className="text-slate-500 text-sm">Complete your profile to see eligible schemes.</p>
        </div>
      )}

      <div className="space-y-4">
        {schemes.map((s) => (
          <div key={s.scheme_id} className="card hover:shadow-card-hover hover:border-blue-200 transition-all">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap gap-2 mb-2">
                  {s.category && (
                    <span className="badge badge-blue">{s.category}</span>
                  )}
                  {s.ministry && (
                    <span className="badge badge-slate">{s.ministry}</span>
                  )}
                </div>
                <h2 className="font-bold text-slate-900 text-base mb-1">
                  {s.translated_name || s.name}
                </h2>
                <p className="text-slate-500 text-sm leading-relaxed line-clamp-2">
                  {s.translated_description}
                </p>
              </div>
              {s.benefit_value && (
                <div className="shrink-0 bg-green-50 border border-green-200 rounded-xl px-3 py-2 text-right">
                  <p className="text-xs text-green-600 font-medium">Benefit</p>
                  <p className="text-green-700 font-bold text-lg">₹{s.benefit_value.toLocaleString("en-IN")}</p>
                </div>
              )}
            </div>
            {s.application_url && (
              <div className="mt-4 pt-4 border-t border-slate-100">
                <a href={s.application_url} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:text-blue-700 transition-colors">
                  Apply on myScheme
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

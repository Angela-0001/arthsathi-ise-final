"use client";
import { useState, useRef } from "react";
import { api } from "@/lib/api";

interface RiskClause { clause_text: string; risk_level: string; explanation: string; }
interface AnalysisResult { summary: string; risk_flags: RiskClause[]; verified: boolean; }

export default function DocumentPage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await api.post("/documents/analyze?lang=en", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(r.data);
    } catch { setError("Analysis failed. Please try a clearer image or different file."); }
    finally { setLoading(false); }
  }

  const high = result?.risk_flags.filter(f => f.risk_level === "high").length ?? 0;
  const medium = result?.risk_flags.filter(f => f.risk_level === "medium").length ?? 0;
  const low = result?.risk_flags.filter(f => f.risk_level === "low").length ?? 0;
  const total = high + medium + low;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-red-500 flex items-center justify-center text-white text-lg">🔍</div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Document Analysis</h1>
          <p className="text-slate-500 text-sm">दस्तावेज़ जाँच — Upload to detect risky clauses</p>
        </div>
      </div>

      {/* Upload */}
      <div className="card mb-6">
        <form onSubmit={handleUpload} className="space-y-4">
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-xl p-10 text-center cursor-pointer transition-colors group"
          >
            <div className="text-4xl mb-3">📄</div>
            <p className="font-semibold text-slate-700 text-sm group-hover:text-blue-600 transition-colors">
              {fileName || "Click to upload document"}
            </p>
            <p className="text-slate-400 text-xs mt-1">Image (JPG/PNG), PDF, or Word (.docx)</p>
            <input ref={fileRef} type="file" accept="image/*,.pdf,.docx"
              className="hidden"
              onChange={e => setFileName(e.target.files?.[0]?.name || "")}
              aria-label="Select document" />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button type="submit" disabled={loading || !fileName} className="btn-primary">
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Analyzing...
              </span>
            ) : "Analyze Document"}
          </button>
        </form>
      </div>

      {result && (
        <div className="space-y-5">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="stat-card text-center">
              <p className="text-3xl font-bold text-red-500">{high}</p>
              <p className="text-xs text-slate-500 mt-1 font-medium">High Risk</p>
            </div>
            <div className="stat-card text-center">
              <p className="text-3xl font-bold text-amber-500">{medium}</p>
              <p className="text-xs text-slate-500 mt-1 font-medium">Medium Risk</p>
            </div>
            <div className="stat-card text-center">
              <p className="text-3xl font-bold text-blue-500">{low}</p>
              <p className="text-xs text-slate-500 mt-1 font-medium">Low Risk</p>
            </div>
          </div>

          {/* Summary */}
          <div className={`card ${total === 0 ? "border-green-200 bg-green-50" : "border-amber-200 bg-amber-50"}`}>
            <div className="flex items-start gap-3">
              <span className="text-2xl">{total === 0 ? "✅" : "⚠️"}</span>
              <div>
                <p className={`font-semibold mb-1 ${total === 0 ? "text-green-800" : "text-amber-800"}`}>
                  {total === 0 ? "No risky clauses detected" : `${total} risk clause(s) found`}
                </p>
                <p className={`text-sm leading-relaxed ${total === 0 ? "text-green-700" : "text-amber-700"}`}>
                  {result.summary}
                </p>
              </div>
            </div>
          </div>

          {/* Flags */}
          {result.risk_flags.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Detected Clauses</h3>
              {result.risk_flags.map((flag, i) => (
                <div key={i} className={
                  flag.risk_level === "high" ? "risk-high" :
                  flag.risk_level === "medium" ? "risk-medium" : "risk-low"
                }>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className={`badge ${flag.risk_level === "high" ? "badge-red" : flag.risk_level === "medium" ? "badge-amber" : "badge-blue"}`}>
                      {flag.risk_level.toUpperCase()} RISK
                    </span>
                  </div>
                  <p className="text-xs font-mono text-slate-600 mb-1">{flag.clause_text}</p>
                  <p className="text-sm text-slate-700">{flag.explanation}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

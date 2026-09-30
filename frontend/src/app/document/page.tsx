"use client";
import { useState, useRef } from "react";
import { api } from "@/lib/api";

interface RiskClause { clause_text: string; risk_level: string; explanation: string; }
interface AnalysisResult { summary: string; risk_flags: RiskClause[]; verified: boolean; }

const RISK_CONFIG: Record<string, { label: string; cls: string; badge: string; dot: string }> = {
  high:   { label: "HIGH RISK",   cls: "risk-high",   badge: "badge-red",   dot: "bg-red-500" },
  medium: { label: "MEDIUM RISK", cls: "risk-medium", badge: "badge-amber",  dot: "bg-amber-500" },
  low:    { label: "LOW RISK",    cls: "risk-low",    badge: "badge-blue",  dot: "bg-blue-500" },
};

export default function DocumentPage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function analyze(file: File) {
    setLoading(true); setError(""); setResult(null);
    setFileName(file.name);
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await api.post("/documents/analyze?lang=en", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(r.data);
    } catch {
      setError("Analysis failed. Please try a clearer image or a different file.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (file) analyze(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) analyze(file);
  }

  const high   = result?.risk_flags.filter(f => f.risk_level === "high").length ?? 0;
  const medium = result?.risk_flags.filter(f => f.risk_level === "medium").length ?? 0;
  const low    = result?.risk_flags.filter(f => f.risk_level === "low").length ?? 0;
  const total  = high + medium + low;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Document Analysis</h1>
        <p className="text-slate-500 text-sm mt-1">दस्तावेज़ जाँच — Upload any loan, land, or insurance document to detect risky clauses</p>
      </div>

      {/* Upload zone */}
      <div className="card mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            onClick={() => fileRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
              dragOver ? "border-blue-400 bg-blue-50" : "border-slate-200 hover:border-blue-300 hover:bg-slate-50"
            }`}
          >
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="font-semibold text-slate-700 text-sm">
              {fileName ? fileName : "Click to upload or drag & drop"}
            </p>
            <p className="text-slate-400 text-xs mt-1">Supports: JPG, PNG, PDF, Word (.docx)</p>
            <input ref={fileRef} type="file" accept="image/*,.pdf,.docx" className="hidden"
              onChange={e => { const f = e.target.files?.[0]; if (f) setFileName(f.name); }}
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
                Analyzing document...
              </span>
            ) : "Analyze Document"}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-5">
          {/* Risk stats */}
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

          {/* Summary card */}
          <div className={`card ${total === 0 ? "border-green-200 bg-green-50" : high > 0 ? "border-red-200 bg-red-50" : "border-amber-200 bg-amber-50"}`}>
            <div className="flex items-start gap-3">
              <span className="text-2xl mt-0.5">{total === 0 ? "✅" : high > 0 ? "🚨" : "⚠️"}</span>
              <div>
                <p className={`font-bold text-base mb-1 ${total === 0 ? "text-green-800" : high > 0 ? "text-red-800" : "text-amber-800"}`}>
                  {total === 0 ? "No risky clauses detected" : `${total} risk clause${total > 1 ? "s" : ""} found`}
                </p>
                <p className={`text-sm leading-relaxed ${total === 0 ? "text-green-700" : high > 0 ? "text-red-700" : "text-amber-700"}`}>
                  {result.summary}
                </p>
                {result.verified && (
                  <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Self-verified — all flags confirmed in source text
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Risk flags */}
          {result.risk_flags.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Detected Clauses</h3>
              <div className="space-y-3">
                {result.risk_flags.map((flag, i) => {
                  const cfg = RISK_CONFIG[flag.risk_level] ?? RISK_CONFIG.low;
                  return (
                    <div key={i} className={cfg.cls}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                        <span className={`badge ${cfg.badge} text-xs`}>{cfg.label}</span>
                      </div>
                      {flag.clause_text && (
                        <p className="text-xs font-mono text-slate-500 mb-1 bg-white/60 rounded px-2 py-1">
                          "{flag.clause_text}"
                        </p>
                      )}
                      <p className="text-sm text-slate-700 font-medium">{flag.explanation}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Advice footer */}
          {total > 0 && (
            <div className="card bg-slate-50 border-slate-200">
              <p className="text-xs text-slate-600 leading-relaxed">
                <strong>What to do:</strong> Do not sign this document until you fully understand every flagged clause.
                Consider consulting a legal aid centre or a trusted person before proceeding.
                You can also use the <strong>Telegram</strong> or <strong>WhatsApp</strong> bot to analyze documents on your mobile.
              </p>
            </div>
          )}
        </div>
      )}

    </div>
  );
}

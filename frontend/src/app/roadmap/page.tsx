"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Step { priority: number; action: string; reason: string; amount: number | null; }
interface Roadmap { monthly_income: number; total_debt: number; steps: Step[]; summary: string; }

const STEP_STYLES = [
  { border: "border-blue-400", bg: "bg-blue-50", num: "bg-blue-600 text-white", amount: "text-blue-600" },
  { border: "border-red-400",  bg: "bg-red-50",  num: "bg-red-500 text-white",  amount: "text-red-500" },
  { border: "border-amber-400",bg: "bg-amber-50",num: "bg-amber-500 text-white",amount: "text-amber-600" },
  { border: "border-indigo-400",bg:"bg-indigo-50",num:"bg-indigo-600 text-white",amount:"text-indigo-600"},
  { border: "border-green-400",bg: "bg-green-50",num: "bg-green-600 text-white",amount: "text-green-600"},
];

export default function RoadmapPage() {
  const [data, setData] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/roadmap/")
      .then(r => setData(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
      {[...Array(4)].map((_, i) => <div key={i} className="card h-20 animate-pulse" />)}
    </div>
  );

  if (!data) return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="card border-red-200 bg-red-50 text-red-600 text-sm">
        Could not load roadmap. Please complete your profile first.
      </div>
    </div>
  );

  const debtRatio = data.monthly_income > 0
    ? Math.min((data.total_debt / (data.monthly_income * 12)) * 100, 100) : 0;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white text-lg">🗺️</div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Financial Roadmap</h1>
          <p className="text-slate-500 text-sm">वित्तीय रोडमैप — Your personalised action plan</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="stat-card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Monthly Income</p>
          <p className="text-2xl font-bold text-blue-600">₹{data.monthly_income.toLocaleString("en-IN")}</p>
        </div>
        <div className="stat-card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Total Debt</p>
          <p className="text-2xl font-bold text-red-500">₹{data.total_debt.toLocaleString("en-IN")}</p>
        </div>
      </div>

      {/* Debt ratio bar */}
      {data.total_debt > 0 && (
        <div className="card mb-6">
          <div className="flex justify-between text-xs text-slate-500 mb-2">
            <span>Debt-to-Annual-Income Ratio</span>
            <span className="font-semibold">{debtRatio.toFixed(1)}%</span>
          </div>
          <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${debtRatio > 50 ? "bg-red-500" : debtRatio > 25 ? "bg-amber-500" : "bg-blue-500"}`}
              style={{ width: `${debtRatio}%` }}
            />
          </div>
        </div>
      )}

      <p className="text-slate-600 text-sm leading-relaxed mb-6 card">{data.summary}</p>

      <div className="space-y-4">
        {data.steps.map((step, idx) => {
          const s = STEP_STYLES[idx % STEP_STYLES.length];
          return (
            <div key={step.priority} className={`rounded-2xl border ${s.border} ${s.bg} p-5 flex items-start gap-4`}>
              <div className={`w-9 h-9 rounded-full ${s.num} flex items-center justify-center font-bold text-sm shrink-0`}>
                {step.priority}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-bold text-slate-900 text-sm mb-1">{step.action}</p>
                <p className="text-slate-500 text-xs leading-relaxed">{step.reason}</p>
                {step.amount != null && (
                  <p className={`text-base font-bold mt-2 ${s.amount}`}>₹{step.amount.toLocaleString("en-IN")}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

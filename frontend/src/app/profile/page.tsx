"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const OCCUPATIONS = ["farmer","daily_wage_worker","small_trader","domestic_worker","construction_worker","self_employed","salaried_employee","weaver","fisherman"];
const STATES = ["Andhra Pradesh","Bihar","Gujarat","Haryana","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Odisha","Punjab","Rajasthan","Tamil Nadu","Telangana","Uttar Pradesh","West Bengal"];
const LANGUAGES = [{ code: "hi", label: "हिंदी (Hindi)" },{ code: "mr", label: "मराठी (Marathi)" },{ code: "en", label: "English" }];

export default function ProfilePage() {
  const router = useRouter();
  const [form, setForm] = useState({ full_name:"", preferred_language:"hi", monthly_income:"", occupation:"", state:"", age:"" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get("/profile/")
      .then(r => {
        const d = r.data;
        setForm({ full_name: d.full_name||"", preferred_language: d.preferred_language||"hi", monthly_income: d.monthly_income?String(d.monthly_income):"", occupation: d.occupation||"", state: d.state||"", age: d.age?String(d.age):"" });
      })
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch("/profile/", {
        full_name: form.full_name || null,
        preferred_language: form.preferred_language,
        monthly_income: form.monthly_income ? parseFloat(form.monthly_income) : null,
        occupation: form.occupation || null,
        state: form.state || null,
        age: form.age ? parseInt(form.age) : null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } finally { setSaving(false); }
  }

  if (loading) return <div className="max-w-2xl mx-auto px-4 py-8"><div className="card h-64 animate-pulse" /></div>;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-slate-700 flex items-center justify-center text-white text-lg">👤</div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Profile</h1>
          <p className="text-slate-500 text-sm">मेरी प्रोफ़ाइल — Your details power the recommendations</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        <div className="card space-y-4">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">Personal Information</h2>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Full Name</label>
            <input type="text" value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})}
              placeholder="Your name" className="input-field" aria-label="Full name" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Age</label>
              <input type="number" value={form.age} onChange={e => setForm({...form, age: e.target.value})}
                placeholder="25" min="10" max="100" className="input-field" aria-label="Age" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Language</label>
              <select value={form.preferred_language} onChange={e => setForm({...form, preferred_language: e.target.value})}
                className="input-field" aria-label="Language">
                {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="card space-y-4">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">Financial Details</h2>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Monthly Income (₹)</label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-medium">₹</span>
              <input type="number" value={form.monthly_income} onChange={e => setForm({...form, monthly_income: e.target.value})}
                placeholder="15000" className="input-field pl-8" aria-label="Monthly income" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Occupation</label>
            <select value={form.occupation} onChange={e => setForm({...form, occupation: e.target.value})}
              className="input-field" aria-label="Occupation">
              <option value="">Select occupation</option>
              {OCCUPATIONS.map(o => <option key={o} value={o}>{o.replace(/_/g," ").replace(/\b\w/g, c => c.toUpperCase())}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">State</label>
            <select value={form.state} onChange={e => setForm({...form, state: e.target.value})}
              className="input-field" aria-label="State">
              <option value="">Select state</option>
              {STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <button type="submit" disabled={saving} className="btn-primary">
          {saving ? "Saving..." : saved ? "✓ Saved!" : "Save Profile"}
        </button>
      </form>

      <div className="mt-6 pt-4 border-t border-slate-100">
        <button onClick={() => { localStorage.removeItem("arthsathi_token"); router.push("/login"); }}
          className="text-slate-400 hover:text-red-500 text-sm transition-colors flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Sign out
        </button>
      </div>
    </div>
  );
}

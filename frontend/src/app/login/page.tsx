"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendOtp(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const r = await api.post("/auth/send-otp", { phone });
      if (r.data.dev_otp) setOtp(r.data.dev_otp);
      setStep("otp");
    } catch { setError("Could not send OTP. Check the number and try again."); }
    finally { setLoading(false); }
  }

  async function verifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const r = await api.post("/auth/verify-otp", { phone, otp });
      localStorage.setItem("arthsathi_token", r.data.access_token);
      router.push("/");
    } catch { setError("Invalid OTP. Please try again."); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white font-bold text-xl mx-auto mb-3">A</div>
          <h1 className="text-2xl font-bold text-slate-900">ArthSathi</h1>
          <p className="text-slate-500 text-sm mt-1">Your Financial Companion</p>
        </div>

        <div className="bg-white rounded-2xl shadow-card border border-slate-100 p-8">
          <h2 className="text-xl font-bold text-slate-900 mb-1">
            {step === "phone" ? "Sign In" : "Enter OTP"}
          </h2>
          <p className="text-slate-500 text-sm mb-6">
            {step === "phone" ? "Enter your mobile number to continue" : `OTP sent to +91 ${phone}`}
          </p>

          {step === "phone" ? (
            <form onSubmit={sendOtp} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">Mobile Number</label>
                <div className="flex">
                  <span className="flex items-center px-4 bg-slate-50 border border-r-0 border-slate-200 rounded-l-xl text-slate-500 text-sm font-medium">+91</span>
                  <input type="tel" value={phone} onChange={e => setPhone(e.target.value)}
                    placeholder="98765 43210" required aria-label="Mobile number"
                    className="flex-1 input-field rounded-l-none border-l-0" />
                </div>
              </div>
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <button type="submit" disabled={loading} className="btn-primary">{loading ? "Sending..." : "Send OTP"}</button>
            </form>
          ) : (
            <form onSubmit={verifyOtp} className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-blue-700 text-xs flex items-center gap-2">
                <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Dev mode — OTP auto-filled for testing
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">6-Digit OTP</label>
                <input type="text" inputMode="numeric" value={otp} onChange={e => setOtp(e.target.value)}
                  placeholder="000000" maxLength={6} required aria-label="OTP"
                  className="input-field text-center text-2xl tracking-[0.5em] font-mono" />
              </div>
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <button type="submit" disabled={loading} className="btn-primary">{loading ? "Verifying..." : "Verify & Continue"}</button>
              <button type="button" onClick={() => setStep("phone")} className="w-full text-slate-500 hover:text-slate-700 text-sm py-1 transition-colors">← Use a different number</button>
            </form>
          )}
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          Available in हिंदी · मराठी · English
        </p>
      </div>
    </div>
  );
}

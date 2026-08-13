"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { HITRAGWordmark } from "@/components/ui/hitrag-wordmark";
import { loginUser, registerUser } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [isRegisterMode, setIsRegisterMode] = useState(false);

  // Form State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("STUDENT");
  const [rememberMe, setRememberMe] = useState(true);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");
    setIsLoading(true);

    try {
      if (isRegisterMode) {
        await registerUser({
          email,
          password,
          full_name: fullName,
          role,
        });

        setSuccessMessage("Account created successfully! Redirecting...");
        await loginUser(email, password);
        router.push("/chat");
      } else {
        await loginUser(email, password);
        router.push("/chat");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Authentication failed.";
      setError(msg);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#070C14] flex items-center justify-center p-4 sm:p-6 relative font-body select-none overflow-hidden">
      
      {/* Background 1: Soft Dynamic Gradient Mesh */}
      <div 
        className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(11,46,92,0.6),rgba(7,12,20,1))]"
      />

      {/* Background 2: Glowing Amber Brand Accent Sphere */}
      <div 
        className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[350px] bg-hit-amber/15 rounded-full blur-[140px] pointer-events-none"
      />

      {/* Background 3: Low-opacity Geometric Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(#E8A33D 1px, transparent 1px)`,
          backgroundSize: "32px 32px",
        }}
      />

      {/* Branded Premium Glassmorphic Card (Soft 20px corners, subtle inner glow & border) */}
      <div className="relative z-10 w-full max-w-[440px] bg-[#0E1726]/75 backdrop-blur-2xl border border-white/10 rounded-2xl p-8 sm:p-10 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8),0_0_40px_rgba(232,163,61,0.06)] flex flex-col items-center animate-in fade-in zoom-in-95 duration-500">
        
        {/* Branding: Official HITRAG Wordmark */}
        <div className="mb-6 scale-105">
          <HITRAGWordmark variant="light" />
        </div>

        {/* Dynamic Heading */}
        <div className="text-center mb-7 space-y-1">
          <h1 className="font-display text-2xl font-extrabold text-white tracking-tight">
            {isRegisterMode ? "Create an Account" : "Sign in to HITRAG"}
          </h1>
          <p className="text-xs text-hit-border/80">
            {isRegisterMode
              ? "Register your institutional credentials to get started"
              : "Enter your institutional credentials to access policy intelligence"}
          </p>
        </div>

        {/* Error / Success Alerts */}
        {error && (
          <div className="w-full mb-5 p-3 rounded-xl bg-hit-warning/15 border border-hit-warning/30 text-hit-warning text-xs font-medium flex items-center gap-2.5 animate-in fade-in slide-in-from-top-2">
            <span className="font-mono font-bold text-sm shrink-0">[!]</span>
            <span>{error}</span>
          </div>
        )}

        {successMessage && (
          <div className="w-full mb-5 p-3 rounded-xl bg-hit-success/15 border border-hit-success/30 text-hit-success text-xs font-medium flex items-center gap-2.5 animate-in fade-in slide-in-from-top-2">
            <span className="font-mono font-bold text-sm shrink-0">[✓]</span>
            <span>{successMessage}</span>
          </div>
        )}

        {/* Form Container */}
        <form onSubmit={handleSubmit} className="w-full space-y-4">
          
          {/* Full Name (Register Mode Only) */}
          {isRegisterMode && (
            <div className="space-y-1">
              <label className="block text-[11px] font-mono font-semibold uppercase tracking-wider text-hit-border/90">
                Full Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  placeholder="e.g. Tafadzwa Moyo"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-white/10 bg-[#071325]/60 text-white placeholder-hit-border/40 text-sm focus:outline-none focus:border-hit-amber focus:ring-1 focus:ring-hit-amber/50 transition-all pl-10"
                />
                <svg
                  className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-hit-amber/70"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          )}

          {/* Role Select (Register Mode Only) */}
          {isRegisterMode && (
            <div className="space-y-1">
              <label className="block text-[11px] font-mono font-semibold uppercase tracking-wider text-hit-border/90">
                Institutional Role
              </label>
              <div className="relative">
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-white/10 bg-[#071325]/90 text-white text-sm focus:outline-none focus:border-hit-amber focus:ring-1 focus:ring-hit-amber/50 transition-all appearance-none cursor-pointer font-mono"
                >
                  <option value="STUDENT" className="bg-[#0E1726] text-white">Student</option>
                  <option value="LECTURER" className="bg-[#0E1726] text-white">Lecturer / Academic Staff</option>
                  <option value="ADMIN" className="bg-[#0E1726] text-white">Administrator</option>
                  <option value="PUBLIC" className="bg-[#0E1726] text-white">Public Access</option>
                </select>
                <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-hit-amber/70 text-xs pointer-events-none">
                  ▼
                </span>
              </div>
            </div>
          )}

          {/* Email Input */}
          <div className="space-y-1">
            <label className="block text-[11px] font-mono font-semibold uppercase tracking-wider text-hit-border/90">
              Institutional Email / Username
            </label>
            <div className="relative">
              <input
                type="email"
                required
                placeholder="e.g. h220104s@hit.ac.zw"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-white/10 bg-[#071325]/60 text-white placeholder-hit-border/40 text-sm focus:outline-none focus:border-hit-amber focus:ring-1 focus:ring-hit-amber/50 transition-all pl-10"
              />
              <svg
                className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-hit-amber/70"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-1">
            <label className="block text-[11px] font-mono font-semibold uppercase tracking-wider text-hit-border/90">
              Password
            </label>
            <div className="relative">
              <input
                type="password"
                required
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-white/10 bg-[#071325]/60 text-white placeholder-hit-border/40 text-sm focus:outline-none focus:border-hit-amber focus:ring-1 focus:ring-hit-amber/50 transition-all pl-10"
              />
              <svg
                className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-hit-amber/70"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          </div>

          {/* Remember me & Forgot Password Row */}
          {!isRegisterMode && (
            <div className="flex items-center justify-between text-xs text-hit-border pt-1 pb-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-white/20 bg-[#071325] text-hit-amber focus:ring-0 accent-hit-amber cursor-pointer"
                />
                <span>Remember me</span>
              </label>
              <a
                href="#forgot-password"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Contact HIT ICT Helpdesk for credential recovery.");
                }}
                className="text-hit-amber hover:underline font-medium transition-colors"
              >
                Forgot password?
              </a>
            </div>
          )}

          {/* Accent Branded Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-6 rounded-xl bg-hit-amber hover:bg-hit-amber/90 active:scale-[0.99] text-[#070C14] font-display font-bold text-sm tracking-wide shadow-lg shadow-hit-amber/15 hover:shadow-hit-amber/25 transition-all duration-200 cursor-pointer mt-3 flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {isLoading ? (
              <>
                <span className="w-4 h-4 rounded-full border-2 border-[#070C14]/30 border-t-[#070C14] animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : isRegisterMode ? (
              <>
                <span>Register Account</span>
                <span className="font-mono">→</span>
              </>
            ) : (
              <>
                <span>Sign In to HITRAG</span>
                <span className="font-mono">→</span>
              </>
            )}
          </button>

          {/* Mode Switcher */}
          <div className="pt-4 text-center text-xs text-hit-border">
            {isRegisterMode ? (
              <span>
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setIsRegisterMode(false);
                    setError("");
                    setSuccessMessage("");
                  }}
                  className="font-bold text-hit-amber hover:underline cursor-pointer ml-1"
                >
                  Sign in here
                </button>
              </span>
            ) : (
              <span>
                Don&apos;t have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setIsRegisterMode(true);
                    setError("");
                    setSuccessMessage("");
                  }}
                  className="font-bold text-hit-amber hover:underline cursor-pointer ml-1"
                >
                  Register here
                </button>
              </span>
            )}
          </div>
        </form>
      </div>

      {/* Micro Institutional Footer */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-center text-[10px] font-mono text-hit-border/50">
        HIT ICT Services &copy; 2026 &bull; Secured Institutional Identity Provider
      </div>
    </div>
  );
}

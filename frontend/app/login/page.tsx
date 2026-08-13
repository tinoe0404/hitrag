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
        // Step 1: Register User Call
        await registerUser({
          email,
          password,
          full_name: fullName,
          role,
        });

        setSuccessMessage("Account created successfully! Logging you in...");
        
        // Step 2: Auto-login after registration
        await loginUser(email, password);
        router.push("/chat");
      } else {
        // Real Login Call
        await loginUser(email, password);
        router.push("/chat");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Authentication failed. Please check your inputs.";
      setError(msg);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-hit-bg flex items-center justify-center p-0 sm:p-6 lg:p-12">
      {/* Container: Single column on mobile, Split two-column on desktop */}
      <div className="w-full max-w-5xl min-h-screen sm:min-h-[640px] bg-hit-surface sm:rounded-2xl border-0 sm:border border-hit-border shadow-none sm:shadow-lg overflow-hidden grid grid-cols-1 lg:grid-cols-12">
        
        {/* Left Column: Sign-in Form (7 columns on desktop) */}
        <div className="lg:col-span-7 p-6 sm:p-10 lg:p-14 flex flex-col justify-between bg-hit-surface">
          <div>
            {/* Mobile Header Wordmark */}
            <div className="flex items-center justify-between mb-8 sm:mb-12">
              <HITRAGWordmark variant="navy" />
              <span className="font-mono text-[10px] bg-hit-bg border border-hit-border text-hit-text-secondary px-2.5 py-1 rounded-full uppercase tracking-wider font-semibold">
                HIT Network Auth
              </span>
            </div>

            {/* Form Headline */}
            <div className="space-y-2 mb-8">
              <h1 className="font-display text-2xl sm:text-3xl font-bold text-hit-blue tracking-tight">
                {isRegisterMode ? "Create an Account" : "Sign in to your account"}
              </h1>
              <p className="text-sm text-hit-text-secondary">
                {isRegisterMode
                  ? "Register your credentials to access HITRAG policy intelligence."
                  : "Enter your institutional credentials to access HITRAG policy intelligence."}
              </p>
            </div>

            {/* Auth Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3.5 rounded-lg bg-hit-warning/10 border border-hit-warning/30 text-hit-warning text-xs font-medium flex items-center gap-2">
                  <span className="font-mono font-bold">[!]</span>
                  <span>{error}</span>
                </div>
              )}

              {successMessage && (
                <div className="p-3.5 rounded-lg bg-hit-success/10 border border-hit-success/30 text-hit-success text-xs font-medium flex items-center gap-2">
                  <span className="font-mono font-bold">[✓]</span>
                  <span>{successMessage}</span>
                </div>
              )}

              {isRegisterMode && (
                <>
                  <div className="space-y-1.5">
                    <label
                      htmlFor="fullName"
                      className="block text-xs font-mono font-semibold uppercase tracking-wider text-hit-text-primary"
                    >
                      Full Name
                    </label>
                    <input
                      id="fullName"
                      type="text"
                      required
                      placeholder="e.g. Tafadzwa Moyo"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-lg border border-hit-border bg-hit-bg/50 text-hit-text-primary text-sm placeholder:text-hit-text-secondary/60 focus:bg-hit-surface focus:outline-none transition-colors"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label
                      htmlFor="role"
                      className="block text-xs font-mono font-semibold uppercase tracking-wider text-hit-text-primary"
                    >
                      Institutional Role
                    </label>
                    <select
                      id="role"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-lg border border-hit-border bg-hit-bg/50 text-hit-text-primary text-sm focus:bg-hit-surface focus:outline-none transition-colors font-mono"
                    >
                      <option value="STUDENT">Student</option>
                      <option value="LECTURER">Lecturer / Staff</option>
                      <option value="ADMIN">Administrator</option>
                      <option value="PUBLIC">Public</option>
                    </select>
                  </div>
                </>
              )}

              <div className="space-y-1.5">
                <label
                  htmlFor="email"
                  className="block text-xs font-mono font-semibold uppercase tracking-wider text-hit-text-primary"
                >
                  HIT Institutional Email / Registration ID
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  placeholder="e.g. h220104s@hit.ac.zw or jsmith@hit.ac.zw"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-hit-border bg-hit-bg/50 text-hit-text-primary text-sm placeholder:text-hit-text-secondary/60 focus:bg-hit-surface focus:outline-none transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="password"
                    className="block text-xs font-mono font-semibold uppercase tracking-wider text-hit-text-primary"
                  >
                    Password
                  </label>
                  {!isRegisterMode && (
                    <a
                      href="#forgot-password"
                      onClick={(e) => {
                        e.preventDefault();
                        alert("Contact HIT ICT Helpdesk for credential recovery.");
                      }}
                      className="text-xs font-mono text-hit-blue hover:underline"
                    >
                      Forgot password?
                    </a>
                  )}
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-hit-border bg-hit-bg/50 text-hit-text-primary text-sm placeholder:text-hit-text-secondary/60 focus:bg-hit-surface focus:outline-none transition-colors"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 py-3 px-4 rounded-lg bg-hit-blue hover:bg-hit-blue-dark text-white font-display text-sm font-semibold tracking-wide shadow-sm hover:shadow transition-all flex items-center justify-center gap-2 disabled:opacity-70 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                    <span>{isRegisterMode ? "Registering Account..." : "Authenticating HIT Session..."}</span>
                  </>
                ) : (
                  <>
                    <span>{isRegisterMode ? "Register Account" : "Sign In to HITRAG"}</span>
                    <span className="font-mono text-hit-amber">→</span>
                  </>
                )}
              </button>

              {/* Register / Sign In Toggle Link */}
              <div className="pt-2 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setIsRegisterMode(!isRegisterMode);
                    setError("");
                    setSuccessMessage("");
                  }}
                  className="text-xs font-mono text-hit-blue hover:underline cursor-pointer"
                >
                  {isRegisterMode
                    ? "Already have an account? Sign in here."
                    : "Need an account? Register here."}
                </button>
              </div>
            </form>
          </div>

          {/* Institutional Footer Notice */}
          <div className="mt-10 pt-6 border-t border-hit-border/60 flex items-center justify-between text-xs text-hit-text-secondary font-mono">
            <span>HIT ICT Services &copy; 2026</span>
            <span>Secured Session</span>
          </div>
        </div>

        {/* Right Column: Navy Institutional Panel (5 columns on desktop) */}
        <div className="lg:col-span-5 bg-hit-blue p-8 sm:p-12 text-white flex flex-col justify-between relative overflow-hidden border-t lg:border-t-0 lg:border-l border-hit-blue-dark">
          <div
            className="absolute inset-0 opacity-5 pointer-events-none"
            style={{
              backgroundImage: `radial-gradient(#E8A33D 1px, transparent 1px)`,
              backgroundSize: "24px 24px",
            }}
          />

          <div className="relative z-10 space-y-8">
            <HITRAGWordmark variant="light" className="hidden lg:flex" />

            <div className="space-y-4 pt-4 lg:pt-12">
              <span className="inline-block px-2.5 py-1 rounded bg-hit-blue-dark border border-white/10 font-mono text-[10px] text-hit-amber uppercase tracking-wider font-semibold">
                Success Through Innovation
              </span>
              <h2 className="font-display text-2xl sm:text-3xl font-bold text-white leading-tight">
                Ask HITRAG anything about HIT policy.
              </h2>
              <p className="text-sm text-hit-border leading-relaxed font-body">
                Grounded strictly in official Harare Institute of Technology regulations, academic handbooks, and administrative guidelines.
              </p>
            </div>
          </div>

          {/* Trust Strip */}
          <div className="relative z-10 pt-10 mt-8 border-t border-white/15 space-y-4">
            <span className="font-mono text-[10px] uppercase tracking-widest text-hit-amber font-semibold block">
              Institutional Trust Guarantees
            </span>
            <ul className="space-y-3 font-mono text-xs text-hit-border">
              <li className="flex items-start gap-2.5">
                <span className="text-hit-amber font-bold shrink-0">[1]</span>
                <span>Cites every answer with section-level document references.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="text-hit-amber font-bold shrink-0">[2]</span>
                <span>Respects your role access level (Student / Lecturer / Admin).</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="text-hit-amber font-bold shrink-0">[3]</span>
                <span>Built exclusively on HIT&apos;s official policy documents.</span>
              </li>
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
}

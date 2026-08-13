"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
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

        setSuccessMessage("Account created! Logging in...");
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
    <div className="min-h-screen w-full bg-[#0d131a] flex items-center justify-center p-4 relative font-sans select-none overflow-hidden">
      {/* Brick Wall Background Container */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-40 mix-blend-luminosity filter blur-[1px]"
        style={{ backgroundImage: `url('/brick-bg.png')` }}
      />

      {/* Simulated Wall Light Fixture Glow Effect */}
      <div className="absolute top-[8%] left-1/2 -translate-x-1/2 w-72 h-40 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-100/40 via-amber-300/10 to-transparent rounded-full blur-2xl pointer-events-none" />

      {/* Glassmorphic Auth Card */}
      <div className="relative z-10 w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 sm:p-10 shadow-2xl shadow-black/80 flex flex-col items-center">
        
        {/* Title */}
        <h1 className="text-3xl font-bold text-white tracking-wide mb-8 text-center drop-shadow">
          {isRegisterMode ? "Register" : "Login"}
        </h1>

        {/* Error / Success Alerts */}
        {error && (
          <div className="w-full mb-4 p-3 rounded-xl bg-red-500/20 border border-red-400/40 text-red-200 text-xs font-medium text-center backdrop-blur-md">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="w-full mb-4 p-3 rounded-xl bg-emerald-500/20 border border-emerald-400/40 text-emerald-200 text-xs font-medium text-center backdrop-blur-md">
            {successMessage}
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="w-full space-y-4">
          
          {/* Full Name Field (Register Mode Only) */}
          {isRegisterMode && (
            <div className="relative w-full">
              <input
                type="text"
                required
                placeholder="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-5 py-3.5 rounded-full border border-white/30 bg-black/20 text-white placeholder-white/70 text-sm focus:outline-none focus:border-white focus:bg-black/30 transition-all pr-12"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 text-sm">
                👤
              </span>
            </div>
          )}

          {/* Role Select (Register Mode Only) */}
          {isRegisterMode && (
            <div className="relative w-full">
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-5 py-3.5 rounded-full border border-white/30 bg-black/40 text-white text-sm focus:outline-none focus:border-white transition-all appearance-none cursor-pointer"
              >
                <option value="STUDENT" className="bg-gray-900 text-white">Student</option>
                <option value="LECTURER" className="bg-gray-900 text-white">Lecturer / Staff</option>
                <option value="ADMIN" className="bg-gray-900 text-white">Administrator</option>
                <option value="PUBLIC" className="bg-gray-900 text-white">Public</option>
              </select>
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 text-xs pointer-events-none">
                ▼
              </span>
            </div>
          )}

          {/* Username / Email Field */}
          <div className="relative w-full">
            <input
              type="email"
              required
              placeholder="Username / Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-5 py-3.5 rounded-full border border-white/30 bg-black/20 text-white placeholder-white/70 text-sm focus:outline-none focus:border-white focus:bg-black/30 transition-all pr-12"
            />
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 text-sm">
              👤
            </span>
          </div>

          {/* Password Field */}
          <div className="relative w-full">
            <input
              type="password"
              required
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-5 py-3.5 rounded-full border border-white/30 bg-black/20 text-white placeholder-white/70 text-sm focus:outline-none focus:border-white focus:bg-black/30 transition-all pr-12"
            />
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 text-sm">
              🔒
            </span>
          </div>

          {/* Remember me & Forgot password Row */}
          {!isRegisterMode && (
            <div className="flex items-center justify-between text-xs text-white/90 px-2 pt-1 pb-2">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-white/40 bg-black/30 text-white focus:ring-0 accent-white cursor-pointer"
                />
                <span>Remember me</span>
              </label>
              <a
                href="#forgot-password"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Contact HIT ICT Helpdesk for credential recovery.");
                }}
                className="hover:underline text-white/90"
              >
                Forgot password?
              </a>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-6 rounded-full bg-white hover:bg-white/90 text-gray-900 font-semibold text-base shadow-lg transition-all transform active:scale-95 disabled:opacity-70 cursor-pointer mt-2"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 rounded-full border-2 border-gray-900/30 border-t-gray-900 animate-spin" />
                <span>Processing...</span>
              </span>
            ) : isRegisterMode ? (
              "Register"
            ) : (
              "Login"
            )}
          </button>

          {/* Toggle Register / Login */}
          <div className="pt-4 text-center text-xs text-white/80">
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
                  className="font-bold text-white hover:underline cursor-pointer"
                >
                  Login
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
                  className="font-bold text-white hover:underline cursor-pointer"
                >
                  Register
                </button>
              </span>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

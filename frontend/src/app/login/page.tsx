"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import AuthShell from "@/components/AuthShell";
import { AlertTriangle, Eye, EyeOff, KeyRound, Lock, Mail, Spinner } from "@/components/icons";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login(email, password);
      setToken(res.access_token);
      router.push("/dashboard");
    } catch {
      setError("That email and password combination did not work. Please try again.");
      setLoading(false);
    }
  }

  return (
    <AuthShell>
      <div className="animate-fade-up">
        <p className="eyebrow">Sign in</p>
        <h1 className="mt-2 text-[32px] font-medium leading-tight">Welcome back.</h1>
        <p className="mt-2 text-sm text-slate-500">
          Continue to your due-diligence workspace.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          {error && (
            <div
              role="alert"
              className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-700"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="email" className="label">
              Email address
            </label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="email"
                className="input pl-10"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="label">
              Password
            </label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="password"
                className="input px-10"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((value) => !value)}
                className="absolute right-2 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-lg text-slate-400 transition hover:bg-ink/5 hover:text-ink"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
            {loading ? <Spinner /> : null}
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="mt-6 rounded-xl border border-dashed border-brass-300/70 bg-brass-50/70 p-3.5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-brass-700">
                <KeyRound className="h-3.5 w-3.5" />
                Demo account
              </p>
              <p className="mt-1.5 font-mono text-[11px] text-brass-900/80">
                demo@propchainai.com · demo1234
              </p>
            </div>
            <button
              type="button"
              className="btn-secondary btn-sm bg-white/70"
              onClick={() => {
                setEmail("demo@propchainai.com");
                setPassword("demo1234");
                setError("");
              }}
            >
              Use demo
            </button>
          </div>
        </div>

        <p className="mt-7 text-center text-sm text-slate-500">
          New here?{" "}
          <Link href="/register" className="font-semibold text-brand-700 underline-offset-4 hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}

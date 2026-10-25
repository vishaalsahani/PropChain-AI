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
      <div>
        <p className="eyebrow">Sign in</p>
        <h1 className="mt-3 font-display text-[44px] leading-[0.98] tracking-[-0.03em]">
          Welcome back.
        </h1>
        <p className="mt-3 text-[14px] leading-relaxed text-secondary">
          Continue to your due-diligence workspace.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          {error && (
            <div
              role="alert"
              className="flex items-start gap-2.5 border border-ink px-3.5 py-3 text-[13px] leading-relaxed text-ink"
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
              <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary" />
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
              <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary" />
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
                className="absolute right-1 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center text-secondary hover:text-ink"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button type="submit" className="btn btn-primary w-full" disabled={loading}>
            {loading ? <Spinner /> : null}
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="mt-6 border border-ink p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.1em] text-ink">
                <KeyRound className="h-3.5 w-3.5" />
                Demo account
              </p>
              <p className="mt-2 font-mono text-[11px] text-secondary">
                demo@propchainai.com · demo1234
              </p>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
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

        <p className="mt-7 text-center text-[14px] text-secondary">
          New here?{" "}
          <Link href="/register" className="border-b border-ink font-medium text-ink">
            Create an account
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}

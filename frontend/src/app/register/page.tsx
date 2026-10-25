"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import AuthShell from "@/components/AuthShell";
import { AlertTriangle, Eye, EyeOff, Lock, Mail, Spinner, User } from "@/components/icons";
import { api, setToken } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
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
      await api.register({ email, full_name: fullName, password });
      const res = await api.login(email, password);
      setToken(res.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
      setLoading(false);
    }
  }

  return (
    <AuthShell>
      <div>
        <p className="eyebrow">Get started</p>
        <h1 className="mt-3 font-display text-[44px] leading-[0.98] tracking-[-0.03em]">
          Create your workspace.
        </h1>
        <p className="mt-3 text-[14px] leading-relaxed text-secondary">
          Set up a private portfolio for your property files.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          {error && (
            <div
              role="alert"
              className="flex items-start gap-2.5 border border-ink px-3.5 py-3 text-[13px] leading-relaxed text-ink"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p className="break-words">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="full-name" className="label">
              Full name
            </label>
            <div className="relative">
              <User className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary" />
              <input
                id="full-name"
                className="input pl-10"
                autoComplete="name"
                placeholder="Your name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          </div>

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
                autoComplete="new-password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={6}
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
            <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
              Use at least 6 characters.
            </p>
          </div>

          <button type="submit" className="btn btn-primary w-full" disabled={loading}>
            {loading ? <Spinner /> : null}
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-7 text-center text-[14px] text-secondary">
          Already have an account?{" "}
          <Link href="/login" className="border-b border-ink font-medium text-ink">
            Sign in
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}

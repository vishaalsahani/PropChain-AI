"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Brand } from "@/components/Brand";
import { Landmark, LogOut, Plus } from "@/components/icons";
import { clearToken, getUserEmail } from "@/lib/api";

const LINKS = [
  { href: "/dashboard", label: "Portfolio" },
  { href: "/properties/new", label: "New property" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    setEmail(getUserEmail());
  }, [pathname]);

  const hide = pathname === "/login" || pathname === "/register";
  if (hide) return null;

  const initials = email ? email.slice(0, 2).toUpperCase() : "PC";

  return (
    <header className="sticky top-0 z-40 border-b border-ink/[0.06] bg-paper/80 backdrop-blur-xl">
      <div className="shell flex h-16 items-center justify-between gap-3">
        <Link href="/dashboard" className="rounded-xl py-1" aria-label="PropChain-AI dashboard">
          <Brand />
        </Link>

        <nav className="hidden items-center gap-1 rounded-full border border-ink/[0.07] bg-white/60 p-1 sm:flex">
          {LINKS.map((link) => {
            const active =
              link.href === "/dashboard"
                ? pathname === "/dashboard" || /^\/properties\/\d+/.test(pathname)
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-3.5 py-1.5 text-[13px] font-semibold transition ${
                  active
                    ? "bg-white text-ink shadow-sm ring-1 ring-ink/5"
                    : "text-slate-500 hover:text-ink"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <span className="chip hidden lg:inline-flex">
            <Landmark className="h-3.5 w-3.5 text-brand-700" />
            Maharashtra
          </span>

          <Link
            href="/properties/new"
            className="grid h-9 w-9 place-items-center rounded-xl border border-ink/10 bg-white/70 text-ink transition hover:border-brand-300 hover:bg-white sm:hidden"
            aria-label="New property"
          >
            <Plus className="h-4 w-4" />
          </Link>

          <span
            className="grid h-9 w-9 place-items-center rounded-full bg-brand-100 text-[11px] font-bold text-brand-800 ring-1 ring-inset ring-brand-700/10"
            title={email ?? "Account"}
          >
            {initials}
          </span>

          <button
            onClick={() => {
              clearToken();
              window.location.href = "/login";
            }}
            className="btn-ghost h-9 w-9 p-0"
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}

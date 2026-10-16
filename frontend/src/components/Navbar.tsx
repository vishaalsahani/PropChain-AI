"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearToken } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const hide = pathname === "/login" || pathname === "/register";

  if (hide) return null;

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link href="/dashboard" className="text-lg font-bold text-brand-700">
          PropChain-AI
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="hover:text-brand-700">
            Dashboard
          </Link>
          <Link href="/properties/new" className="hover:text-brand-700">
            New Property
          </Link>
          <button
            onClick={() => {
              clearToken();
              window.location.href = "/login";
            }}
            className="btn-secondary"
          >
            Logout
          </button>
        </nav>
      </div>
    </header>
  );
}

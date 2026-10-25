"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Brand } from "@/components/Brand";
import { LogOut, Plus } from "@/components/icons";
import { api, clearToken, getToken, UserOut } from "@/lib/api";

const LINKS = [
  { href: "/dashboard", label: "Portfolio" },
  { href: "/properties/new", label: "New property" },
  { href: "/rules", label: "Rules" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [email, setEmail] = useState<string | null>(null);
  const [user, setUser] = useState<UserOut | null>(null);
  // usePathname() is not identical during static pre-render and hydration on
  // every route, so active-link attributes are only applied after mount. The
  // un-highlighted first paint is preferable to a hydration mismatch.
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!getToken()) {
      setEmail(null);
      setUser(null);
      return;
    }
    api
      .me()
      .then((current) => {
        setUser(current);
        setEmail(current.email);
      })
      .catch(() => {
        clearToken();
        setEmail(null);
        setUser(null);
      });
  }, [pathname]);

  const hide = pathname === "/login" || pathname === "/register";
  if (hide) return null;

  const initials = email ? email.slice(0, 2).toUpperCase() : "PC";
  const links = email
    ? [
        ...LINKS,
        ...(user?.role === "reviewer" || user?.role === "admin"
          ? [{ href: "/review", label: "Review queue" }]
          : []),
      ]
    : [{ href: "/rules", label: "Rules" }];
  // On mobile the plus control already opens the new-property form, so keep
  // the text row short enough to stay on one line. "Review" is the compact
  // label for the reviewer queue at narrow widths.
  const mobileLinks = links
    .filter((link) => link.href !== "/properties/new")
    .map((link) => (link.href === "/review" ? { ...link, label: "Review" } : link));

  return (
    <header className="sticky top-0 z-40 border-b border-quiet bg-paper">
      <div className="shell flex h-[72px] items-center gap-10">
        <Link
          href={email ? "/dashboard" : "/"}
          className="shrink-0"
          aria-label={email ? "PropChain-AI dashboard" : "PropChain-AI home"}
        >
          <Brand />
        </Link>

        <nav className="hidden items-center gap-6 md:flex xl:gap-7" aria-label="Workspace">
          {links.map((link) => {
            const active =
              mounted &&
              (link.href === "/dashboard"
                ? pathname === "/dashboard" || /^\/properties\/\d+/.test(pathname)
                : pathname.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={`smallcaps whitespace-nowrap border-b pb-0.5 ${
                  link.href === "/properties/new" ? "hidden lg:inline-flex" : ""
                } ${
                  active
                    ? "border-ink text-ink"
                    : "border-transparent text-secondary hover:border-ink hover:text-ink"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <span className="eyebrow hidden xl:inline-flex">Maharashtra</span>

          {email ? (
            <>
              <Link
                href="/properties/new"
                className="icon-btn lg:hidden"
                aria-label="New property"
              >
                <Plus className="h-4 w-4" />
              </Link>

              <span
                className="grid h-9 w-9 place-items-center border border-ink font-mono text-[10px] uppercase tracking-[0.08em]"
                title={user ? `${user.email} · ${user.role}` : email}
              >
                {initials}
              </span>

              <button
                onClick={() => {
                  clearToken();
                  window.location.href = "/login";
                }}
                className="icon-btn"
                title="Sign out"
                aria-label="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </>
          ) : (
            <Link href="/login" className="btn btn-secondary btn-sm">
              Sign in
            </Link>
          )}
        </div>
      </div>

      <nav
        className="shell flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-quiet py-3 md:hidden"
        aria-label="Workspace mobile"
      >
        {mobileLinks.map((link) => {
          const active =
            mounted &&
            (link.href === "/dashboard"
              ? pathname === "/dashboard" || /^\/properties\/\d+/.test(pathname)
              : pathname.startsWith(link.href));
          return (
            <Link
              key={link.href}
              href={link.href}
              aria-current={active ? "page" : undefined}
              className={`smallcaps shrink-0 border-b pb-0.5 ${
                active
                  ? "border-ink text-ink"
                  : "border-transparent text-secondary hover:border-ink hover:text-ink"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}

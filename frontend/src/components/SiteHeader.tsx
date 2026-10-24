import Link from "next/link";
import { Brand } from "@/components/Brand";
import { ArrowRight } from "@/components/icons";

const NAV = [
  { href: "#checks", label: "What we check" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#verdicts", label: "Verdicts" },
  { href: "#responsible", label: "Responsible AI" },
];

export default function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-ink/[0.06] bg-paper/80 backdrop-blur-xl">
      <div className="shell flex h-16 items-center justify-between gap-4">
        <Link href="/" aria-label="PropChain-AI home" className="shrink-0 rounded-xl py-1">
          <Brand />
        </Link>

        <nav className="hidden items-center gap-6 text-[13px] font-medium text-slate-500 lg:flex xl:gap-7">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="whitespace-nowrap transition hover:text-ink"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-1.5">
          <Link href="/login" className="btn-ghost hidden whitespace-nowrap sm:inline-flex">
            Sign in
          </Link>
          <Link href="/register" className="btn-primary whitespace-nowrap">
            <span className="hidden sm:inline">Create account</span>
            <span className="sm:hidden">Get started</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </header>
  );
}

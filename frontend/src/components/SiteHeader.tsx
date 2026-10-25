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
    <header className="sticky top-0 z-40 border-b border-quiet bg-paper">
      <div className="shell flex h-[72px] items-center gap-10">
        <Link href="/" aria-label="PropChain-AI home" className="shrink-0">
          <Brand />
        </Link>

        <nav
          className="hidden items-center gap-6 lg:flex"
          aria-label="Landing page sections"
        >
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="smallcaps border-b border-transparent pb-0.5 text-secondary hover:border-ink hover:text-ink"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="ml-auto flex shrink-0 items-center gap-3">
          <Link href="/login" className="smallcaps hidden text-ink sm:inline-flex">
            Sign in
          </Link>
          <Link href="/register" className="btn btn-primary text-[11px]">
            <span className="hidden sm:inline">Create account</span>
            <span className="sm:hidden">Get started</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </header>
  );
}

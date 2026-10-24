import Link from "next/link";
import { Brand } from "@/components/Brand";
import { ShieldCheck } from "@/components/icons";

export default function SiteFooter() {
  return (
    <footer className="border-t border-ink/[0.06] bg-white/40">
      <div className="shell grid gap-10 py-12 md:grid-cols-[1.5fr_1fr_1fr]">
        <div>
          <Brand />
          <p className="mt-4 max-w-sm text-[13px] leading-relaxed text-slate-500">
            AI-assisted documentary analysis for Maharashtra property files. Extraction, cross-
            verification and an evidence-based ownership chain.
          </p>
          <p className="mt-5 inline-flex items-center gap-2 rounded-full border border-ink/[0.07] bg-white/70 px-3 py-1.5 text-[11px] font-medium text-slate-500">
            <ShieldCheck className="h-3.5 w-3.5 text-brand-700" />
            Findings are indicators, not legal determinations
          </p>
        </div>

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">Product</p>
          <ul className="mt-3 space-y-2 text-[13px] text-slate-500">
            <li><a href="#checks" className="hover:text-ink">What we check</a></li>
            <li><a href="#how-it-works" className="hover:text-ink">How it works</a></li>
            <li><a href="#verdicts" className="hover:text-ink">Screening verdicts</a></li>
            <li><a href="#responsible" className="hover:text-ink">Responsible AI</a></li>
          </ul>
        </div>

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">Workspace</p>
          <ul className="mt-3 space-y-2 text-[13px] text-slate-500">
            <li><Link href="/login" className="hover:text-ink">Sign in</Link></li>
            <li><Link href="/register" className="hover:text-ink">Create an account</Link></li>
            <li><Link href="/dashboard" className="hover:text-ink">Open the portfolio</Link></li>
          </ul>
        </div>
      </div>

      <div className="border-t border-ink/[0.06]">
        <div className="shell flex flex-wrap items-center justify-between gap-3 py-5 text-[11px] text-slate-400">
          <p>© {new Date().getFullYear()} PropChain-AI · Maharashtra MVP</p>
          <p>Not a substitute for government records or professional legal advice.</p>
        </div>
      </div>
    </footer>
  );
}

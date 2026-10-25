import Link from "next/link";
import { Brand } from "@/components/Brand";
import { ShieldCheck } from "@/components/icons";

export default function SiteFooter() {
  return (
    <footer className="border-t-[3px] border-ink">
      <div className="shell">
        <div className="dp-section py-12">
          <div className="dp-rail">
            <Brand />
            <p className="mt-5 max-w-sm text-[14px] leading-relaxed text-secondary">
              AI-assisted documentary analysis for Maharashtra property files. Extraction,
              cross-verification and an evidence-based ownership chain.
            </p>
            <p className="mt-5 flex items-start gap-2 font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-secondary">
              <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink" />
              Findings are indicators, not legal determinations
            </p>
          </div>

          <div className="dp-body">
            <div className="grid gap-10 sm:grid-cols-2">
              <div>
                <p className="eyebrow text-ink">Product</p>
                <ul className="mt-4 space-y-2.5 font-text text-[14px]">
                  <li>
                    <a href="#checks" className="border-b border-transparent hover:border-ink">
                      What we check
                    </a>
                  </li>
                  <li>
                    <a href="#how-it-works" className="border-b border-transparent hover:border-ink">
                      How it works
                    </a>
                  </li>
                  <li>
                    <a href="#verdicts" className="border-b border-transparent hover:border-ink">
                      Screening verdicts
                    </a>
                  </li>
                  <li>
                    <a href="#responsible" className="border-b border-transparent hover:border-ink">
                      Responsible AI
                    </a>
                  </li>
                </ul>
              </div>

              <div>
                <p className="eyebrow text-ink">Workspace</p>
                <ul className="mt-4 space-y-2.5 font-text text-[14px]">
                  <li>
                    <Link href="/login" className="border-b border-transparent hover:border-ink">
                      Sign in
                    </Link>
                  </li>
                  <li>
                    <Link href="/register" className="border-b border-transparent hover:border-ink">
                      Create an account
                    </Link>
                  </li>
                  <li>
                    <Link href="/dashboard" className="border-b border-transparent hover:border-ink">
                      Open the portfolio
                    </Link>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-quiet py-5 font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-secondary">
          <p>© {new Date().getFullYear()} PropChain-AI · Maharashtra MVP</p>
          <p>Not a substitute for government records or professional legal advice.</p>
        </div>
      </div>
    </footer>
  );
}

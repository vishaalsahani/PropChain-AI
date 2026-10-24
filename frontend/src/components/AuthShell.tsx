import { Brand } from "@/components/Brand";
import { Layers, Link2, ShieldCheck } from "@/components/icons";

const FEATURES = [
  {
    icon: Layers,
    title: "Extraction in English & Marathi",
    body: "Sale deeds, 7/12 extracts, property cards, ECs and ferfars become structured fields.",
  },
  {
    icon: Link2,
    title: "Cross-document consistency",
    body: "Survey numbers, area, owners, dates and registration numbers are tested against each other.",
  },
  {
    icon: ShieldCheck,
    title: "Hash-anchored documents",
    body: "Files stay off-chain. Only their SHA-256 fingerprints are registered and verified.",
  },
];

export default function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen lg:grid lg:grid-cols-[1.08fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-brand-950 px-10 py-12 text-white lg:flex lg:flex-col xl:px-14">
        <div aria-hidden className="absolute inset-0 bg-grid-dark [background-size:32px_32px]" />
        <div
          aria-hidden
          className="absolute -left-32 -top-24 h-[520px] w-[520px] rounded-full bg-brand-600/25 blur-3xl"
        />
        <div
          aria-hidden
          className="absolute -bottom-40 -right-24 h-[460px] w-[460px] rounded-full bg-brass-400/10 blur-3xl"
        />

        <div className="relative z-10 flex items-center justify-between gap-4">
          <Brand light />
          <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-100/80">
            Maharashtra · MVP
          </span>
        </div>

        <div className="relative z-10 mt-14 max-w-lg">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-brass-200/80">
            Evidence-first due diligence
          </p>
          <h1 className="mt-4 font-display text-[40px] font-medium leading-[1.06] text-white xl:text-[46px]">
            Read the file.
            <br />
            Prove the chain.
          </h1>
          <p className="mt-5 max-w-md text-sm leading-relaxed text-brand-100/70">
            PropChain-AI turns Maharashtra property documents into structured evidence, checks them
            against each other, and traces the ownership chain — with every unknown stated plainly.
          </p>

          <ul className="mt-9 space-y-5">
            {FEATURES.map((feature) => (
              <li key={feature.title} className="flex gap-3.5">
                <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.06] text-brass-200">
                  <feature.icon className="h-[18px] w-[18px]" />
                </span>
                <div>
                  <p className="text-[13px] font-semibold text-white">{feature.title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-brand-100/55">{feature.body}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div aria-hidden className="relative z-10 mt-10 hidden h-48 max-w-md 2xl:block">
          <div className="absolute left-0 top-2 w-[61%] -rotate-3 rounded-2xl border border-white/10 bg-white/[0.055] p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between text-[9px] font-semibold uppercase tracking-[0.18em] text-brand-200/60">
              <span>7/12 Extract</span>
              <span>मराठी</span>
            </div>
            <div className="mt-4 space-y-2">
              <div className="h-1.5 w-4/5 rounded-full bg-white/15" />
              <div className="h-1.5 w-3/5 rounded-full bg-white/10" />
              <div className="h-1.5 w-2/3 rounded-full bg-white/10" />
            </div>
            <div className="mt-4 flex gap-2">
              <span className="rounded-md bg-brand-900/80 px-2 py-1 text-[9px] text-brand-100/70">Survey 42/2</span>
              <span className="rounded-md bg-brand-900/80 px-2 py-1 text-[9px] text-brand-100/70">0.24 ha</span>
            </div>
          </div>

          <div className="absolute right-0 top-12 w-[63%] rotate-2 rounded-2xl border border-ink/5 bg-[#fffdf8] p-4 text-ink shadow-[0_30px_60px_-20px_rgba(0,0,0,0.55)]">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-slate-400">Sale Deed</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[9px] font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-600/15">
                <ShieldCheck className="h-2.5 w-2.5" />
                Hash verified
              </span>
            </div>
            <p className="mt-3 font-display text-sm text-ink">Registered transfer · 2019</p>
            <div className="mt-2 space-y-1.5">
              <div className="h-1.5 w-11/12 rounded-full bg-slate-200/80" />
              <div className="h-1.5 w-2/3 rounded-full bg-slate-200/60" />
            </div>
            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2.5">
              <span className="font-mono text-[9px] text-slate-400">SHA-256 · 9f3a…c21e</span>
              <span className="text-[9px] font-semibold text-brand-700">Chain intact</span>
            </div>
          </div>
        </div>

        <p className="relative z-10 mt-auto pt-10 text-[11px] leading-relaxed text-brand-200/45">
          Findings are screening indicators for a reviewer — not legal determinations. Always confirm
          against government records and professional advice.
        </p>
      </aside>

      <main className="flex min-h-screen flex-col px-4 py-8 sm:px-8 lg:px-10 lg:py-10">
        <div className="lg:hidden">
          <Brand />
        </div>

        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-[420px]">{children}</div>
        </div>

        <p className="text-center text-[11px] text-slate-400">
          © {new Date().getFullYear()} PropChain-AI · Built for Maharashtra land records
        </p>
      </main>
    </div>
  );
}

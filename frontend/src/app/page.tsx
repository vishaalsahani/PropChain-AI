import type { Metadata } from "next";
import Link from "next/link";

import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";
import {
  ArrowRight,
  Check,
  FileText,
  Flag,
  Hash,
  Landmark,
  Layers,
  Link2,
  Lock,
  MapPin,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "@/components/icons";

export const metadata: Metadata = {
  title: "Evidence-first property due diligence",
  description:
    "AI-assisted due diligence for Maharashtra property files. Read deed sets in English and Marathi, cross-check the facts and trace an evidence-based ownership chain.",
};

const CHECKS = [
  {
    icon: Layers,
    title: "Cross-document consistency",
    body: "Survey and gat numbers, owners, area, boundaries, registration details and dates are compared across the whole deed set.",
    footnote: "Catches mismatches between the sale deed, 7/12 extract and property card.",
  },
  {
    icon: Link2,
    title: "Evidence-based ownership chain",
    body: "Transfers are sequenced from the root record. Missing links and unregistered gaps are surfaced rather than smoothed over.",
    footnote: "Every node points back to the document that supports it.",
  },
  {
    icon: Landmark,
    title: "Maharashtra rule pack",
    body: "A deterministic policy checks land type, succession, encumbrance, identity and area rules for the Maharashtra record stack.",
    footnote: "Same findings and policy version produce the same verdict.",
  },
  {
    icon: Lock,
    title: "Integrity you can verify",
    body: "Each upload is hashed with SHA-256. Only the hash is registered on-chain — the document itself stays off-chain.",
    footnote: "Tamper-evident by design, private by default.",
  },
];

const STEPS = [
  {
    icon: FileText,
    title: "Create the file",
    body: "Add the property and upload the deed set — sale deeds, 7/12 extracts, property cards and encumbrance certificates.",
    meta: "Input · PDF or image scans",
  },
  {
    icon: Sparkles,
    title: "Run the analysis",
    body: "OCR in English and Marathi, document classification, field extraction, cross-checks and ownership reconstruction.",
    meta: "Pipeline · OCR → extract → cross-check → chain → policy",
  },
  {
    icon: ShieldCheck,
    title: "Review the evidence",
    body: "A verdict with reasons, severity and confidence for each finding, plus an explicit list of what was not checked.",
    meta: "Output · Verdict, report and audit trail",
  },
];

const RECORD_STACK = [
  "7/12 extract",
  "Property card",
  "Sale deed",
  "Encumbrance certificate",
  "Ferfar",
  "Index II",
];

const VERDICTS = [
  {
    tone: "border-emerald-200/70 bg-emerald-50/70",
    iconTone: "bg-emerald-600 text-white",
    titleTone: "text-emerald-950",
    label: "Verified",
    icon: ShieldCheck,
    body: "The checks that ran found no blocking inconsistency across the uploaded documents.",
    trigger: "Clean file, complete chain",
  },
  {
    tone: "border-amber-200/70 bg-amber-50/70",
    iconTone: "bg-amber-500 text-white",
    titleTone: "text-amber-950",
    label: "Needs review",
    icon: ShieldAlert,
    body: "Something could not be cleared automatically. A reviewer decides what to do next.",
    trigger: "Ambiguous extract or incomplete evidence",
  },
  {
    tone: "border-rose-200/70 bg-rose-50/70",
    iconTone: "bg-rose-500 text-white",
    titleTone: "text-rose-950",
    label: "Flagged",
    icon: Flag,
    body: "A significant finding or an ownership gap needs attention before the file proceeds.",
    trigger: "Missing link or critical mismatch",
  },
];

export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <main>
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-40 -top-48 h-[34rem] w-[34rem] rounded-full bg-brand-200/40 blur-3xl"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -left-40 top-40 h-[28rem] w-[28rem] rounded-full bg-brass-200/30 blur-3xl"
          />

          <div className="shell relative grid gap-14 py-16 md:py-20 lg:grid-cols-[1.04fr_0.96fr] lg:items-center lg:gap-12 lg:py-24">
            <div className="animate-fade-up">
              <p className="inline-flex items-center gap-2 rounded-full border border-brand-900/10 bg-white/60 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.17em] text-brand-800 shadow-soft backdrop-blur">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                AI-assisted screening · Maharashtra land records
              </p>

              <h1 className="mt-6 max-w-[13ch] text-balance text-[2.75rem] leading-[1.03] tracking-[-0.025em] sm:text-[3.75rem] lg:text-[3.5rem] xl:text-[4.1rem]">
                Due diligence that{" "}
                <span className="relative inline-block text-brand-800">
                  shows its evidence.
                  <svg
                    aria-hidden="true"
                    viewBox="0 0 320 12"
                    preserveAspectRatio="none"
                    className="absolute -bottom-2 left-0 h-2.5 w-full text-brass-400"
                  >
                    <path
                      d="M2 8.5c58-4.5 112-4.5 166-2 45 2 92 1.5 150-3"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </span>
              </h1>

              <p className="mt-7 max-w-xl text-[15px] leading-7 text-slate-600">
                PropChain-AI reads sale deeds, 7/12 extracts, property cards and encumbrance
                certificates in English and Marathi — then cross-checks them and traces the chain
                of title, with a reason behind every finding.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link href="/register" className="btn-primary px-5 py-3 text-[13px]">
                  Create a property file
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link href="/login" className="btn-secondary px-5 py-3 text-[13px]">
                  Sign in to the workspace
                </Link>
              </div>

              <ul className="mt-9 space-y-2.5 text-[12px] text-slate-500">
                {[
                  "Documents stay off-chain — only their SHA-256 hashes are registered.",
                  "Every not-checked item stays visible in the verdict.",
                  "Screening indicators for a reviewer — not a legal title opinion.",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-brand-100 text-brand-800">
                      <Check className="h-2.5 w-2.5" />
                    </span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="relative mx-auto w-full max-w-[480px] animate-fade-up animation-delay-200">
              <div
                aria-hidden="true"
                className="absolute -inset-8 rounded-[3rem] bg-gradient-to-br from-brand-200/60 via-paper to-brass-200/50 blur-2xl"
              />
              <div className="relative rounded-[26px] border border-ink/[0.08] bg-white/90 p-5 shadow-lift backdrop-blur-sm sm:p-6">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-slate-400">
                      Screening result
                    </p>
                    <p className="mt-0.5 text-[11px] text-slate-500">Gat 214 · Koregaon, Satara</p>
                  </div>
                  <span className="badge bg-amber-500/10 text-amber-800 ring-1 ring-inset ring-amber-600/20">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                    Needs review
                  </span>
                </div>

                <div className="mt-4 rounded-2xl border border-amber-600/10 bg-gradient-to-br from-amber-50 to-white p-4">
                  <div className="flex items-start gap-3">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-amber-500 text-white">
                      <ShieldAlert className="h-4.5 w-4.5" />
                    </span>
                    <div>
                      <p className="font-display text-[19px] leading-tight text-amber-950">
                        Area mismatch across documents
                      </p>
                      <p className="mt-1 text-[11px] leading-relaxed text-slate-500">
                        Sale deed records 2,000 sq ft. The 7/12 extract records 1,850 sq ft.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-4 space-y-2.5">
                  {[
                    { icon: FileText, text: "Sale deed · 2019 · 2,000 sq ft", tone: "text-slate-500" },
                    { icon: MapPin, text: "7/12 extract · 1,850 sq ft", tone: "text-slate-500" },
                    { icon: Flag, text: "150 sq ft difference · medium severity", tone: "text-amber-700" },
                  ].map((row) => (
                    <div
                      key={row.text}
                      className="flex items-center gap-2.5 rounded-lg border border-ink/[0.05] bg-paper/50 px-3 py-2 text-[11px]"
                    >
                      <row.icon className={`h-3.5 w-3.5 shrink-0 ${row.tone}`} />
                      <span className="text-slate-600">{row.text}</span>
                    </div>
                  ))}
                </div>

                <div className="mt-4 border-t border-ink/[0.06] pt-4">
                  <div className="flex items-center justify-between">
                    <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-slate-400">
                      Ownership chain
                    </p>
                    <span className="text-[9px] font-semibold text-amber-700">1 gap noted</span>
                  </div>
                  <div className="mt-2 flex items-center gap-1.5 text-[10px] font-medium text-slate-600">
                    <span className="rounded-md bg-paper px-2 py-1 ring-1 ring-inset ring-ink/[0.06]">
                      Dagdu Shinde
                    </span>
                    <ArrowRight className="h-3 w-3 shrink-0 text-slate-300" />
                    <span className="rounded-md bg-paper px-2 py-1 ring-1 ring-inset ring-ink/[0.06]">
                      Vitthal More
                    </span>
                    <ArrowRight className="h-3 w-3 shrink-0 text-slate-300" />
                    <span className="rounded-md border border-dashed border-amber-500/30 bg-amber-50/60 px-2 py-1 text-amber-800">
                      Missing link
                    </span>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between gap-2 rounded-xl bg-brand-950 px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5 text-[10px] font-medium text-brand-100">
                    <Hash className="h-3 w-3 text-brass-300" />
                    SHA-256 anchored
                  </span>
                  <span className="font-mono text-[9px] tracking-tight text-brand-200/70">
                    9f3a82…c21e
                  </span>
                </div>
              </div>
              <p className="mt-3 text-center text-[10px] text-slate-400">
                Illustrative screening output
              </p>
            </div>
          </div>

          <div className="shell relative">
            <div className="flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-ink/[0.07] py-5 text-[11px] text-slate-500">
              <span className="font-semibold uppercase tracking-[0.15em] text-slate-400">
                Built for the Maharashtra record stack
              </span>
              {RECORD_STACK.map((item) => (
                <span key={item} className="inline-flex items-center gap-1.5">
                  <Check className="h-3 w-3 text-brand-600" />
                  {item}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* What we check */}
        <section id="checks" className="scroll-mt-24 py-20">
          <div className="shell">
            <div className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr] lg:gap-16">
              <div>
                <p className="eyebrow text-brand-700">The review</p>
                <h2 className="mt-3 max-w-sm text-balance text-3xl leading-tight tracking-[-0.02em] sm:text-4xl">
                  More than OCR. A documented chain of reasoning.
                </h2>
                <p className="mt-4 max-w-md text-sm leading-7 text-slate-600">
                  Extraction is only the first step. The engine compares what each document says,
                  reconstructs the sequence of transfers, and applies a fixed Maharashtra rule pack
                  to decide what a reviewer should look at.
                </p>
                <div className="mt-6 rounded-2xl border border-brand-900/10 bg-brand-50/60 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-brand-800">
                    The principle
                  </p>
                  <p className="mt-1.5 font-display text-lg leading-snug text-brand-950">
                    If the evidence isn&apos;t there, the finding says so.
                  </p>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {CHECKS.map((item) => (
                  <article
                    key={item.title}
                    className="group rounded-2xl border border-ink/[0.06] bg-white/70 p-5 shadow-soft backdrop-blur-sm transition duration-300 hover:-translate-y-0.5 hover:border-brand-200 hover:bg-white/90"
                  >
                    <span className="grid h-10 w-10 place-items-center rounded-xl border border-brand-900/10 bg-brand-50 text-brand-700">
                      <item.icon className="h-[18px] w-[18px]" />
                    </span>
                    <h3 className="mt-4 text-[17px] font-medium leading-snug">{item.title}</h3>
                    <p className="mt-2 text-[12px] leading-relaxed text-slate-500">{item.body}</p>
                    <p className="mt-4 border-t border-ink/[0.06] pt-3 text-[10px] leading-relaxed text-slate-400">
                      {item.footnote}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="relative scroll-mt-20 overflow-hidden bg-brand-950 py-20 text-white">
          <div aria-hidden="true" className="absolute inset-0 bg-grid-dark opacity-70" />
          <div
            aria-hidden="true"
            className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-brand-500/20 blur-3xl"
          />

          <div className="shell relative">
            <div className="flex flex-wrap items-end justify-between gap-6">
              <div className="max-w-2xl">
                <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-brass-300">
                  How it works
                </p>
                <h2 className="mt-3 text-balance text-3xl leading-tight tracking-[-0.02em] text-white sm:text-4xl">
                  From a folder of scans to a reviewable verdict.
                </h2>
              </div>
              <p className="max-w-sm text-[13px] leading-6 text-brand-100/65">
                No black-box score. Each stage leaves a trace you can inspect in the workspace and
                in the report.
              </p>
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {STEPS.map((step, index) => (
                <article
                  key={step.title}
                  className="relative rounded-2xl border border-white/10 bg-white/[0.045] p-5 backdrop-blur-sm"
                >
                  <span className="absolute right-5 top-4 font-display text-4xl leading-none text-white/10">
                    0{index + 1}
                  </span>
                  <span className="grid h-10 w-10 place-items-center rounded-xl bg-white/10 text-brass-200 ring-1 ring-inset ring-white/10">
                    <step.icon className="h-[18px] w-[18px]" />
                  </span>
                  <h3 className="mt-5 text-[18px] font-medium text-white">{step.title}</h3>
                  <p className="mt-2 text-[12px] leading-relaxed text-brand-100/65">{step.body}</p>
                  <p className="mt-4 border-t border-white/10 pt-3 text-[10px] leading-relaxed text-brand-200/50">
                    {step.meta}
                  </p>
                </article>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-x-2 gap-y-2 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
              <span className="mr-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-brass-300">
                Pipeline
              </span>
              {["OCR", "Classify", "Extract", "Cross-check", "Chain", "Verdict policy", "Report"].map(
                (stage, index, all) => (
                  <span key={stage} className="inline-flex items-center gap-2 text-[11px] text-brand-100/60">
                    {stage}
                    {index < all.length - 1 && <ArrowRight className="h-3 w-3 text-white/20" />}
                  </span>
                ),
              )}
            </div>
          </div>
        </section>

        {/* Verdicts */}
        <section id="verdicts" className="scroll-mt-24 py-20">
          <div className="shell">
            <div className="mx-auto max-w-2xl text-center">
              <p className="eyebrow text-brand-700">Screening verdicts</p>
              <h2 className="mt-3 text-balance text-3xl leading-tight tracking-[-0.02em] sm:text-4xl">
                Three outcomes. One transparent policy.
              </h2>
              <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-slate-600">
                The verdict is a screening output under a fixed rule pack. It tells a reviewer what
                needs attention — it does not silently turn missing evidence into a pass.
              </p>
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {VERDICTS.map((verdict) => (
                <article
                  key={verdict.label}
                  className={`rounded-2xl border p-5 shadow-soft ${verdict.tone}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className={`grid h-10 w-10 place-items-center rounded-xl ${verdict.iconTone}`}>
                      <verdict.icon className="h-[18px] w-[18px]" />
                    </span>
                    <span className="text-[9px] font-bold uppercase tracking-[0.16em] text-slate-400">
                      Verdict
                    </span>
                  </div>
                  <h3 className={`mt-4 font-display text-[26px] leading-none ${verdict.titleTone}`}>
                    {verdict.label}
                  </h3>
                  <p className="mt-3 min-h-[60px] text-[12px] leading-relaxed text-slate-600">
                    {verdict.body}
                  </p>
                  <p className="border-t border-ink/[0.07] pt-3 text-[10px] leading-relaxed text-slate-500">
                    <span className="font-semibold text-slate-600">Typical trigger · </span>
                    {verdict.trigger}
                  </p>
                </article>
              ))}
            </div>

            <div className="mx-auto mt-8 flex max-w-3xl items-start gap-3 rounded-2xl border border-ink/[0.06] bg-white/60 px-4 py-3.5">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-brand-700" />
              <p className="text-[11px] leading-relaxed text-slate-500">
                <span className="font-semibold text-slate-700">Not a legal determination.</span>{" "}
                Findings are screening indicators for a human reviewer. A clean verdict is not a
                title certificate, and a flagged verdict is not an allegation.
              </p>
            </div>
          </div>
        </section>

        {/* Responsible AI */}
        <section id="responsible" className="scroll-mt-24 pb-20">
          <div className="shell">
            <div className="overflow-hidden rounded-3xl border border-ink/[0.06] bg-white/60 shadow-soft backdrop-blur-sm">
              <div className="grid lg:grid-cols-[0.95fr_1.05fr]">
                <div className="p-7 sm:p-10">
                  <p className="eyebrow text-brand-700">Responsible by design</p>
                  <h2 className="mt-3 text-balance text-3xl leading-tight tracking-[-0.02em]">
                    Evidence over confidence.
                  </h2>
                  <p className="mt-4 text-sm leading-7 text-slate-600">
                    Property records are messy. The useful question is not &ldquo;does the AI look
                    sure?&rdquo; but &ldquo;what exactly did it check, what did it find, and what did
                    it leave unknown?&rdquo;
                  </p>

                  <div className="mt-7 space-y-4">
                    {[
                      {
                        title: "Every finding has a source",
                        body: "The document, extracted values and rule reference travel with each finding — no unsupported scores.",
                      },
                      {
                        title: "Unknowns are first-class",
                        body: "RERA, litigation, government record checks and title opinion stay in a visible not-checked list.",
                      },
                      {
                        title: "Documents stay private",
                        body: "Only hashes are registered on-chain. Original files remain off-chain in the application store.",
                      },
                    ].map((item) => (
                      <div key={item.title} className="flex gap-3">
                        <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-brand-100 text-brand-800">
                          <Check className="h-3 w-3" />
                        </span>
                        <div>
                          <p className="text-[13px] font-semibold text-ink">{item.title}</p>
                          <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500">
                            {item.body}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="border-t border-ink/[0.06] bg-paper/50 p-7 sm:p-10 lg:border-l lg:border-t-0">
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                      In every verdict
                    </p>
                    <span className="badge bg-brand-900/5 text-brand-800 ring-1 ring-inset ring-brand-900/10">
                      Always stated
                    </span>
                  </div>
                  <h3 className="mt-4 font-display text-2xl leading-snug">
                    What this review does <span className="text-brand-700">not</span> decide.
                  </h3>
                  <div className="mt-5 grid gap-2 sm:grid-cols-2">
                    {[
                      "RERA registration status",
                      "Pending litigation",
                      "Government record verification",
                      "Legal title opinion",
                      "Physical boundary verification",
                      "Mortgage or lien clearance",
                    ].map((item) => (
                      <div
                        key={item}
                        className="flex items-start gap-2 rounded-xl border border-ink/[0.06] bg-white/70 px-3 py-2.5 text-[11px] text-slate-500"
                      >
                        <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-300" />
                        {item}
                      </div>
                    ))}
                  </div>
                  <p className="mt-5 border-t border-ink/[0.07] pt-4 text-[10px] leading-relaxed text-slate-400">
                    These items are surfaced explicitly so a reviewer can follow up outside the
                    system. They are never assumed to be clean.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="pb-20">
          <div className="shell">
            <div className="relative overflow-hidden rounded-[28px] bg-brand-900 px-6 py-12 text-center shadow-lift sm:px-12 sm:py-14">
              <div aria-hidden="true" className="absolute inset-0 bg-grid-dark opacity-50" />
              <div
                aria-hidden="true"
                className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-brass-400/20 blur-3xl"
              />
              <div className="relative mx-auto max-w-xl">
                <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-100">
                  <Sparkles className="h-3 w-3 text-brass-300" />
                  Start with one property
                </span>
                <h2 className="mt-5 text-balance font-display text-3xl leading-tight text-white sm:text-4xl">
                  Open your first property file.
                </h2>
                <p className="mx-auto mt-3 max-w-md text-[13px] leading-6 text-brand-100/70">
                  Create a workspace, upload a deed set and follow the evidence from extraction to
                  an explainable screening verdict.
                </p>
                <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
                  <Link
                    href="/register"
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-[13px] font-semibold text-brand-950 shadow-soft transition hover:-translate-y-px hover:bg-brand-50"
                  >
                    Create an account
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    href="/login"
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/5 px-5 py-3 text-[13px] font-semibold text-white transition hover:bg-white/10"
                  >
                    Sign in
                  </Link>
                </div>
                <p className="mt-5 text-[10px] text-brand-200/50">
                  Demo environment · Uploaded documents stay off-chain
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}

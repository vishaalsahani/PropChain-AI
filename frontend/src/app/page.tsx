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
    label: "Verified",
    icon: ShieldCheck,
    body: "The checks that ran found no blocking inconsistency across the uploaded documents.",
    trigger: "Clean file, complete chain",
  },
  {
    label: "Needs review",
    icon: ShieldAlert,
    body: "Something could not be cleared automatically. A reviewer decides what to do next.",
    trigger: "Ambiguous extract or incomplete evidence",
  },
  {
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
        <section className="border-b border-quiet">
          <div className="shell">
            <div className="dp-section section-y">
              <div className="dp-rail">
                <p className="eyebrow">
                  AI-assisted screening
                  <br />
                  Maharashtra land records
                </p>
                <p className="mt-6 max-w-[14rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-secondary">
                  Findings are screening indicators for a reviewer — not legal determinations.
                </p>
              </div>

              <div className="dp-body">
                <h1 className="display-title">
                  Due diligence that{" "}
                  <em className="font-display italic">shows its evidence.</em>
                </h1>

                <div className="mt-10 grid gap-10 lg:grid-cols-[0.94fr_1.06fr] lg:items-start">
                  <div>
                    <p className="max-w-[34em] text-[17px] leading-[1.55] text-secondary">
                      PropChain-AI reads sale deeds, 7/12 extracts, property cards and encumbrance
                      certificates in English and Marathi — then cross-checks them and traces the
                      chain of title, with a reason behind every finding.
                    </p>

                    <div className="mt-8 flex flex-wrap items-center gap-3">
                      <Link href="/register" className="btn btn-primary">
                        Create a property file
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                      <Link href="/login" className="btn btn-secondary">
                        Sign in to the workspace
                      </Link>
                    </div>

                    <ul className="mt-10 space-y-3 border-t border-quiet pt-5 text-[13px] leading-relaxed text-secondary">
                      {[
                        "Documents stay off-chain — only their SHA-256 hashes are registered.",
                        "Every not-checked item stays visible in the verdict.",
                        "Screening indicators for a reviewer — not a legal title opinion.",
                      ].map((item) => (
                        <li key={item} className="flex items-start gap-2.5">
                          <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center border border-ink text-ink">
                            <Check className="h-2.5 w-2.5" />
                          </span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="border border-ink">
                    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-ink p-4">
                      <div>
                        <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-secondary">
                          Screening result
                        </p>
                        <p className="mt-1 font-display text-[19px] leading-none">
                          Gat 214 · Koregaon, Satara
                        </p>
                      </div>
                      <span className="border border-ink bg-ink px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.1em] text-paper">
                        Needs review
                      </span>
                    </div>

                    <div className="p-4">
                      <div className="border border-ink p-4">
                        <div className="flex items-start gap-3">
                          <span className="grid h-9 w-9 shrink-0 place-items-center border border-ink text-ink">
                            <ShieldAlert className="h-4 w-4" />
                          </span>
                          <div>
                            <p className="font-display text-[24px] leading-[1.02]">
                              Area mismatch across documents
                            </p>
                            <p className="mt-2 text-[11px] leading-relaxed text-secondary">
                              Sale deed records 2,000 sq ft. The 7/12 extract records 1,850 sq ft.
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4">
                        {[
                          { icon: FileText, text: "Sale deed · 2019 · 2,000 sq ft" },
                          { icon: MapPin, text: "7/12 extract · 1,850 sq ft" },
                          { icon: Flag, text: "150 sq ft difference · medium severity" },
                        ].map((row) => (
                          <div
                            key={row.text}
                            className="flex items-center gap-2.5 border-t border-quiet py-2.5 font-mono text-[10px] text-secondary first:border-t-0"
                          >
                            <row.icon className="h-3.5 w-3.5 shrink-0 text-ink" />
                            <span>{row.text}</span>
                          </div>
                        ))}
                      </div>

                      <div className="border-t border-ink pt-4">
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-secondary">
                            Ownership chain
                          </p>
                          <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-ink">
                            1 gap noted
                          </span>
                        </div>
                        <div className="mt-2 flex flex-wrap items-center gap-1.5 font-mono text-[9px] text-secondary">
                          <span className="border border-quiet px-2 py-1">Dagdu Shinde</span>
                          <ArrowRight className="h-3 w-3 shrink-0 text-quiet" />
                          <span className="border border-quiet px-2 py-1">Vitthal More</span>
                          <ArrowRight className="h-3 w-3 shrink-0 text-quiet" />
                          <span className="border border-dashed border-ink px-2 py-1 text-ink">
                            Missing link
                          </span>
                        </div>
                      </div>

                      <div className="mt-4 flex items-center justify-between gap-2 bg-ink px-3 py-2.5">
                        <span className="inline-flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-[0.08em] text-paper">
                          <Hash className="h-3 w-3" />
                          SHA-256 anchored
                        </span>
                        <span className="font-mono text-[9px] tracking-tight text-quiet">
                          9f3a82…c21e
                        </span>
                      </div>
                    </div>

                    <p className="border-t border-quiet px-4 py-2.5 font-mono text-[9px] uppercase tracking-[0.08em] text-secondary">
                      Illustrative screening output
                    </p>
                  </div>
                </div>

                <div className="mt-10 flex flex-wrap items-center gap-x-7 gap-y-2.5 border-t border-quiet pt-5">
                  <span className="eyebrow text-ink">Built for the Maharashtra record stack</span>
                  {RECORD_STACK.map((item) => (
                    <span
                      key={item}
                      className="inline-flex items-center gap-1.5 font-mono text-[10px] text-secondary"
                    >
                      <Check className="h-3 w-3 text-ink" />
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="checks" className="scroll-mt-24 border-b border-quiet">
          <div className="shell">
            <div className="dp-section section-y">
              <div className="dp-rail">
                <p className="eyebrow">The review</p>
                <h2 className="display-heading mt-4">
                  More than OCR. A documented chain of reasoning.
                </h2>
                <p className="mt-5 max-w-[34em] text-[14px] leading-[1.55] text-secondary">
                  Extraction is only the first step. The engine compares what each document says,
                  reconstructs the sequence of transfers, and applies a fixed Maharashtra rule pack
                  to decide what a reviewer should look at.
                </p>
                <div className="mt-8 border-t border-ink pt-4">
                  <p className="eyebrow text-ink">The principle</p>
                  <p className="mt-2 font-display text-[24px] leading-[1.05]">
                    If the evidence isn&apos;t there, the finding says so.
                  </p>
                </div>
              </div>

              <div className="dp-body">
                <div className="grid gap-px bg-quiet sm:grid-cols-2">
                  {CHECKS.map((item) => (
                    <article key={item.title} className="bg-paper p-6">
                      <span className="grid h-10 w-10 place-items-center border border-ink text-ink">
                        <item.icon className="h-[18px] w-[18px]" />
                      </span>
                      <h3 className="mt-5 font-display text-[26px] leading-[1.02]">{item.title}</h3>
                      <p className="mt-3 text-[13px] leading-relaxed text-secondary">{item.body}</p>
                      <p className="mt-5 border-t border-quiet pt-3 font-mono text-[10px] uppercase leading-relaxed tracking-[0.06em] text-secondary">
                        {item.footnote}
                      </p>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="scroll-mt-20 border-b border-ink bg-ink text-paper">
          <div className="shell">
            <div className="dp-section section-y">
              <div className="dp-rail">
                <p className="eyebrow text-quiet">How it works</p>
                <h2 className="display-heading mt-4 text-paper">
                  From a folder of scans to a reviewable verdict.
                </h2>
                <p className="mt-5 max-w-[30em] text-[13px] leading-relaxed text-quiet">
                  No black-box score. Each stage leaves a trace you can inspect in the workspace and
                  in the report.
                </p>
              </div>

              <div className="dp-body dp-body--inverted">
                <div className="grid gap-px bg-quiet-inverted md:grid-cols-3">
                  {STEPS.map((step, index) => (
                    <article key={step.title} className="bg-ink p-6">
                      <div className="flex items-start justify-between gap-4">
                        <span className="grid h-10 w-10 place-items-center border border-quiet-inverted text-quiet">
                          <step.icon className="h-[18px] w-[18px]" />
                        </span>
                        <span className="font-display text-[54px] leading-none text-quiet-inverted">
                          0{index + 1}
                        </span>
                      </div>
                      <h3 className="mt-6 font-display text-[26px] leading-[1.02] text-paper">
                        {step.title}
                      </h3>
                      <p className="mt-3 text-[13px] leading-relaxed text-quiet">{step.body}</p>
                      <p className="mt-5 border-t border-quiet-inverted pt-3 font-mono text-[9px] uppercase leading-relaxed tracking-[0.06em] text-quiet">
                        {step.meta}
                      </p>
                    </article>
                  ))}
                </div>

                <div className="mt-8 flex flex-wrap items-center gap-x-2 gap-y-2 border-t border-quiet-inverted pt-4">
                  <span className="mr-2 font-mono text-[9px] uppercase tracking-[0.1em] text-quiet">
                    Pipeline
                  </span>
                  {["OCR", "Classify", "Extract", "Cross-check", "Chain", "Verdict policy", "Report"].map(
                    (stage, index, all) => (
                      <span
                        key={stage}
                        className="inline-flex items-center gap-2 font-mono text-[10px] text-quiet"
                      >
                        {stage}
                        {index < all.length - 1 && (
                          <ArrowRight className="h-3 w-3 text-quiet-inverted" />
                        )}
                      </span>
                    ),
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="verdicts" className="scroll-mt-24 border-b border-quiet">
          <div className="shell">
            <div className="dp-section section-y">
              <div className="dp-rail">
                <p className="eyebrow">Screening verdicts</p>
                <h2 className="display-heading mt-4">Three outcomes. One transparent policy.</h2>
                <p className="mt-5 max-w-[32em] text-[14px] leading-[1.55] text-secondary">
                  The verdict is a screening output under a fixed rule pack. It tells a reviewer what
                  needs attention — it does not silently turn missing evidence into a pass.
                </p>
              </div>

              <div className="dp-body">
                <div className="bg-ink p-5 sm:p-8">
                  <div className="grid gap-px bg-quiet-inverted md:grid-cols-3">
                    {VERDICTS.map((verdict, index) => {
                      const featured = index === 1;
                      const Icon = verdict.icon;
                      return (
                        <article
                          key={verdict.label}
                          className={`p-6 ${
                            featured
                              ? "relative z-10 border border-ink bg-paper text-ink md:-my-5 md:p-8"
                              : "bg-ink text-paper"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span
                              className={`grid h-10 w-10 place-items-center border ${
                                featured
                                  ? "border-ink text-ink"
                                  : "border-quiet-inverted text-quiet"
                              }`}
                            >
                              <Icon className="h-[18px] w-[18px]" />
                            </span>
                            <span
                              className={`font-mono text-[9px] uppercase tracking-[0.1em] ${
                                featured ? "text-secondary" : "text-quiet"
                              }`}
                            >
                              Verdict
                            </span>
                          </div>
                          <h3
                            className={`mt-6 font-display text-[36px] leading-none tracking-[-0.03em] ${
                              featured ? "text-ink" : "text-paper"
                            }`}
                          >
                            {verdict.label}
                          </h3>
                          <p
                            className={`mt-3 min-h-[84px] text-[13px] leading-relaxed ${
                              featured ? "text-secondary" : "text-quiet"
                            }`}
                          >
                            {verdict.body}
                          </p>
                          <p
                            className={`border-t pt-3 font-mono text-[9px] uppercase leading-relaxed tracking-[0.06em] ${
                              featured
                                ? "border-quiet text-secondary"
                                : "border-quiet-inverted text-quiet"
                            }`}
                          >
                            <span className={featured ? "text-ink" : "text-paper"}>
                              Typical trigger
                            </span>{" "}
                            · {verdict.trigger}
                          </p>
                        </article>
                      );
                    })}
                  </div>
                </div>

                <div className="mt-6 flex max-w-[52em] items-start gap-3 border-t border-ink pt-4">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-ink" />
                  <p className="text-[12px] leading-relaxed text-secondary">
                    <span className="font-medium text-ink">Not a legal determination.</span> Findings
                    are screening indicators for a human reviewer. A clean verdict is not a title
                    certificate, and a flagged verdict is not an allegation.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="responsible" className="scroll-mt-24 border-b border-quiet">
          <div className="shell">
            <div className="dp-section section-y">
              <div className="dp-rail">
                <p className="eyebrow">Responsible by design</p>
                <h2 className="display-heading mt-4">Evidence over confidence.</h2>
                <p className="mt-5 max-w-[30em] text-[14px] leading-[1.55] text-secondary">
                  Property records are messy. The useful question is not &ldquo;does the AI look
                  sure?&rdquo; but &ldquo;what exactly did it check, what did it find, and what did
                  it leave unknown?&rdquo;
                </p>
              </div>

              <div className="dp-body">
                <div className="grid gap-8 lg:grid-cols-2 lg:gap-10">
                  <div>
                    <ul className="border-t border-quiet">
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
                        <li key={item.title} className="flex gap-3 border-b border-quiet py-5">
                          <span className="mt-1 grid h-5 w-5 shrink-0 place-items-center border border-ink text-ink">
                            <Check className="h-3 w-3" />
                          </span>
                          <div>
                            <p className="font-display text-[22px] leading-[1.05] text-ink">
                              {item.title}
                            </p>
                            <p className="mt-1.5 text-[12px] leading-relaxed text-secondary">
                              {item.body}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-ink p-6 text-paper lg:p-8">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-quiet">
                        In every verdict
                      </p>
                      <span className="border border-quiet-inverted px-2 py-1 font-mono text-[9px] uppercase tracking-[0.08em] text-quiet">
                        Always stated
                      </span>
                    </div>
                    <h3 className="mt-5 font-display text-[30px] leading-[1.02] text-paper">
                      What this review does <em className="italic text-quiet">not</em> decide.
                    </h3>
                    <div className="mt-5 grid gap-px bg-quiet-inverted sm:grid-cols-2">
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
                          className="flex items-start gap-2 bg-ink px-3 py-2.5 font-mono text-[10px] leading-relaxed text-quiet"
                        >
                          <span className="mt-1.5 h-1 w-1 shrink-0 bg-quiet" />
                          {item}
                        </div>
                      ))}
                    </div>
                    <p className="mt-5 border-t border-quiet-inverted pt-4 font-mono text-[9px] uppercase leading-relaxed tracking-[0.06em] text-quiet">
                      These items are surfaced explicitly so a reviewer can follow up outside the
                      system. They are never assumed to be clean.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-t-[3px] border-ink bg-ink text-paper">
          <div className="shell">
            <div className="dp-section section-y">
              <div className="dp-rail">
                <p className="eyebrow text-quiet">Start with one property</p>
                <p className="mt-5 max-w-[13rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-quiet">
                  Demo environment · Uploaded documents stay off-chain
                </p>
              </div>

              <div className="dp-body dp-body--inverted">
                <h2 className="font-display text-[clamp(42px,6cqw,84px)] font-medium leading-[0.98] tracking-[-0.04em] text-paper">
                  Open your first property file.
                </h2>
                <p className="mt-5 max-w-[34em] text-[15px] leading-relaxed text-quiet">
                  Create a workspace, upload a deed set and follow the evidence from extraction to
                  an explainable screening verdict.
                </p>
                <div className="mt-8 flex flex-wrap items-center gap-3">
                  <Link href="/register" className="btn btn-on-ink">
                    Create an account
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link href="/login" className="btn btn-on-ink-outline">
                    Sign in
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}

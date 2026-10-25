"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import { AlertTriangle, ArrowRight, Check, ShieldCheck, Spinner } from "@/components/icons";
import { api, getToken, ReviewQueueItem, UserOut } from "@/lib/api";
import { formatDate, humanize, riskTone } from "@/lib/presentation";

type Filter = "awaiting" | "reviewed" | "all";

function verdictChip(value: string | null) {
  const label = value ? humanize(value) : "No verdict";
  const filled = value === "flagged" || value === "needs_review";
  return (
    <span
      className={`inline-flex items-center border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.08em] ${
        filled ? "border-ink bg-ink text-paper" : "border-quiet text-secondary"
      }`}
    >
      {label}
    </span>
  );
}

function reviewChip(status: string) {
  const reviewed = status === "confirmed" || status === "overridden";
  return (
    <span
      className={`inline-flex items-center gap-1 border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.08em] ${
        reviewed ? "border-ink bg-ink text-paper" : "border-quiet text-secondary"
      }`}
    >
      {reviewed && <Check className="h-2.5 w-2.5" />}
      {status === "pending" ? "Awaiting review" : humanize(status)}
    </span>
  );
}

export default function ReviewQueuePage() {
  const [me, setMe] = useState<UserOut | null>(null);
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [filter, setFilter] = useState<Filter>("awaiting");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    const user = await api.me();
    setMe(user);
    if (user.role !== "reviewer" && user.role !== "admin") {
      setItems([]);
      return;
    }
    setItems(await api.reviewQueue());
  }

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    load()
      .catch((err) =>
        setError(err instanceof Error ? err.message : "The review queue could not be loaded.")
      )
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const counts = useMemo(
    () => ({
      all: items.length,
      awaiting: items.filter((item) => item.review_status === "pending").length,
      reviewed: items.filter((item) => item.review_status !== "pending").length,
      flagged: items.filter((item) => item.verdict === "flagged").length,
      evidence: items.reduce((sum, item) => sum + item.open_findings, 0),
    }),
    [items]
  );

  const visible = items.filter((item) =>
    filter === "all"
      ? true
      : filter === "awaiting"
        ? item.review_status === "pending"
        : item.review_status !== "pending"
  );

  const allowed = me?.role === "reviewer" || me?.role === "admin";

  return (
    <>
      <Navbar />
      <main>
        <section className="border-b border-ink bg-ink text-paper">
          <div className="shell">
            <div className="dp-section section-y-md">
              <div className="dp-rail">
                <p className="eyebrow text-quiet">Human review</p>
                <p className="mt-5 max-w-[13rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-quiet">
                  Latest run per file · append-only decisions
                </p>
              </div>
              <div className="dp-body dp-body--inverted">
                <h1 className="font-display text-[clamp(42px,6cqw,84px)] font-medium leading-[0.98] tracking-[-0.04em] text-paper">
                  Review the evidence, not the interface.
                </h1>
                <p className="mt-4 max-w-[40em] text-[15px] leading-[1.55] text-quiet">
                  Work the queue one file at a time. Disposition individual findings, then confirm
                  the system verdict or record an override with a note that remains in the record.
                </p>
              </div>
            </div>
          </div>
        </section>

        <div className="shell">
          {loading && (
            <div className="mt-8 border border-quiet px-5 py-16 text-center">
              <Spinner className="mx-auto h-5 w-5 text-ink" />
              <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                Loading the queue…
              </p>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="mt-8 flex items-start gap-3 border border-ink px-4 py-3.5 text-[13px] leading-relaxed text-ink"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p className="flex-1">{error}</p>
            </div>
          )}

          {!loading && !error && !allowed && (
            <div className="mx-auto mt-10 max-w-xl border border-ink p-8 text-center">
              <ShieldCheck className="mx-auto h-7 w-7 text-ink" />
              <h2 className="mt-4 font-display text-[32px] leading-none">
                Reviewer access is required
              </h2>
              <p className="mt-3 text-[13px] leading-relaxed text-secondary">
                You are signed in as {me ? humanize(me.role) : "a non-reviewer"}. Ask an
                administrator to provision a reviewer account, or return to your own portfolio.
              </p>
              <Link href="/dashboard" className="btn btn-secondary mt-6">
                Back to portfolio
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          )}

          {!loading && !error && allowed && (
            <>
              <section className="mt-8 grid gap-px border border-quiet bg-quiet sm:grid-cols-2 xl:grid-cols-4">
                <div className="bg-paper p-5">
                  <p className="eyebrow">Analysed files</p>
                  <p className="display-number mt-3">{counts.all}</p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    Latest completed run
                  </p>
                </div>
                <div className="bg-paper p-5">
                  <p className="eyebrow">Awaiting review</p>
                  <p className="display-number mt-3">{counts.awaiting}</p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    No human decision yet
                  </p>
                </div>
                <div className="bg-paper p-5">
                  <p className="eyebrow">Flagged runs</p>
                  <p className="display-number mt-3">{counts.flagged}</p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    System verdict
                  </p>
                </div>
                <div className="bg-paper p-5">
                  <p className="eyebrow">Open findings</p>
                  <p className="display-number mt-3">{counts.evidence}</p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    Awaiting review or evidence
                  </p>
                </div>
              </section>

              <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-b border-ink pb-3">
                <h2 className="display-heading">Queue</h2>
                <div className="flex flex-wrap gap-1">
                  {(["awaiting", "reviewed", "all"] as const).map((value) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setFilter(value)}
                      className={`border px-3 py-1.5 font-mono text-[9px] uppercase tracking-[0.08em] ${
                        filter === value
                          ? "border-ink bg-ink text-paper"
                          : "border-quiet text-secondary hover:border-ink hover:text-ink"
                      }`}
                      aria-pressed={filter === value}
                    >
                      {value} · {counts[value]}
                    </button>
                  ))}
                </div>
              </div>

              {visible.length === 0 ? (
                <div className="border-b border-quiet py-16 text-center">
                  <ShieldCheck className="mx-auto h-6 w-6 text-ink" />
                  <p className="mt-3 font-display text-[26px] leading-none">Queue is clear</p>
                  <p className="mx-auto mt-2 max-w-sm text-[13px] leading-relaxed text-secondary">
                    There are no files in this filter. New runs appear here automatically.
                  </p>
                </div>
              ) : (
                <ol>
                  {visible.map((item) => {
                    const risk = riskTone(item.risk_score);
                    return (
                      <li key={item.run_id} className="border-b border-quiet py-5">
                        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              {verdictChip(item.verdict)}
                              {reviewChip(item.review_status)}
                              <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-secondary">
                                Run #{item.run_id} · {item.finished_at ? formatDate(item.finished_at) : "in progress"}
                              </span>
                            </div>
                            <h3 className="mt-2 max-w-[34em] font-display text-[28px] font-medium leading-[1.02] text-ink">
                              {item.title}
                            </h3>
                            <p className="mt-1.5 text-[12px] leading-relaxed text-secondary">
                              {[item.village, item.district].filter(Boolean).join(", ") || "Location not set"}
                            </p>
                            <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[10px] text-secondary">
                              <span>
                                <span className="uppercase tracking-[0.08em]">Risk</span>{" "}
                                <span className="font-medium text-ink">{risk.label}</span>{" "}
                                {item.risk_score !== null ? `· ${Math.round(item.risk_score)}` : ""}
                              </span>
                              <span>
                                <span className="uppercase tracking-[0.08em]">Findings</span>{" "}
                                <span className="font-medium text-ink">{item.open_findings}</span> open
                                {" · "}
                                {item.total_findings} total
                              </span>
                              {item.review_verdict && (
                                <span>
                                  <span className="uppercase tracking-[0.08em]">Final</span>{" "}
                                  <span className="font-medium text-ink">
                                    {humanize(item.review_verdict)}
                                  </span>
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-start">
                            <Link
                              href={`/properties/${item.property_id}`}
                              className="btn btn-secondary btn-sm"
                            >
                              Open file
                              <ArrowRight className="h-3.5 w-3.5" />
                            </Link>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ol>
              )}

              <div className="mt-8 border-t border-ink py-4">
                <p className="max-w-[54em] text-[11px] leading-relaxed text-secondary">
                  <span className="font-medium text-ink">Reviewer note.</span> A human decision is
                  recorded against the exact analysis run. Re-running the analysis creates a new run
                  and returns the file to the queue; the previous decision remains in run history.
                </p>
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
}

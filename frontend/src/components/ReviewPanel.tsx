"use client";

import { useState } from "react";
import { AlertTriangle, Check, FileText, ShieldCheck, Spinner } from "@/components/icons";
import { AnalysisRunSummary, api } from "@/lib/api";
import { formatDate, humanize } from "@/lib/presentation";

type Decision = "confirmed" | "overridden";

function reviewBadge(status: string) {
  const label =
    status === "confirmed"
      ? "Confirmed"
      : status === "overridden"
        ? "Overridden"
        : status === "pending"
          ? "Awaiting review"
          : humanize(status);
  const filled = status === "confirmed" || status === "overridden";
  return (
    <span
      className={`inline-flex items-center gap-1.5 border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.08em] ${
        filled ? "border-ink bg-ink text-paper" : "border-quiet text-secondary"
      }`}
    >
      {filled && <Check className="h-2.5 w-2.5" />}
      {label}
    </span>
  );
}

function verdictText(value: string | null) {
  return value ? humanize(value) : "Not recorded";
}

export default function ReviewPanel({
  latestRun,
  runs,
  canReview,
  onUpdated,
}: {
  latestRun: AnalysisRunSummary | null;
  runs: AnalysisRunSummary[];
  canReview: boolean;
  onUpdated: () => Promise<void>;
}) {
  const [decision, setDecision] = useState<Decision>("confirmed");
  const [overrideVerdict, setOverrideVerdict] = useState<
    "verified" | "needs_review" | "flagged"
  >("needs_review");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!latestRun) {
    return (
      <div className="border border-quiet px-5 py-10 text-center">
        <ShieldCheck className="mx-auto h-5 w-5 text-secondary" />
        <p className="mt-3 font-display text-[24px] leading-none text-ink">Not ready for review</p>
        <p className="mx-auto mt-2 max-w-sm text-[13px] leading-relaxed text-secondary">
          Human review starts after the owner has run an analysis. No run exists for this file yet.
        </p>
      </div>
    );
  }

  async function submit(nextDecision: Decision) {
    if (!latestRun) return;
    if (note.trim().length < 3) {
      setError("Add a review note of at least three characters before recording a decision.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.reviewRun(latestRun.id, {
        decision: nextDecision,
        verdict: nextDecision === "overridden" ? overrideVerdict : null,
        note: note.trim(),
      });
      setNote("");
      await onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "The review could not be recorded.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="grid gap-px border border-quiet bg-quiet sm:grid-cols-2 xl:grid-cols-4">
        <div className="bg-paper p-4">
          <p className="eyebrow">Latest run</p>
          <p className="mt-2 font-display text-[26px] leading-none">#{latestRun.id}</p>
          <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
            {latestRun.finished_at ? formatDate(latestRun.finished_at) : "In progress"}
          </p>
        </div>
        <div className="bg-paper p-4">
          <p className="eyebrow">System verdict</p>
          <p className="mt-2 font-display text-[24px] leading-none">
            {verdictText(latestRun.verdict)}
          </p>
          <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
            {latestRun.finding_count} findings
          </p>
        </div>
        <div className="bg-paper p-4">
          <p className="eyebrow">Human review</p>
          <div className="mt-2">{reviewBadge(latestRun.review_status)}</div>
          <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
            {latestRun.reviewed_at
              ? `Reviewed ${formatDate(latestRun.reviewed_at)}`
              : "No decision recorded"}
          </p>
        </div>
        <div className="bg-paper p-4">
          <p className="eyebrow">Final verdict</p>
          <p className="mt-2 font-display text-[24px] leading-none">
            {verdictText(latestRun.review_verdict)}
          </p>
          <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
            {latestRun.review_verdict
              ? "Reviewer decision of record"
              : "System verdict stands until reviewed"}
          </p>
        </div>
      </div>

      {latestRun.review_note && (
        <div className="mt-4 border-l border-ink pl-4">
          <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-secondary">
            Reviewer note
          </p>
          <p className="mt-1 max-w-[52em] text-[13px] leading-relaxed text-ink">
            {latestRun.review_note}
          </p>
        </div>
      )}

      {!canReview && (
        <p className="mt-4 border border-quiet px-4 py-3 text-[12px] leading-relaxed text-secondary">
          Owner view. Only a reviewer or administrator can record a human decision on this run.
        </p>
      )}

      {canReview && (
        <div className="mt-6 border border-ink p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="eyebrow">Record a decision</p>
              <p className="mt-1 max-w-[44em] text-[13px] leading-relaxed text-secondary">
                Confirming keeps the system verdict. Overriding records your final disposition and
                updates the property status. The system output is never erased.
              </p>
            </div>
            <span className="border border-quiet px-2 py-1 font-mono text-[9px] uppercase tracking-[0.08em] text-secondary">
              Run #{latestRun.id}
            </span>
          </div>

          {error && (
            <p
              role="alert"
              className="mt-4 flex items-start gap-2 border border-ink px-3.5 py-2.5 text-[12px] leading-relaxed text-ink"
            >
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {error}
            </p>
          )}

          <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_auto]">
            <div>
              <label htmlFor="review-note" className="label">
                Review note
              </label>
              <textarea
                id="review-note"
                className="input mt-2 min-h-[76px] text-[13px]"
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="What did you verify, and what remains uncertain?"
              />
            </div>
            <div className="min-w-[220px]">
              <label htmlFor="override-verdict" className="label">
                Override verdict
              </label>
              <select
                id="override-verdict"
                className="input mt-2"
                value={overrideVerdict}
                onChange={(event) =>
                  setOverrideVerdict(
                    event.target.value as "verified" | "needs_review" | "flagged"
                  )
                }
                disabled={decision !== "overridden"}
              >
                <option value="verified">Verified</option>
                <option value="needs_review">Needs review</option>
                <option value="flagged">Flagged</option>
              </select>
              <label className="mt-3 flex items-center gap-2 font-mono text-[9px] uppercase tracking-[0.08em] text-ink">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-ink"
                  checked={decision === "overridden"}
                  onChange={(event) =>
                    setDecision(event.target.checked ? "overridden" : "confirmed")
                  }
                />
                Use override
              </label>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => submit("confirmed")}
              disabled={busy}
            >
              {busy ? <Spinner /> : <Check className="h-3.5 w-3.5" />}
              Confirm system verdict
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => submit("overridden")}
              disabled={busy || decision !== "overridden"}
            >
              <FileText className="h-3.5 w-3.5" />
              Record override
            </button>
          </div>
        </div>
      )}

      <div className="mt-8">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-ink pb-3">
          <h3 className="font-display text-[26px] leading-none">Run history</h3>
          <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-secondary">
            Immutable · newest first
          </span>
        </div>
        <ol>
          {runs.map((run) => (
            <li
              key={run.id}
              className="grid gap-2 border-b border-quiet py-3 sm:grid-cols-[6rem_1fr_auto]"
            >
              <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-ink">
                Run #{run.id}
                {run.id === latestRun.id && (
                  <span className="ml-1.5 border border-ink px-1 py-0.5 text-[8px]">current</span>
                )}
              </p>
              <div>
                <p className="text-[12px] leading-relaxed text-ink">
                  {verdictText(run.verdict)} · {run.finding_count} findings ·{" "}
                  {run.finished_at ? formatDate(run.finished_at) : "in progress"}
                </p>
                <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
                  {run.engine_version}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                {reviewBadge(run.review_status)}
                {run.review_verdict && (
                  <span className="font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
                    {verdictText(run.review_verdict)}
                  </span>
                )}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

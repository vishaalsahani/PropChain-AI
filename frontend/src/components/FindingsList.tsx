import { useState } from "react";
import { AlertTriangle, Check, FileText, ShieldCheck, X } from "@/components/icons";
import { Finding, FindingReviewStatus } from "@/lib/api";
import { formatDate, humanize, severityTone } from "@/lib/presentation";

const REVIEW_LABELS: Record<FindingReviewStatus, string> = {
  open: "Awaiting review",
  confirmed: "Confirmed",
  dismissed: "Dismissed",
  needs_evidence: "Evidence requested",
};

export default function FindingsList({
  findings,
  hasRun = false,
  canReview = false,
  onReview,
}: {
  findings: Finding[];
  hasRun?: boolean;
  canReview?: boolean;
  onReview?: (
    findingId: number,
    status: FindingReviewStatus,
    note: string,
    expectedStatus: FindingReviewStatus
  ) => Promise<void>;
}) {
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function review(finding: Finding, status: FindingReviewStatus) {
    if (!onReview) return;
    const note = (notes[finding.id] ?? "").trim();
    if ((status === "dismissed" || status === "needs_evidence") && !note) {
      setError(`Add a note before marking this finding as ${REVIEW_LABELS[status].toLowerCase()}.`);
      return;
    }
    setBusy(finding.id);
    setError("");
    try {
      await onReview(finding.id, status, note, finding.status);
      setNotes((current) => ({ ...current, [finding.id]: "" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "The review could not be saved.");
    } finally {
      setBusy(null);
    }
  }

  if (!findings.length) {
    return (
      <div className="border border-quiet px-5 py-12 text-center">
        <span className="mx-auto grid h-11 w-11 place-items-center border border-ink text-ink">
          <ShieldCheck className="h-5 w-5" />
        </span>
        <p className="mt-4 font-display text-[24px] leading-none text-ink">
          {hasRun ? "No findings on this run" : "No findings yet"}
        </p>
        <p className="mx-auto mt-2 max-w-sm text-[13px] leading-relaxed text-secondary">
          {hasRun
            ? "Every selected check passed on the uploaded documents."
            : "Upload documents and run the analysis to surface inconsistencies."}
        </p>
      </div>
    );
  }

  const counts = findings.reduce<Record<string, number>>((acc, finding) => {
    acc[finding.severity] = (acc[finding.severity] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      <div className="flex flex-wrap gap-2 pb-4">
        {(["critical", "high", "medium", "low"] as const)
          .filter((severity) => (counts[severity] ?? 0) > 0)
          .map((severity) => {
            const tone = severityTone(severity);
            return (
              <span key={severity} className={tone.badge}>
                {counts[severity]} {tone.label}
              </span>
            );
          })}
      </div>

      {error && (
        <p
          role="alert"
          className="mb-4 flex items-start gap-2 border border-ink px-3.5 py-2.5 text-[12px] leading-relaxed text-ink"
        >
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          {error}
        </p>
      )}

      <div>
        {findings.map((finding) => {
          const tone = severityTone(finding.severity);
          const reviewLabel = REVIEW_LABELS[finding.status] ?? humanize(finding.status);
          const reviewed = finding.status !== "open";
          return (
            <article key={finding.id} className="relative border-t border-quiet py-5 pl-4">
              <span className={`absolute inset-y-5 left-0 w-[3px] ${tone.bar}`} />
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="max-w-[36em] font-display text-[24px] font-medium leading-[1.05] text-ink">
                    {finding.title}
                  </h3>
                  <p className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.1em] text-secondary">
                    {humanize(finding.category)}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={tone.badge}>{tone.label}</span>
                  <span
                    className={`inline-flex items-center gap-1.5 border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.08em] ${
                      reviewed ? "border-ink bg-ink text-paper" : "border-quiet text-secondary"
                    }`}
                  >
                    {finding.status === "confirmed" && <Check className="h-2.5 w-2.5" />}
                    {finding.status === "dismissed" && <X className="h-2.5 w-2.5" />}
                    {finding.status === "needs_evidence" && <FileText className="h-2.5 w-2.5" />}
                    {reviewLabel}
                  </span>
                </div>
              </div>

              <p className="mt-3 max-w-[38em] text-[14px] leading-relaxed text-secondary">
                {finding.description}
              </p>

              {finding.evidence && (
                <div className="mt-4 border-l border-ink pl-3">
                  <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-secondary">
                    Evidence
                  </p>
                  <p className="mt-1 text-[13px] leading-relaxed text-ink">{finding.evidence}</p>
                </div>
              )}

              <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[10px] text-secondary">
                {finding.rule_ref && (
                  <span className="border border-quiet px-2 py-0.5">{finding.rule_ref}</span>
                )}
                <span className="inline-flex items-center gap-2">
                  <span className="uppercase tracking-[0.08em]">Confidence</span>
                  <span className="h-1.5 w-20 border border-ink">
                    <span
                      className="block h-full bg-ink"
                      style={{ width: `${Math.round(finding.confidence * 100)}%` }}
                    />
                  </span>
                  <span className="font-medium text-ink">
                    {Math.round(finding.confidence * 100)}%
                  </span>
                </span>
              </div>

              {finding.review_note && (
                <div className="mt-4 border-t border-quiet pt-3">
                  <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-secondary">
                    Reviewer note
                    {finding.reviewed_at ? ` · ${formatDate(finding.reviewed_at)}` : ""}
                  </p>
                  <p className="mt-1 text-[12px] leading-relaxed text-ink">{finding.review_note}</p>
                </div>
              )}

              {canReview && onReview && (
                <div className="mt-4 border-t border-quiet pt-4">
                  <label
                    htmlFor={`review-note-${finding.id}`}
                    className="font-mono text-[9px] uppercase tracking-[0.1em] text-secondary"
                  >
                    Reviewer note {finding.status === "open" ? "· required to dismiss or request evidence" : "· updates this disposition"}
                  </label>
                  <textarea
                    id={`review-note-${finding.id}`}
                    className="input mt-2 min-h-[64px] text-[13px]"
                    value={notes[finding.id] ?? ""}
                    onChange={(e) =>
                      setNotes((current) => ({ ...current, [finding.id]: e.target.value }))
                    }
                    placeholder="What did you check, and what remains?"
                  />
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={busy === finding.id}
                      onClick={() => review(finding, "confirmed")}
                    >
                      <Check className="h-3 w-3" />
                      Confirm finding
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={busy === finding.id}
                      onClick={() => review(finding, "dismissed")}
                    >
                      <X className="h-3 w-3" />
                      Dismiss
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={busy === finding.id}
                      onClick={() => review(finding, "needs_evidence")}
                    >
                      <FileText className="h-3 w-3" />
                      Request evidence
                    </button>
                  </div>
                </div>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}

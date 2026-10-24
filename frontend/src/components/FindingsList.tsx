import { Finding } from "@/lib/api";
import { ShieldCheck } from "@/components/icons";
import { humanize, severityTone } from "@/lib/presentation";

export default function FindingsList({
  findings,
  hasRun = false,
}: {
  findings: Finding[];
  hasRun?: boolean;
}) {
  if (!findings.length) {
    return (
      <div className="rounded-xl border border-dashed border-ink/15 bg-white/40 px-5 py-10 text-center">
        <span className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-emerald-50 text-emerald-600">
          <ShieldCheck className="h-5 w-5" />
        </span>
        <p className="mt-3 text-sm font-medium text-slate-600">
          {hasRun ? "No findings on this run" : "No findings yet"}
        </p>
        <p className="mt-1 text-xs text-slate-400">
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
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5 pb-1">
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

      {findings.map((finding) => {
        const tone = severityTone(finding.severity);
        return (
          <article
            key={finding.id}
            className="relative overflow-hidden rounded-xl border border-ink/[0.06] bg-white/70 p-4 pl-5"
          >
            <span className={`absolute inset-y-0 left-0 w-1 ${tone.bar}`} />
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="text-sm font-semibold leading-snug text-ink">{finding.title}</h3>
                <p className="mt-1 text-[11px] uppercase tracking-[0.12em] text-slate-400">
                  {humanize(finding.category)}
                </p>
              </div>
              <span className={tone.badge}>{tone.label}</span>
            </div>

            <p className="mt-2.5 text-sm leading-relaxed text-slate-600">{finding.description}</p>

            {finding.evidence && (
              <div className="mt-3 rounded-lg border border-ink/[0.05] bg-paper/70 px-3 py-2">
                <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
                  Evidence
                </p>
                <p className="mt-0.5 text-xs leading-relaxed text-slate-600">{finding.evidence}</p>
              </div>
            )}

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-slate-400">
              {finding.rule_ref && (
                <span className="rounded-md bg-ink/[0.04] px-2 py-0.5 font-mono text-[10px] text-slate-500">
                  {finding.rule_ref}
                </span>
              )}
              <span className="inline-flex items-center gap-2">
                <span>Confidence</span>
                <span className="h-1.5 w-20 overflow-hidden rounded-full bg-ink/[0.06]">
                  <span
                    className={`block h-full rounded-full ${tone.bar}`}
                    style={{ width: `${Math.round(finding.confidence * 100)}%` }}
                  />
                </span>
                <span className="font-semibold text-slate-500">
                  {Math.round(finding.confidence * 100)}%
                </span>
              </span>
            </div>
          </article>
        );
      })}
    </div>
  );
}

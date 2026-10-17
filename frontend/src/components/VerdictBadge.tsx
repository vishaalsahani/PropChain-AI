import { VerdictOut } from "@/lib/api";

//: FR-8 verdict vocabulary -> display label + colour. Unknown/absent verdicts
//: render as "Not analysed" so the badge never guesses a risk level.
const STYLES: Record<string, { label: string; badge: string }> = {
  verified: { label: "Verified", badge: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  needs_review: { label: "Needs Review", badge: "bg-amber-100 text-amber-800 border-amber-300" },
  flagged: { label: "Flagged", badge: "bg-red-100 text-red-800 border-red-300" },
};

export default function VerdictBadge({ verdict }: { verdict: VerdictOut | null }) {
  const style = verdict?.verdict ? STYLES[verdict.verdict] : undefined;

  return (
    <div className="card">
      <p className="text-sm text-slate-500">Due-Diligence Verdict</p>
      <div className="mt-2">
        {style ? (
          <span className={`inline-block rounded-full border px-3 py-1 text-sm font-semibold ${style.badge}`}>
            {style.label}
          </span>
        ) : (
          <span className="inline-block rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-600">
            Not analysed
          </span>
        )}
      </div>

      {verdict?.reasons?.length ? (
        <ul className="mt-4 space-y-1 text-sm text-slate-700">
          {verdict.reasons.map((reason, index) => (
            <li key={index}>• {reason}</li>
          ))}
        </ul>
      ) : verdict?.verdict ? (
        <p className="mt-4 text-sm text-slate-600">
          No ownership, identity, area, encumbrance or document-integrity findings were raised.
        </p>
      ) : (
        <p className="mt-4 text-sm text-slate-600">Run the analysis to compute a verdict.</p>
      )}

      {verdict?.not_checked?.length ? (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs font-medium text-slate-500">
            Not checked ({verdict.not_checked.length})
          </summary>
          <ul className="mt-2 space-y-1 text-xs text-slate-500">
            {verdict.not_checked.map((item, index) => (
              <li key={index}>• {item}</li>
            ))}
          </ul>
        </details>
      ) : null}

      <p className="mt-3 text-xs text-slate-500">
        Screening verdict from the automated checks and the rule pack. Findings are indicators for a
        reviewer, not legal determinations.
      </p>
    </div>
  );
}

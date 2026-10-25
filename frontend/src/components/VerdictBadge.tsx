import { VerdictOut } from "@/lib/api";
import { Flag, ShieldAlert, ShieldCheck } from "@/components/icons";

type VerdictConfig = {
  label: string;
  sub: string;
  icon: typeof ShieldCheck;
  inverted: boolean;
};

const VERDICTS: Record<string, VerdictConfig> = {
  verified: {
    label: "Verified",
    sub: "No blocking inconsistencies were found in the uploaded documents.",
    icon: ShieldCheck,
    inverted: false,
  },
  needs_review: {
    label: "Needs review",
    sub: "Some items could not be cleared automatically. A reviewer should confirm them.",
    icon: ShieldAlert,
    inverted: true,
  },
  flagged: {
    label: "Flagged",
    sub: "A significant finding or an ownership gap needs attention before proceeding.",
    icon: Flag,
    inverted: true,
  },
};

const EMPTY: VerdictConfig = {
  label: "Not analysed",
  sub: "Run the analysis to compute a verdict from the uploaded documents.",
  icon: ShieldAlert,
  inverted: false,
};

export default function VerdictBadge({ verdict }: { verdict: VerdictOut | null }) {
  const config = (verdict?.verdict && VERDICTS[verdict.verdict]) || EMPTY;
  const Icon = config.icon;
  const reasons = verdict?.reasons ?? [];
  const notChecked = verdict?.not_checked ?? [];

  return (
    <section className="border border-ink">
      <div
        className={`p-5 ${
          config.inverted ? "bg-ink text-paper" : "bg-paper text-ink"
        }`}
      >
        <div className="flex items-start justify-between gap-3">
          <span className="grid h-10 w-10 place-items-center border border-current">
            <Icon className="h-5 w-5" />
          </span>
          <span
            className={`border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.1em] ${
              config.inverted ? "border-quiet-inverted text-quiet" : "border-ink text-ink"
            }`}
          >
            Screening verdict
          </span>
        </div>

        <p
          className={`mt-5 font-mono text-[10px] uppercase tracking-[0.12em] ${
            config.inverted ? "text-quiet" : "text-secondary"
          }`}
        >
          Due-diligence verdict
        </p>
        <h2
          className={`mt-1 font-display text-[34px] font-medium leading-none tracking-[-0.03em] ${
            config.inverted ? "text-paper" : "text-ink"
          }`}
        >
          {config.label}
        </h2>
        <p
          className={`mt-3 max-w-[34em] text-[14px] leading-relaxed ${
            config.inverted ? "text-quiet" : "text-secondary"
          }`}
        >
          {config.sub}
        </p>
      </div>

      <div className="space-y-5 p-5">
        {reasons.length > 0 ? (
          <div>
            <p className="eyebrow text-ink">Why</p>
            <ul className="mt-3 space-y-2.5">
              {reasons.map((reason, index) => (
                <li
                  key={index}
                  className="flex gap-2.5 text-[13px] leading-relaxed text-secondary"
                >
                  <span className="mt-[0.6em] h-1.5 w-1.5 shrink-0 bg-ink" />
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : verdict?.verdict ? (
          <p className="text-[13px] leading-relaxed text-secondary">
            No ownership, identity, area, encumbrance or document-integrity findings were raised.
          </p>
        ) : (
          <p className="text-[13px] leading-relaxed text-secondary">
            The verdict appears after the first analysis run.
          </p>
        )}

        {notChecked.length > 0 && (
          <details className="group border-t border-quiet pt-4">
            <summary className="flex cursor-pointer items-center justify-between gap-2 text-[12px] font-medium text-ink">
              <span className="inline-flex items-center gap-2">
                Not checked
                <span className="border border-quiet px-1.5 py-0.5 font-mono text-[10px] text-secondary">
                  {notChecked.length}
                </span>
              </span>
              <span aria-hidden className="text-lg leading-none">
                <span className="group-open:hidden">+</span>
                <span className="hidden group-open:inline">−</span>
              </span>
            </summary>
            <ul className="mt-3 space-y-2">
              {notChecked.map((item, index) => (
                <li
                  key={index}
                  className="flex gap-2 text-[12px] leading-relaxed text-secondary"
                >
                  <span className="mt-[0.6em] h-1 w-1 shrink-0 bg-secondary" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </details>
        )}

        <div className="border-t border-quiet pt-4">
          {verdict?.engine_version && (
            <p
              className="break-all font-mono text-[10px] leading-relaxed text-secondary"
              title="Engine tag for this run"
            >
              {verdict.engine_version}
            </p>
          )}
          <p className="mt-2 font-mono text-[10px] leading-relaxed text-secondary">
            Findings are indicators for a reviewer, not legal determinations.
          </p>
        </div>
      </div>
    </section>
  );
}

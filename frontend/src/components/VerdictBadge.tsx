import { VerdictOut } from "@/lib/api";
import {
  ChevronDown,
  Flag,
  ShieldAlert,
  ShieldCheck,
} from "@/components/icons";

type VerdictConfig = {
  label: string;
  sub: string;
  icon: typeof ShieldCheck;
  header: string;
  iconWrap: string;
  title: string;
  badge: string;
  dot: string;
};

const VERDICTS: Record<string, VerdictConfig> = {
  verified: {
    label: "Verified",
    sub: "No blocking inconsistencies were found in the uploaded documents.",
    icon: ShieldCheck,
    header: "from-emerald-50 via-emerald-50/60 to-white",
    iconWrap: "bg-emerald-600 text-white",
    title: "text-emerald-950",
    badge: "bg-emerald-600/10 text-emerald-800 ring-1 ring-inset ring-emerald-600/20",
    dot: "bg-emerald-500",
  },
  needs_review: {
    label: "Needs review",
    sub: "Some items could not be cleared automatically. A reviewer should confirm them.",
    icon: ShieldAlert,
    header: "from-amber-50 via-amber-50/60 to-white",
    iconWrap: "bg-amber-500 text-white",
    title: "text-amber-950",
    badge: "bg-amber-500/10 text-amber-800 ring-1 ring-inset ring-amber-600/20",
    dot: "bg-amber-500",
  },
  flagged: {
    label: "Flagged",
    sub: "A significant finding or an ownership gap needs attention before proceeding.",
    icon: Flag,
    header: "from-rose-50 via-rose-50/60 to-white",
    iconWrap: "bg-rose-500 text-white",
    title: "text-rose-950",
    badge: "bg-rose-500/10 text-rose-800 ring-1 ring-inset ring-rose-600/20",
    dot: "bg-rose-500",
  },
};

const EMPTY: VerdictConfig = {
  label: "Not analysed",
  sub: "Run the analysis to compute a verdict from the uploaded documents.",
  icon: ShieldAlert,
  header: "from-slate-50 to-white",
  iconWrap: "bg-slate-100 text-slate-500",
  title: "text-slate-700",
  badge: "bg-slate-500/10 text-slate-600 ring-1 ring-inset ring-slate-500/15",
  dot: "bg-slate-400",
};

export default function VerdictBadge({ verdict }: { verdict: VerdictOut | null }) {
  const config = (verdict?.verdict && VERDICTS[verdict.verdict]) || EMPTY;
  const Icon = config.icon;
  const reasons = verdict?.reasons ?? [];
  const notChecked = verdict?.not_checked ?? [];

  return (
    <section className="overflow-hidden rounded-2xl border border-ink/[0.06] bg-white/80 shadow-soft backdrop-blur-sm">
      <div className={`bg-gradient-to-br p-5 ${config.header}`}>
        <div className="flex items-start justify-between gap-3">
          <span className={`grid h-10 w-10 place-items-center rounded-xl ${config.iconWrap}`}>
            <Icon className="h-5 w-5" />
          </span>
          <span className={`${config.badge} inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.1em]`}>
            <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
            Screening verdict
          </span>
        </div>

        <p className="mt-4 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          Due-diligence verdict
        </p>
        <h2 className={`mt-1 text-[26px] font-medium leading-tight ${config.title}`}>{config.label}</h2>
        <p className="mt-1.5 text-xs leading-relaxed text-slate-600">{config.sub}</p>
      </div>

      <div className="space-y-4 p-5">
        {reasons.length > 0 ? (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              Why
            </p>
            <ul className="mt-2 space-y-2">
              {reasons.map((reason, index) => (
                <li key={index} className="flex gap-2 text-xs leading-relaxed text-slate-600">
                  <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${config.dot}`} />
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : verdict?.verdict ? (
          <p className="text-xs leading-relaxed text-slate-500">
            No ownership, identity, area, encumbrance or document-integrity findings were raised.
          </p>
        ) : (
          <p className="text-xs leading-relaxed text-slate-500">
            The verdict appears after the first analysis run.
          </p>
        )}

        {notChecked.length > 0 && (
          <details className="group rounded-xl border border-ink/[0.06] bg-paper/60 px-3.5 py-3">
            <summary className="flex cursor-pointer items-center justify-between gap-2 text-[11px] font-semibold text-slate-600">
              <span className="inline-flex items-center gap-1.5">
                Not checked
                <span className="rounded-full bg-white px-1.5 py-0.5 text-[10px] font-bold text-slate-500 ring-1 ring-inset ring-ink/10">
                  {notChecked.length}
                </span>
              </span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-400 transition group-open:rotate-180" />
            </summary>
            <ul className="mt-2.5 space-y-1.5">
              {notChecked.map((item, index) => (
                <li key={index} className="flex gap-1.5 text-[11px] leading-relaxed text-slate-500">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-300" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </details>
        )}

        <div className="border-t border-ink/[0.06] pt-3">
          {verdict?.engine_version && (
            <p className="break-all font-mono text-[9px] leading-relaxed text-slate-400" title="Engine tag for this run">
              {verdict.engine_version}
            </p>
          )}
          <p className="mt-2 text-[10px] leading-relaxed text-slate-400">
            Findings are indicators for a reviewer, not legal determinations.
          </p>
        </div>
      </div>
    </section>
  );
}

import { riskTone } from "@/lib/presentation";

export default function RiskIndicator({ score }: { score: number | null }) {
  const tone = riskTone(score);
  const value = score === null ? null : Math.min(Math.max(score, 0), 100);
  const percent = value ?? 0;
  const radius = 52;
  const circumference = 2 * Math.PI * radius;

  return (
    <section className="card">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold">Risk indicator</h2>
        <span className="chip text-[10px] uppercase tracking-wide">Project-defined</span>
      </div>

      <div className="mt-4 flex items-center gap-5">
        <div className="relative h-[116px] w-[116px] shrink-0">
          <svg viewBox="0 0 128 128" className="h-full w-full" role="img" aria-label={`Risk score ${value ?? "not available"}`}>
            <circle cx="64" cy="64" r={radius} fill="none" stroke="#ece7db" strokeWidth="10" />
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke={tone.stroke}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - percent / 100)}
              transform="rotate(-90 64 64)"
              className="transition-all duration-700"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-display text-[30px] leading-none text-ink">
              {value === null ? "—" : Math.round(value)}
            </span>
            <span className="mt-1 text-[9px] font-semibold uppercase tracking-[0.14em] text-slate-400">
              of 100
            </span>
          </div>
        </div>

        <div className="min-w-0">
          <p className={`inline-flex items-center gap-1.5 text-sm font-semibold ${tone.text}`}>
            <span className={`h-2 w-2 rounded-full ${tone.bar}`} />
            {tone.label}
          </p>
          <p className="mt-1.5 text-xs leading-relaxed text-slate-500">
            {value === null
              ? "Run the analysis to compute a risk indicator for this file."
              : "Weighted from finding severity and confidence, plus any ownership gaps."}
          </p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-1.5 border-t border-ink/[0.06] pt-3">
        {[
          { label: "Low", range: "0–39", dot: "bg-emerald-500" },
          { label: "Moderate", range: "40–69", dot: "bg-amber-500" },
          { label: "High", range: "70–100", dot: "bg-rose-500" },
        ].map((band) => (
          <div key={band.label} className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className={`h-1.5 w-1.5 rounded-full ${band.dot}`} />
            <span className="font-medium text-slate-500">{band.label}</span>
            <span>{band.range}</span>
          </div>
        ))}
      </div>

      <p className="mt-3 text-[10px] leading-relaxed text-slate-400">
        Not a legal conclusion — a screening indicator for a reviewer.
      </p>
    </section>
  );
}

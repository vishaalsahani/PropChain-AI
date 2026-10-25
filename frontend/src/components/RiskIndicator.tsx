import { riskTone } from "@/lib/presentation";

export default function RiskIndicator({ score }: { score: number | null }) {
  const tone = riskTone(score);
  const value = score === null ? null : Math.min(Math.max(score, 0), 100);
  const percent = value ?? 0;

  return (
    <section className="border border-ink p-5">
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-display text-[24px] leading-none">Risk indicator</h2>
        <span className="border border-quiet px-2 py-1 font-mono text-[9px] uppercase tracking-[0.1em] text-secondary">
          Project-defined
        </span>
      </div>

      <div className="mt-6 flex items-end justify-between gap-4">
        <div>
          <p className="font-display text-[clamp(52px,5.8cqw,84px)] leading-none tracking-[-0.04em] text-ink">
            {value === null ? "—" : Math.round(value)}
          </p>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.12em] text-secondary">
            of 100
          </p>
        </div>
        <p className="mb-1 text-right font-mono text-[10px] uppercase tracking-[0.1em] text-ink">
          {tone.label}
        </p>
      </div>

      <div className="mt-5" role="img" aria-label={`Risk score ${value ?? "not available"}`}>
        <div className="h-3 w-full border border-ink">
          <div className={`h-full ${tone.bar}`} style={{ width: `${percent}%` }} />
        </div>
        <div className="mt-2 flex justify-between font-mono text-[9px] uppercase tracking-[0.08em] text-secondary">
          <span>0</span>
          <span>100</span>
        </div>
      </div>

      <p className="mt-4 text-[12px] leading-relaxed text-secondary">
        {value === null
          ? "Run the analysis to compute a risk indicator for this file."
          : "Weighted from finding severity and confidence, plus any ownership gaps."}
      </p>

      <div className="mt-5 grid grid-cols-3 border-t border-quiet pt-3">
        {[
          { label: "Low", range: "0–39" },
          { label: "Moderate", range: "40–69" },
          { label: "High", range: "70–100" },
        ].map((band) => (
          <div
            key={band.label}
            className="border-l border-quiet pl-2 first:border-l-0 first:pl-0"
          >
            <p className="font-mono text-[9px] uppercase tracking-[0.08em] text-ink">
              {band.label}
            </p>
            <p className="mt-0.5 font-mono text-[9px] text-secondary">{band.range}</p>
          </div>
        ))}
      </div>

      <p className="mt-4 border-t border-quiet pt-3 font-mono text-[9px] uppercase leading-relaxed tracking-[0.08em] text-secondary">
        Not a legal conclusion — a screening indicator for a reviewer.
      </p>
    </section>
  );
}

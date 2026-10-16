export default function RiskIndicator({ score }: { score: number | null }) {
  const value = score ?? 0;
  const color = value >= 70 ? "bg-red-500" : value >= 40 ? "bg-amber-500" : "bg-emerald-500";
  const label = value >= 70 ? "High Risk" : value >= 40 ? "Moderate Risk" : "Low Risk";

  return (
    <div className="card">
      <p className="text-sm text-slate-500">Risk Indicator</p>
      <div className="mt-2 flex items-end gap-3">
        <span className="text-3xl font-bold">{value.toFixed(0)}</span>
        <span className="mb-1 text-sm font-medium text-slate-600">{label}</span>
      </div>
      <div className="mt-4 h-2 rounded-full bg-slate-200">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <p className="mt-3 text-xs text-slate-500">
        Project-defined indicator based on finding severity and confidence. Not a legal conclusion.
      </p>
    </div>
  );
}

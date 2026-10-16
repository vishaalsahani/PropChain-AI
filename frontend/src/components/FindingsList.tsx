import { Finding } from "@/lib/api";

const severityStyles: Record<Finding["severity"], string> = {
  low: "bg-emerald-100 text-emerald-800",
  medium: "bg-amber-100 text-amber-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

export default function FindingsList({ findings }: { findings: Finding[] }) {
  if (!findings.length) {
    return <p className="text-sm text-slate-500">No findings yet. Run analysis after uploading documents.</p>;
  }

  return (
    <div className="space-y-3">
      {findings.map((finding) => (
        <div key={finding.id} className="rounded-lg border border-slate-200 p-4">
          <div className="mb-2 flex items-center justify-between gap-2">
            <h4 className="font-medium">{finding.title}</h4>
            <span className={`badge ${severityStyles[finding.severity]}`}>{finding.severity}</span>
          </div>
          <p className="text-sm text-slate-600">{finding.description}</p>
          <div className="mt-2 text-xs text-slate-500">
            {finding.rule_ref && <span>Rule: {finding.rule_ref} · </span>}
            Confidence: {(finding.confidence * 100).toFixed(0)}%
          </div>
          {finding.evidence && <p className="mt-1 text-xs text-slate-500">Evidence: {finding.evidence}</p>}
        </div>
      ))}
    </div>
  );
}

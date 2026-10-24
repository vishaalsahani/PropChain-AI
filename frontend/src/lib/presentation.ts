//: Shared presentation tokens. Keeping the full class strings here (instead of
//: building them dynamically) means Tailwind's scanner can see every variant.

export type StatusTone = {
  label: string;
  badge: string;
  dot: string;
  accent: string;
};

const STATUS_BASE =
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset";

const PROPERTY_STATUS: Record<string, StatusTone> = {
  draft: {
    label: "Draft",
    badge: `${STATUS_BASE} bg-slate-50 text-slate-600 ring-slate-500/15`,
    dot: "bg-slate-400",
    accent: "bg-slate-300",
  },
  analyzing: {
    label: "Analyzing",
    badge: `${STATUS_BASE} bg-sky-50 text-sky-700 ring-sky-600/15`,
    dot: "bg-sky-500",
    accent: "bg-sky-400",
  },
  analyzed: {
    label: "Analyzed",
    badge: `${STATUS_BASE} bg-emerald-50 text-emerald-700 ring-emerald-600/15`,
    dot: "bg-emerald-500",
    accent: "bg-emerald-400",
  },
  needs_review: {
    label: "Needs review",
    badge: `${STATUS_BASE} bg-amber-50 text-amber-700 ring-amber-600/20`,
    dot: "bg-amber-500",
    accent: "bg-amber-400",
  },
  flagged: {
    label: "Flagged",
    badge: `${STATUS_BASE} bg-rose-50 text-rose-700 ring-rose-600/15`,
    dot: "bg-rose-500",
    accent: "bg-rose-400",
  },
};

export function propertyStatus(status: string | null | undefined): StatusTone {
  if (!status) {
    return {
      label: "Unknown",
      badge: `${STATUS_BASE} bg-slate-50 text-slate-600 ring-slate-500/15`,
      dot: "bg-slate-400",
      accent: "bg-slate-300",
    };
  }
  return (
    PROPERTY_STATUS[status] ?? {
      label: humanize(status),
      badge: `${STATUS_BASE} bg-slate-50 text-slate-600 ring-slate-500/15`,
      dot: "bg-slate-400",
      accent: "bg-slate-300",
    }
  );
}

const DOC_STATUS: Record<string, { label: string; badge: string; dot: string }> = {
  pending: {
    label: "Queued",
    badge: `${STATUS_BASE} bg-slate-50 text-slate-600 ring-slate-500/15`,
    dot: "bg-slate-400",
  },
  processing: {
    label: "Processing",
    badge: `${STATUS_BASE} bg-sky-50 text-sky-700 ring-sky-600/15`,
    dot: "bg-sky-500",
  },
  completed: {
    label: "Processed",
    badge: `${STATUS_BASE} bg-emerald-50 text-emerald-700 ring-emerald-600/15`,
    dot: "bg-emerald-500",
  },
  failed: {
    label: "Failed",
    badge: `${STATUS_BASE} bg-rose-50 text-rose-700 ring-rose-600/15`,
    dot: "bg-rose-500",
  },
};

export function documentStatus(status: string | null | undefined) {
  if (!status) return DOC_STATUS.pending;
  return DOC_STATUS[status] ?? { ...DOC_STATUS.pending, label: humanize(status) };
}

export type SeverityTone = {
  label: string;
  badge: string;
  bar: string;
  text: string;
};

const SEVERITY_BASE = "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ring-1 ring-inset";

const SEVERITY: Record<string, SeverityTone> = {
  low: {
    label: "Low",
    badge: `${SEVERITY_BASE} bg-emerald-50 text-emerald-700 ring-emerald-600/20`,
    bar: "bg-emerald-400",
    text: "text-emerald-700",
  },
  medium: {
    label: "Medium",
    badge: `${SEVERITY_BASE} bg-amber-50 text-amber-700 ring-amber-600/20`,
    bar: "bg-amber-400",
    text: "text-amber-700",
  },
  high: {
    label: "High",
    badge: `${SEVERITY_BASE} bg-orange-50 text-orange-700 ring-orange-600/20`,
    bar: "bg-orange-400",
    text: "text-orange-700",
  },
  critical: {
    label: "Critical",
    badge: `${SEVERITY_BASE} bg-rose-50 text-rose-700 ring-rose-600/20`,
    bar: "bg-rose-500",
    text: "text-rose-700",
  },
};

export function severityTone(severity: string): SeverityTone {
  return SEVERITY[severity] ?? SEVERITY.low;
}

export function humanize(value: string): string {
  if (!value) return "Unknown";
  const special: Record<string, string> = {
    RERA: "RERA",
    mh_pack: "MH pack",
    mh_v1: "MH v1",
    cts: "CTS",
    ec: "EC",
    gat: "Gat",
    sqft: "sq ft",
    needs_review: "Needs review",
  };
  if (special[value]) return special[value];
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateShort(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function shortHash(hash: string | null | undefined, head = 10, tail = 6): string {
  if (!hash) return "—";
  if (hash.length <= head + tail + 1) return hash;
  return `${hash.slice(0, head)}…${hash.slice(-tail)}`;
}

export function formatArea(area: number | null | undefined): string {
  if (area === null || area === undefined) return "—";
  return `${area.toLocaleString("en-IN", { maximumFractionDigits: 0 })} sq ft`;
}

export function riskTone(score: number | null | undefined) {
  if (score === null || score === undefined) {
    return { label: "Not scored", bar: "bg-slate-300", text: "text-slate-500", stroke: "#cbd5e1" };
  }
  if (score >= 70) return { label: "High risk", bar: "bg-rose-500", text: "text-rose-600", stroke: "#f43f5e" };
  if (score >= 40) return { label: "Moderate risk", bar: "bg-amber-500", text: "text-amber-600", stroke: "#f59e0b" };
  return { label: "Low risk", bar: "bg-emerald-500", text: "text-emerald-600", stroke: "#10b981" };
}

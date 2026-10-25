// Shared presentation tokens. Keeping the full class strings here (instead of
// building them dynamically) means Tailwind's scanner can see every variant.

export type StatusTone = {
  label: string;
  badge: string;
  dot: string;
  accent: string;
};

const STATUS_BASE =
  "inline-flex items-center gap-1.5 border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.1em]";

const PROPERTY_STATUS: Record<string, StatusTone> = {
  draft: {
    label: "Draft",
    badge: `${STATUS_BASE} border-quiet text-secondary`,
    dot: "bg-quiet",
    accent: "bg-quiet",
  },
  analyzing: {
    label: "Analyzing",
    badge: `${STATUS_BASE} border-ink text-ink`,
    dot: "bg-ink",
    accent: "bg-ink",
  },
  analyzed: {
    label: "Analyzed",
    badge: `${STATUS_BASE} border-ink text-ink`,
    dot: "bg-ink",
    accent: "bg-ink",
  },
  needs_review: {
    label: "Needs review",
    badge: `${STATUS_BASE} border-ink bg-ink text-paper`,
    dot: "bg-paper",
    accent: "bg-ink",
  },
  flagged: {
    label: "Flagged",
    badge: `${STATUS_BASE} border-ink bg-ink text-paper`,
    dot: "bg-paper",
    accent: "bg-ink",
  },
};

export function propertyStatus(status: string | null | undefined): StatusTone {
  if (!status) {
    return {
      label: "Unknown",
      badge: `${STATUS_BASE} border-quiet text-secondary`,
      dot: "bg-quiet",
      accent: "bg-quiet",
    };
  }
  return (
    PROPERTY_STATUS[status] ?? {
      label: humanize(status),
      badge: `${STATUS_BASE} border-quiet text-secondary`,
      dot: "bg-quiet",
      accent: "bg-quiet",
    }
  );
}

const DOC_STATUS: Record<string, { label: string; badge: string; dot: string }> = {
  pending: {
    label: "Queued",
    badge: `${STATUS_BASE} border-quiet text-secondary`,
    dot: "bg-quiet",
  },
  processing: {
    label: "Processing",
    badge: `${STATUS_BASE} border-ink text-ink`,
    dot: "bg-ink",
  },
  completed: {
    label: "Processed",
    badge: `${STATUS_BASE} border-ink bg-ink text-paper`,
    dot: "bg-paper",
  },
  failed: {
    label: "Failed",
    badge: `${STATUS_BASE} border-ink text-ink`,
    dot: "bg-ink",
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

const SEVERITY_BASE =
  "inline-flex items-center border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.1em]";

const SEVERITY: Record<string, SeverityTone> = {
  low: {
    label: "Low",
    badge: `${SEVERITY_BASE} border-quiet text-secondary`,
    bar: "bg-quiet",
    text: "text-secondary",
  },
  medium: {
    label: "Medium",
    badge: `${SEVERITY_BASE} border-ink text-ink`,
    bar: "bg-ink",
    text: "text-ink",
  },
  high: {
    label: "High",
    badge: `${SEVERITY_BASE} border-ink bg-ink text-paper`,
    bar: "bg-ink",
    text: "text-ink",
  },
  critical: {
    label: "Critical",
    badge: `${SEVERITY_BASE} border-2 border-ink bg-ink text-paper`,
    bar: "bg-ink",
    text: "text-ink",
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
    return {
      label: "Not scored",
      bar: "bg-quiet",
      text: "text-secondary",
      stroke: "#cfcfcf",
    };
  }
  if (score >= 70) {
    return {
      label: "High risk",
      bar: "bg-ink",
      text: "text-ink",
      stroke: "#000000",
    };
  }
  if (score >= 40) {
    return {
      label: "Moderate risk",
      bar: "bg-ink",
      text: "text-ink",
      stroke: "#000000",
    };
  }
  return {
    label: "Low risk",
    bar: "bg-ink",
    text: "text-ink",
    stroke: "#000000",
  };
}

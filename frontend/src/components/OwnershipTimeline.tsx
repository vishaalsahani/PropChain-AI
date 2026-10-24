import { OwnershipNode } from "@/lib/api";
import { AlertTriangle, ArrowRight, Link2 } from "@/components/icons";
import { formatDate, humanize } from "@/lib/presentation";

export default function OwnershipTimeline({ nodes }: { nodes: OwnershipNode[] }) {
  if (!nodes.length) {
    return (
      <div className="rounded-xl border border-dashed border-ink/15 bg-white/40 px-5 py-10 text-center">
        <Link2 className="mx-auto h-7 w-7 text-slate-300" />
        <p className="mt-3 text-sm font-medium text-slate-600">No chain yet</p>
        <p className="mt-1 text-xs text-slate-400">
          The ownership chain is traced during the analysis.
        </p>
      </div>
    );
  }

  return (
    <ol className="relative">
      <span aria-hidden className="absolute bottom-4 left-4 top-4 w-px bg-ink/10" />
      {nodes.map((node) => {
        const gap = Boolean(node.gap_flag);
        return (
          <li key={node.id} className="relative pb-4 pl-11 last:pb-0">
            <span
              className={`absolute left-0 top-0 grid h-8 w-8 place-items-center rounded-full text-[11px] font-bold ring-4 ring-paper ${
                gap ? "bg-rose-500 text-white" : "bg-brand-900 text-white"
              }`}
            >
              {gap ? <AlertTriangle className="h-4 w-4" /> : node.sequence}
            </span>

            <div
              className={`rounded-xl border p-3.5 ${
                gap
                  ? "border-rose-200 bg-rose-50/70"
                  : "border-ink/[0.06] bg-white/70"
              }`}
            >
              <div className="flex flex-wrap items-center gap-1.5 text-sm font-semibold text-ink">
                {node.from_party ? (
                  <>
                    <span className="truncate">{node.from_party}</span>
                    <ArrowRight className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                    <span className="truncate">{node.person_name}</span>
                  </>
                ) : (
                  <>
                    <span className="truncate">{node.person_name}</span>
                    <span className="rounded-full bg-brand-50 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-brand-700 ring-1 ring-inset ring-brand-600/15">
                      Root record
                    </span>
                  </>
                )}
              </div>

              <p className="mt-1 text-xs text-slate-500">
                {humanize(node.transaction_type)}
                {node.transaction_date ? ` · ${formatDate(node.transaction_date)}` : ""}
              </p>

              {node.document_ref && (
                <p className="mt-2 break-all font-mono text-[10px] text-slate-400">
                  Ref: {node.document_ref}
                </p>
              )}

              {gap && (
                <p className="mt-2.5 flex items-start gap-1.5 rounded-lg bg-white/70 px-2.5 py-1.5 text-[11px] leading-relaxed text-rose-700">
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                  Gap: the transferor is not evidenced by an uploaded document.
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

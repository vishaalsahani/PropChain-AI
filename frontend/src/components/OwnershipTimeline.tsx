import { OwnershipNode } from "@/lib/api";
import { AlertTriangle, ArrowRight, Link2 } from "@/components/icons";
import { formatDate, humanize } from "@/lib/presentation";

export default function OwnershipTimeline({ nodes }: { nodes: OwnershipNode[] }) {
  if (!nodes.length) {
    return (
      <div className="border border-quiet px-5 py-12 text-center">
        <Link2 className="mx-auto h-7 w-7 text-secondary" />
        <p className="mt-4 font-display text-[24px] leading-none text-ink">No chain yet</p>
        <p className="mx-auto mt-2 max-w-sm text-[13px] leading-relaxed text-secondary">
          The ownership chain is traced during the analysis.
        </p>
      </div>
    );
  }

  return (
    <ol className="relative">
      <span
        aria-hidden
        className="absolute bottom-5 left-[15px] top-5 w-px bg-quiet"
      />
      {nodes.map((node) => {
        const gap = Boolean(node.gap_flag);
        return (
          <li key={node.id} className="relative pb-6 pl-12 last:pb-0">
            <span
              className={`absolute left-0 top-0 grid h-8 w-8 place-items-center border font-mono text-[10px] ${
                gap
                  ? "border-ink bg-ink text-paper"
                  : "border-ink bg-paper text-ink"
              }`}
            >
              {gap ? <AlertTriangle className="h-4 w-4" /> : node.sequence}
            </span>

            <div className="border-t border-quiet py-3">
              <div className="flex flex-wrap items-center gap-2 font-display text-[20px] font-medium leading-tight text-ink">
                {node.from_party ? (
                  <>
                    <span className="truncate">{node.from_party}</span>
                    <ArrowRight className="h-3.5 w-3.5 shrink-0 text-secondary" />
                    <span className="truncate">{node.person_name}</span>
                  </>
                ) : (
                  <>
                    <span className="truncate">{node.person_name}</span>
                    <span className="border border-quiet px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-[0.08em] text-secondary">
                      Root record
                    </span>
                  </>
                )}
              </div>

              <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                {humanize(node.transaction_type)}
                {node.transaction_date ? ` · ${formatDate(node.transaction_date)}` : ""}
              </p>

              {node.document_ref && (
                <p className="mt-2 break-all font-mono text-[10px] text-secondary">
                  Ref: {node.document_ref}
                </p>
              )}

              {gap && (
                <p className="mt-3 flex items-start gap-2 border-l border-ink pl-2.5 text-[12px] leading-relaxed text-ink">
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                  <span>
                    <span className="font-mono text-[10px] uppercase tracking-[0.08em]">Gap</span>{" "}
                    — the transferor is not evidenced by an uploaded document.
                  </span>
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

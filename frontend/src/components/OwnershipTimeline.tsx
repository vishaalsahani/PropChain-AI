import { OwnershipNode } from "@/lib/api";

export default function OwnershipTimeline({ nodes }: { nodes: OwnershipNode[] }) {
  if (!nodes.length) {
    return <p className="text-sm text-slate-500">Ownership chain will appear after analysis.</p>;
  }

  return (
    <ol className="relative space-y-4 border-l border-slate-300 pl-6">
      {nodes.map((node) => (
        <li key={node.id} className="relative">
          <span
            className={`absolute -left-[1.95rem] top-1 h-3 w-3 rounded-full ${
              node.gap_flag ? "bg-red-500" : "bg-brand-700"
            }`}
          />
          <div className={`rounded-lg border p-3 ${node.gap_flag ? "border-red-300 bg-red-50" : "border-slate-200"}`}>
            <p className="font-medium">
              {node.from_party ? `${node.from_party} → ${node.person_name}` : node.person_name}
            </p>
            <p className="text-sm text-slate-600">
              {node.transaction_type} · {node.transaction_date}
            </p>
            {node.document_ref && <p className="mt-1 text-xs text-slate-500">Ref: {node.document_ref}</p>}
            {node.gap_flag && (
              <p className="mt-2 inline-block rounded border border-red-300 bg-white px-2 py-0.5 text-xs font-medium text-red-700">
                Gap: transferor not evidenced by an uploaded document
              </p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}

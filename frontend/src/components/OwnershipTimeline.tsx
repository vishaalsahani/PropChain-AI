import { OwnershipNode } from "@/lib/api";

export default function OwnershipTimeline({ nodes }: { nodes: OwnershipNode[] }) {
  if (!nodes.length) {
    return <p className="text-sm text-slate-500">Ownership chain will appear after analysis.</p>;
  }

  return (
    <ol className="relative space-y-4 border-l border-slate-300 pl-6">
      {nodes.map((node) => (
        <li key={node.id} className="relative">
          <span className="absolute -left-[1.95rem] top-1 h-3 w-3 rounded-full bg-brand-700" />
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="font-medium">{node.person_name}</p>
            <p className="text-sm text-slate-600">
              {node.transaction_type} · {node.transaction_date}
            </p>
            {node.document_ref && <p className="mt-1 text-xs text-slate-500">Ref: {node.document_ref}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}

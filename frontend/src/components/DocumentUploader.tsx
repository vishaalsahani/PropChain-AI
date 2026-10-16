"use client";

import { useState } from "react";
import { api, DocumentItem } from "@/lib/api";

export default function DocumentUploader({
  propertyId,
  onUploaded,
}: {
  propertyId: number;
  onUploaded: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      await api.uploadDocument(propertyId, file);
      onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  }

  return (
    <div className="card">
      <h3 className="mb-2 font-semibold">Upload Document</h3>
      <p className="mb-4 text-sm text-slate-500">Supported: PDF, JPG, JPEG, PNG</p>
      <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={handleUpload} disabled={loading} />
      {loading && <p className="mt-2 text-sm text-brand-700">Processing document...</p>}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}

export function DocumentList({
  documents,
  onAction,
}: {
  documents: DocumentItem[];
  onAction: () => void;
}) {
  async function register(id: number) {
    await api.registerBlockchain(id);
    onAction();
  }

  async function verify(id: number) {
    await api.verifyBlockchain(id);
    onAction();
  }

  if (!documents.length) {
    return <p className="text-sm text-slate-500">No documents uploaded yet.</p>;
  }

  return (
    <div className="space-y-3">
      {documents.map((doc) => (
        <div key={doc.id} className="rounded-lg border border-slate-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="font-medium">{doc.filename}</p>
              <p className="text-xs text-slate-500">
                {doc.doc_type} · {doc.status}
              </p>
            </div>
            <div className="flex gap-2">
              <button className="btn-secondary" onClick={() => register(doc.id)}>
                Register Hash
              </button>
              <button className="btn-secondary" onClick={() => verify(doc.id)}>
                Verify
              </button>
            </div>
          </div>
          <p className="mt-2 break-all text-xs text-slate-500">SHA-256: {doc.file_hash}</p>
          {doc.blockchain_tx && (
            <p className="text-xs text-emerald-700">Blockchain TX: {doc.blockchain_tx}</p>
          )}
        </div>
      ))}
    </div>
  );
}

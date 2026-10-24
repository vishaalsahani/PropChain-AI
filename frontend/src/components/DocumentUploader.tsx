"use client";

import { useRef, useState } from "react";
import {
  AlertTriangle,
  Check,
  Copy,
  FileText,
  Hash,
  Link2,
  Lock,
  ShieldCheck,
  Spinner,
  UploadCloud,
} from "@/components/icons";
import { api, DocumentItem } from "@/lib/api";
import { documentStatus, formatDate, humanize, shortHash } from "@/lib/presentation";

const MAX_MB = 25;

export default function DocumentUploader({
  propertyId,
  onUploaded,
}: {
  propertyId: number;
  onUploaded: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");

  async function upload(file: File) {
    if (!/\.(pdf|jpe?g|png)$/i.test(file.name)) {
      setError("Accepted formats are PDF, JPG, JPEG and PNG.");
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`The file is larger than the ${MAX_MB} MB limit.`);
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.uploadDocument(propertyId, file);
      await onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) upload(file);
  }

  function openPicker() {
    if (!loading) inputRef.current?.click();
  }

  return (
    <section className="card">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold">Upload documents</h2>
          <p className="mt-0.5 text-xs text-slate-400">
            Add the deed set for this property — one file at a time.
          </p>
        </div>
        <span className="chip text-[10px] uppercase tracking-wide">PDF · JPG · PNG</span>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={handleInput}
        disabled={loading}
        className="sr-only"
        id="document-upload"
      />

      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a document"
        onClick={openPicker}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openPicker();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) upload(file);
        }}
        className={`cursor-pointer rounded-2xl border border-dashed p-5 transition ${
          dragging
            ? "border-brand-400 bg-brand-50/80 ring-4 ring-brand-500/10"
            : "border-ink/15 bg-white/50 hover:border-brand-300 hover:bg-brand-50/30"
        } ${loading ? "pointer-events-none opacity-70" : ""}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-600/10">
              <UploadCloud className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-semibold text-ink">
                Drop a file here, or <span className="text-brand-700 underline underline-offset-4">browse</span>
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Sale deed, 7/12 extract, property card, EC or ferfar.
              </p>
              <p className="mt-1 text-[11px] text-slate-400">Up to {MAX_MB} MB per file.</p>
            </div>
          </div>
          <button
            type="button"
            className="btn-secondary btn-sm shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              openPicker();
            }}
            disabled={loading}
          >
            Choose file
          </button>
        </div>
      </div>

      {loading && (
        <div className="mt-3 flex items-center gap-2.5 rounded-xl bg-brand-50/80 px-3.5 py-2.5 text-xs font-medium text-brand-800">
          <Spinner className="h-3.5 w-3.5" />
          Processing — OCR, classification and field extraction…
        </div>
      )}

      {error && (
        <div className="mt-3 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-xs text-rose-700">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <p className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-400">
        <Lock className="h-3 w-3" />
        Files stay off-chain — only their SHA-256 hash is registered.
      </p>
    </section>
  );
}

export function DocumentList({
  documents,
  onAction,
}: {
  documents: DocumentItem[];
  onAction: () => void;
}) {
  const [busy, setBusy] = useState<number | null>(null);
  const [copied, setCopied] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function run(id: number, action: "register" | "verify") {
    setBusy(id);
    setError("");
    try {
      if (action === "register") await api.registerBlockchain(id);
      else await api.verifyBlockchain(id);
      await onAction();
    } catch (err) {
      setError(err instanceof Error ? err.message : "The blockchain action failed.");
    } finally {
      setBusy(null);
    }
  }

  async function copyHash(doc: DocumentItem) {
    try {
      await navigator.clipboard.writeText(doc.file_hash);
      setCopied(doc.id);
      window.setTimeout(() => setCopied((value) => (value === doc.id ? null : value)), 1600);
    } catch {
      // Clipboard access is optional; the full hash is available in the title attribute.
    }
  }

  if (!documents.length) {
    return (
      <div className="rounded-xl border border-dashed border-ink/15 bg-white/40 px-5 py-10 text-center">
        <FileText className="mx-auto h-7 w-7 text-slate-300" />
        <p className="mt-3 text-sm font-medium text-slate-600">No documents yet</p>
        <p className="mt-1 text-xs text-slate-400">
          Upload the first file to start the extraction pipeline.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {error && (
        <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-xs text-rose-700">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {documents.map((doc) => {
        const status = documentStatus(doc.status);
        return (
          <div
            key={doc.id}
            className="rounded-xl border border-ink/[0.06] bg-white/70 p-4 transition hover:border-brand-200/80 hover:bg-white"
          >
            <div className="flex flex-wrap items-start gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
                <FileText className="h-[18px] w-[18px]" />
              </span>

              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
                  <p className="max-w-full truncate text-sm font-semibold text-ink">{doc.filename}</p>
                  <span className="badge bg-slate-50 text-slate-600 ring-1 ring-inset ring-slate-500/15">
                    {humanize(doc.doc_type)}
                  </span>
                  <span className={status.badge}>
                    <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
                    {status.label}
                  </span>
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[11px] text-slate-400">
                  <span className="inline-flex min-w-0 items-center gap-1.5">
                    <Hash className="h-3 w-3 shrink-0" />
                    <span className="hash" title={doc.file_hash}>
                      {shortHash(doc.file_hash, 12, 8)}
                    </span>
                    <button
                      type="button"
                      onClick={() => copyHash(doc)}
                      className="rounded p-0.5 transition hover:bg-ink/5 hover:text-ink"
                      aria-label="Copy SHA-256 hash"
                      title="Copy full hash"
                    >
                      {copied === doc.id ? (
                        <Check className="h-3 w-3 text-emerald-600" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </button>
                  </span>
                  <span>Uploaded {formatDate(doc.created_at)}</span>
                </div>

                {doc.blockchain_tx && (
                  <p className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px] text-emerald-700">
                    <Link2 className="h-3 w-3 shrink-0" />
                    <span className="font-medium">Hash anchored</span>
                    <span className="font-mono text-emerald-600/80">{shortHash(doc.blockchain_tx, 12, 6)}</span>
                    {doc.blockchain_verified && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-1.5 py-0.5 font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/15">
                        <ShieldCheck className="h-2.5 w-2.5" />
                        Verified
                      </span>
                    )}
                  </p>
                )}
              </div>

              <div className="flex w-full shrink-0 flex-wrap gap-1.5 sm:w-auto">
                <button
                  className="btn-secondary btn-sm"
                  onClick={() => run(doc.id, "register")}
                  disabled={busy === doc.id}
                  title="Register the SHA-256 hash on-chain"
                >
                  {busy === doc.id ? <Spinner className="h-3 w-3" /> : null}
                  Register hash
                </button>
                <button
                  className="btn-secondary btn-sm"
                  onClick={() => run(doc.id, "verify")}
                  disabled={busy === doc.id}
                  title="Verify the stored hash against the on-chain record"
                >
                  Verify
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

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
    <section>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="font-display text-[26px] leading-none text-ink">Upload documents</h3>
          <p className="mt-1.5 text-[12px] leading-relaxed text-secondary">
            Add the deed set for this property — one file at a time.
          </p>
        </div>
        <span className="chip">PDF · JPG · PNG</span>
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
        className={`cursor-pointer border border-dashed p-5 ${
          dragging ? "border-ink bg-paper-deep" : "border-quiet bg-paper hover:border-ink"
        } ${loading ? "pointer-events-none opacity-60" : ""}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <span className="grid h-11 w-11 shrink-0 place-items-center border border-ink text-ink">
              <UploadCloud className="h-5 w-5" />
            </span>
            <div>
              <p className="font-display text-[20px] leading-tight text-ink">
                Drop a file here, or{" "}
                <span className="border-b border-ink">browse</span>
              </p>
              <p className="mt-1 text-[12px] leading-relaxed text-secondary">
                Sale deed, 7/12 extract, property card, EC or ferfar.
              </p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                Up to {MAX_MB} MB per file
              </p>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm shrink-0"
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
        <div className="mt-3 flex items-center gap-2.5 border border-ink bg-ink px-3.5 py-2.5 font-mono text-[10px] uppercase tracking-[0.08em] text-paper">
          <Spinner className="h-3.5 w-3.5" />
          Processing — OCR, classification and field extraction
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="mt-3 flex items-start gap-2.5 border border-ink px-3.5 py-2.5 text-[12px] leading-relaxed text-ink"
        >
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <p className="mt-3 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
        <Lock className="h-3 w-3" />
        Files stay off-chain — only their SHA-256 hash is registered.
      </p>
    </section>
  );
}

export function DocumentList({
  documents,
  onAction,
  canManage = true,
}: {
  documents: DocumentItem[];
  onAction: () => void;
  canManage?: boolean;
}) {
  const [busy, setBusy] = useState<number | null>(null);
  const [copied, setCopied] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<{ id: number; text: string; ok: boolean } | null>(null);

  const hasEvmAnchor = documents.some(
    (doc) => doc.blockchain_tx && !doc.blockchain_tx.startsWith("mock-tx-")
  );
  const hasMockAnchor = documents.some((doc) => doc.blockchain_tx?.startsWith("mock-tx-"));

  async function run(id: number, action: "register" | "verify") {
    setBusy(id);
    setError("");
    setFeedback(null);
    try {
      const result =
        action === "register"
          ? await api.registerBlockchain(id)
          : await api.verifyBlockchain(id);
      setFeedback({
        id,
        text: result.message,
        ok: result.status !== "MISMATCH" && result.status !== "NOT_REGISTERED",
      });
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
      <div className="border border-quiet px-5 py-12 text-center">
        <FileText className="mx-auto h-7 w-7 text-secondary" />
        <p className="mt-4 font-display text-[24px] leading-none text-ink">No documents yet</p>
        <p className="mx-auto mt-2 max-w-sm text-[13px] leading-relaxed text-secondary">
          Upload the first file to start the extraction pipeline.
        </p>
      </div>
    );
  }

  return (
    <div>
      {error && (
        <div
          role="alert"
          className="mb-3 flex items-start gap-2.5 border border-ink px-3.5 py-2.5 text-[12px] leading-relaxed text-ink"
        >
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {feedback && (
        <p
          role="status"
          className={`mb-3 flex items-center gap-2 border px-3.5 py-2.5 font-mono text-[10px] uppercase tracking-[0.06em] text-ink ${
            feedback.ok ? "border-quiet" : "border-2 border-ink"
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          {feedback.text}
        </p>
      )}

      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 border-t border-ink pt-3 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
        <span>Anchor mode</span>
        <span className="text-ink">
          {hasEvmAnchor ? "EVM · confirmed" : hasMockAnchor ? "Mock · not a chain write" : "Not anchored"}
        </span>
      </div>

      {documents.map((doc) => {
        const status = documentStatus(doc.status);
        return (
          <div key={doc.id} className="border-t border-quiet py-4">
            <div className="flex flex-wrap items-start gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center border border-quiet text-ink">
                <FileText className="h-[18px] w-[18px]" />
              </span>

              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
                  <p className="max-w-full truncate font-display text-[20px] leading-tight text-ink">
                    {doc.filename}
                  </p>
                  <span className="chip">{humanize(doc.doc_type)}</span>
                  <span className={status.badge}>
                    <span className={`h-1.5 w-1.5 ${status.dot}`} />
                    {status.label}
                  </span>
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 font-mono text-[10px] text-secondary">
                  <span className="inline-flex min-w-0 items-center gap-1.5">
                    <Hash className="h-3 w-3 shrink-0" />
                    <span className="hash" title={doc.file_hash}>
                      {shortHash(doc.file_hash, 12, 8)}
                    </span>
                    <button
                      type="button"
                      onClick={() => copyHash(doc)}
                      className="p-0.5 hover:text-ink"
                      aria-label="Copy SHA-256 hash"
                      title="Copy full hash"
                    >
                      {copied === doc.id ? (
                        <Check className="h-3 w-3" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </button>
                  </span>
                  <span>Uploaded {formatDate(doc.created_at)}</span>
                </div>

                {doc.blockchain_tx && (
                  <p className="mt-2 flex flex-wrap items-center gap-1.5 font-mono text-[10px] text-ink">
                    <Link2 className="h-3 w-3 shrink-0" />
                    <span className="uppercase tracking-[0.08em]">
                      {doc.blockchain_tx.startsWith("mock-tx-") ? "Mock anchor" : "EVM anchor"}
                    </span>
                    <span className="text-secondary">{shortHash(doc.blockchain_tx, 12, 6)}</span>
                    {doc.blockchain_verified === true && (
                      <span className="inline-flex items-center gap-1 border border-ink px-1.5 py-0.5 uppercase tracking-[0.08em]">
                        <ShieldCheck className="h-2.5 w-2.5" />
                        Verified
                      </span>
                    )}
                    {doc.blockchain_verified === false && (
                      <span className="inline-flex items-center gap-1 border-2 border-ink px-1.5 py-0.5 uppercase tracking-[0.08em]">
                        <AlertTriangle className="h-2.5 w-2.5" />
                        Mismatch
                      </span>
                    )}
                  </p>
                )}
              </div>

              {canManage && (
                <div className="flex w-full shrink-0 flex-wrap gap-2 sm:w-auto">
                  {!doc.blockchain_tx ? (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => run(doc.id, "register")}
                      disabled={busy === doc.id}
                      title="Anchor the SHA-256 hash using the configured blockchain mode"
                    >
                      {busy === doc.id ? <Spinner className="h-3 w-3" /> : null}
                      Anchor hash
                    </button>
                  ) : (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => run(doc.id, "verify")}
                      disabled={busy === doc.id}
                      title="Compare the stored file with the anchored hash"
                    >
                      {busy === doc.id ? <Spinner className="h-3 w-3" /> : null}
                      Verify hash
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

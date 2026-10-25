"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  ChevronDown,
  Link2,
  RefreshCw,
  ShieldCheck,
  Spinner,
  X,
} from "@/components/icons";
import {
  api,
  clearToken,
  Finding,
  getToken,
  LegalRule,
  RuleDetail,
  RulePack,
  RuleUpdateInput,
  UserOut,
} from "@/lib/api";
import { formatDate, humanize, severityTone, shortHash } from "@/lib/presentation";

type RuleForm = {
  title: string;
  description: string;
  severity: Finding["severity"];
  confidence: string;
  conditions: string;
  recommended_action: string;
  law_name: string;
  section: string;
  source_url: string;
  is_active: boolean;
  change_note: string;
};

function formFromRule(rule: RuleDetail): RuleForm {
  return {
    title: rule.title,
    description: rule.description ?? "",
    severity: rule.severity,
    confidence: String(rule.confidence),
    conditions: rule.conditions ? JSON.stringify(rule.conditions, null, 2) : "",
    recommended_action: rule.recommended_action ?? "",
    law_name: rule.law_name ?? "",
    section: rule.section ?? "",
    source_url: rule.source_url ?? "",
    is_active: rule.is_active,
    change_note: "",
  };
}

export default function RulesPage() {
  const [pack, setPack] = useState<RulePack | null>(null);
  const [me, setMe] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const [editing, setEditing] = useState<RuleDetail | null>(null);
  const [form, setForm] = useState<RuleForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [editorError, setEditorError] = useState("");
  const [resetting, setResetting] = useState(false);

  const isAdmin = me?.role === "admin";

  async function loadPack(user: UserOut | null = me) {
    const data =
      user?.role === "admin"
        ? await api.adminGetRulePack("Maharashtra")
        : await api.getRulePack("Maharashtra");
    setPack(data);
    return data;
  }

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      try {
        let user: UserOut | null = null;
        if (getToken()) {
          try {
            user = await api.me();
          } catch {
            clearToken();
            user = null;
          }
        }
        if (!active) return;
        setMe(user);
        const data =
          user?.role === "admin"
            ? await api.adminGetRulePack("Maharashtra")
            : await api.getRulePack("Maharashtra");
        if (active) setPack(data);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "The rule catalogue could not be loaded.");
        }
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function startEdit(rule: LegalRule) {
    setEditorError("");
    setNotice("");
    try {
      const detail = await api.adminGetRule(rule.jurisdiction, rule.rule_code);
      setEditing(detail);
      setForm(formFromRule(detail));
      window.scrollTo({ top: 0, behavior: "auto" });
      window.setTimeout(() => document.getElementById("rule-title")?.focus(), 0);
    } catch (err) {
      setEditorError(err instanceof Error ? err.message : "The rule could not be opened.");
    }
  }

  async function saveRule() {
    if (!editing || !form) return;
    setSaving(true);
    setEditorError("");
    setNotice("");
    try {
      let conditions: Record<string, unknown> | null = null;
      if (form.conditions.trim()) {
        const parsed = JSON.parse(form.conditions);
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("Conditions must be a JSON object.");
        }
        conditions = parsed as Record<string, unknown>;
      }
      const confidence = Number(form.confidence);
      const payload: RuleUpdateInput = {
        title: form.title.trim(),
        description: form.description.trim() || null,
        severity: form.severity,
        confidence,
        conditions,
        recommended_action: form.recommended_action.trim() || null,
        law_name: form.law_name.trim() || null,
        section: form.section.trim() || null,
        source_url: form.source_url.trim() || null,
        is_active: form.is_active,
        change_note: form.change_note.trim() || null,
        expected_version: editing.current_version,
      };
      if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
        throw new Error("Confidence must be between 0 and 1.");
      }
      const updated = await api.adminUpdateRule(editing.jurisdiction, editing.rule_code, payload);
      setEditing(updated);
      setForm(formFromRule(updated));
      setNotice(`Saved ${updated.rule_code} as version ${updated.current_version}.`);
      await loadPack();
    } catch (err) {
      setEditorError(
        err instanceof Error ? err.message : "The rule could not be saved. Try again."
      );
    } finally {
      setSaving(false);
    }
  }

  async function rollback(version: number) {
    if (!editing) return;
    const note = window.prompt(
      `Restore ${editing.rule_code} from version ${version}? Add a change note (optional).`
    );
    if (note === null) return;
    setSaving(true);
    setEditorError("");
    setNotice("");
    try {
      const updated = await api.adminRollbackRule(editing.jurisdiction, editing.rule_code, {
        version,
        change_note: note.trim() || null,
      });
      setEditing(updated);
      setForm(formFromRule(updated));
      setNotice(`Restored ${updated.rule_code} as version ${updated.current_version}.`);
      await loadPack();
    } catch (err) {
      setEditorError(err instanceof Error ? err.message : "The rollback failed.");
    } finally {
      setSaving(false);
    }
  }

  async function resetPack() {
    if (!pack) return;
    if (
      !window.confirm(
        "Reset the Maharashtra pack to the built-in mh-v1 catalogue? This creates new versions for every rule."
      )
    ) {
      return;
    }
    setResetting(true);
    setEditorError("");
    setNotice("");
    try {
      const refreshed = await api.adminResetRulePack(pack.jurisdiction, {
        change_note: "Admin reset to the built-in catalogue",
      });
      setPack(refreshed);
      setEditing(null);
      setForm(null);
      setNotice("The pack was reset to the built-in mh-v1 catalogue.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "The pack could not be reset.");
    } finally {
      setResetting(false);
    }
  }

  return (
    <>
      <Navbar />
      <main>
        <section className="border-b border-ink bg-ink text-paper">
          <div className="shell">
            <div className="dp-section section-y-md">
              <div className="dp-rail">
                <p className="eyebrow text-quiet">Rule catalogue</p>
                <p className="mt-5 max-w-[13rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-quiet">
                  Screening rules, not legal conclusions
                </p>
              </div>
              <div className="dp-body dp-body--inverted">
                <h1 className="font-display text-[clamp(42px,6cqw,84px)] font-medium leading-[0.98] tracking-[-0.04em] text-paper">
                  The rules behind the verdict.
                </h1>
                <p className="mt-4 max-w-[38em] text-[15px] leading-[1.55] text-quiet">
                  Every catalogue entry names the condition it tests, the reference behind it and the
                  action a reviewer can take. Editing is append-only: each change becomes a new
                  version.
                </p>
              </div>
            </div>
          </div>
        </section>

        <div className="shell">
          {loading && (
            <div className="mt-8 border border-quiet px-5 py-12 text-center">
              <Spinner className="mx-auto h-5 w-5 text-ink" />
              <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                Loading the catalogue…
              </p>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="mt-8 flex items-start gap-3 border border-ink px-4 py-3.5 text-[13px] leading-relaxed text-ink"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p className="flex-1">{error}</p>
            </div>
          )}

          {pack && (
            <>
              <section className="mt-8 grid gap-px border border-quiet bg-quiet sm:grid-cols-2 xl:grid-cols-4">
                <div className="bg-paper p-5">
                  <p className="eyebrow">Pack</p>
                  <p className="mt-3 font-display text-[26px] leading-none">{pack.name}</p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    {pack.jurisdiction} · v{pack.version}
                  </p>
                </div>
                <div className="bg-paper p-5">
                  <p className="eyebrow">Catalogue</p>
                  <p className="display-number mt-3">{pack.rule_count}</p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    {pack.active_rule_count} active
                  </p>
                </div>
                <div className="bg-paper p-5">
                  <p className="eyebrow">Evaluable</p>
                  <p className="display-number mt-3">{pack.evaluable_rule_count}</p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    machine-checked rows
                  </p>
                </div>
                <div className="bg-paper p-5">
                  <p className="eyebrow">Signature</p>
                  <p className="mt-3 font-mono text-[13px] leading-relaxed text-ink">
                    {shortHash(pack.signature, 10, 8)}
                  </p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    {pack.updated_at ? `Updated ${formatDate(pack.updated_at)}` : "Built-in catalogue"}
                  </p>
                </div>
              </section>

              {isAdmin && (
                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border border-ink bg-ink px-4 py-3 text-paper">
                  <p className="font-mono text-[10px] uppercase tracking-[0.08em]">
                    Admin mode · every save creates a version snapshot
                  </p>
                  <button
                    type="button"
                    className="btn btn-on-ink-outline btn-sm"
                    onClick={resetPack}
                    disabled={resetting}
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${resetting ? "animate-spin" : ""}`} />
                    Reset pack
                  </button>
                </div>
              )}

              {notice && (
                <p
                  role="status"
                  className="mt-5 flex items-center gap-2 border border-ink px-4 py-3 font-mono text-[10px] uppercase tracking-[0.06em] text-ink"
                >
                  <Check className="h-3.5 w-3.5" />
                  {notice}
                </p>
              )}

              {editing && form && (
                <section className="mt-8 border border-ink">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink px-5 py-4">
                    <div>
                      <p className="eyebrow">Editing {editing.rule_code}</p>
                      <p className="mt-1 font-display text-[26px] leading-none">
                        Version {editing.current_version}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="icon-btn"
                      onClick={() => {
                        setEditing(null);
                        setForm(null);
                        setEditorError("");
                      }}
                      aria-label="Close editor"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="grid gap-8 p-5 lg:grid-cols-[1.4fr_0.6fr]">
                    <div>
                      {editorError && (
                        <p
                          role="alert"
                          className="mb-4 flex items-start gap-2 border border-ink px-3.5 py-3 text-[12px] leading-relaxed text-ink"
                        >
                          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                          {editorError}
                        </p>
                      )}

                      <div className="grid gap-4">
                        <div>
                          <label htmlFor="rule-title" className="label">
                            Title
                          </label>
                          <input
                            id="rule-title"
                            className="input"
                            value={form.title}
                            onChange={(e) => setForm({ ...form, title: e.target.value })}
                          />
                        </div>
                        <div>
                          <label htmlFor="rule-description" className="label">
                            Description
                          </label>
                          <textarea
                            id="rule-description"
                            className="input min-h-[96px]"
                            value={form.description}
                            onChange={(e) => setForm({ ...form, description: e.target.value })}
                          />
                        </div>
                        <div className="grid gap-4 sm:grid-cols-2">
                          <div>
                            <label htmlFor="rule-severity" className="label">
                              Severity
                            </label>
                            <select
                              id="rule-severity"
                              className="input"
                              value={form.severity}
                              onChange={(e) =>
                                setForm({
                                  ...form,
                                  severity: e.target.value as Finding["severity"],
                                })
                              }
                            >
                              {(["low", "medium", "high", "critical"] as const).map((severity) => (
                                <option key={severity} value={severity}>
                                  {humanize(severity)}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label htmlFor="rule-confidence" className="label">
                              Confidence (0–1)
                            </label>
                            <input
                              id="rule-confidence"
                              className="input"
                              type="number"
                              min="0"
                              max="1"
                              step="0.01"
                              value={form.confidence}
                              onChange={(e) => setForm({ ...form, confidence: e.target.value })}
                            />
                          </div>
                        </div>
                        <div>
                          <label htmlFor="rule-conditions" className="label">
                            Conditions JSON
                          </label>
                          <textarea
                            id="rule-conditions"
                            className="input min-h-[180px] font-mono text-[12px]"
                            spellCheck={false}
                            value={form.conditions}
                            onChange={(e) => setForm({ ...form, conditions: e.target.value })}
                          />
                          <p className="mt-2 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
                            Leave empty for a metadata-only catalogue row.
                          </p>
                        </div>
                        <div>
                          <label htmlFor="rule-action" className="label">
                            Recommended action
                          </label>
                          <textarea
                            id="rule-action"
                            className="input min-h-[80px]"
                            value={form.recommended_action}
                            onChange={(e) =>
                              setForm({ ...form, recommended_action: e.target.value })
                            }
                          />
                        </div>
                        <div className="grid gap-4 sm:grid-cols-3">
                          <div>
                            <label htmlFor="rule-law" className="label">
                              Law
                            </label>
                            <input
                              id="rule-law"
                              className="input"
                              value={form.law_name}
                              onChange={(e) => setForm({ ...form, law_name: e.target.value })}
                            />
                          </div>
                          <div>
                            <label htmlFor="rule-section" className="label">
                              Section
                            </label>
                            <input
                              id="rule-section"
                              className="input"
                              value={form.section}
                              onChange={(e) => setForm({ ...form, section: e.target.value })}
                            />
                          </div>
                          <div>
                            <label htmlFor="rule-source" className="label">
                              Source URL
                            </label>
                            <input
                              id="rule-source"
                              className="input"
                              value={form.source_url}
                              onChange={(e) => setForm({ ...form, source_url: e.target.value })}
                            />
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-4">
                          <label className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.08em] text-ink">
                            <input
                              type="checkbox"
                              className="h-4 w-4 accent-ink"
                              checked={form.is_active}
                              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                            />
                            Active
                          </label>
                        </div>
                        <div>
                          <label htmlFor="rule-note" className="label">
                            Change note
                          </label>
                          <input
                            id="rule-note"
                            className="input"
                            placeholder="Why this rule changed"
                            value={form.change_note}
                            onChange={(e) => setForm({ ...form, change_note: e.target.value })}
                          />
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            className="btn btn-primary"
                            onClick={saveRule}
                            disabled={saving}
                          >
                            {saving ? <Spinner /> : <Check className="h-4 w-4" />}
                            {saving ? "Saving…" : "Save new version"}
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => {
                              setEditing(null);
                              setForm(null);
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>

                    <aside>
                      <h3 className="font-display text-[24px] leading-none">Version history</h3>
                      <p className="mt-2 font-mono text-[10px] leading-relaxed text-secondary">
                        Snapshots are append-only. Restore any earlier version as a new one.
                      </p>
                      <ol className="mt-4">
                        {editing.versions.map((version) => (
                          <li key={version.version} className="border-t border-quiet py-3">
                            <div className="flex items-center justify-between gap-2">
                              <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-ink">
                                v{version.version}
                                {version.version === editing.current_version ? " · current" : ""}
                              </p>
                              <p className="font-mono text-[9px] text-secondary">
                                {formatDate(version.created_at)}
                              </p>
                            </div>
                            {version.change_note && (
                              <p className="mt-1 text-[11px] leading-relaxed text-secondary">
                                {version.change_note}
                              </p>
                            )}
                            {version.version !== editing.current_version && (
                              <button
                                type="button"
                                className="mt-2 font-mono text-[9px] uppercase tracking-[0.08em] text-ink underline underline-offset-4 disabled:opacity-40"
                                onClick={() => rollback(version.version)}
                                disabled={saving}
                              >
                                Restore this version
                              </button>
                            )}
                          </li>
                        ))}
                      </ol>
                    </aside>
                  </div>
                </section>
              )}

              <section className="mt-10 border-t border-ink">
                <div className="flex flex-wrap items-end justify-between gap-4 py-5">
                  <div>
                    <h2 className="display-heading">Catalogue</h2>
                    <p className="mt-2 max-w-[38em] text-[13px] leading-relaxed text-secondary">
                      A rule can be active without being evaluable. Metadata-only rows document the
                      checks performed by the cross-validator matrix.
                    </p>
                  </div>
                  <span className="chip">{pack.rules.length} rows</span>
                </div>

                <div>
                  {pack.rules.map((rule) => {
                    const tone = severityTone(rule.severity);
                    const open = expanded === rule.rule_code;
                    return (
                      <article key={rule.rule_code} className="border-t border-quiet py-6">
                        <div className="grid gap-4 lg:grid-cols-[8rem_minmax(0,1fr)_auto]">
                          <div>
                            <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-ink">
                              {rule.rule_code}
                            </p>
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              <span className={tone.badge}>{tone.label}</span>
                              {!rule.is_active && <span className="chip">Inactive</span>}
                              {!rule.is_evaluable && <span className="chip">Metadata</span>}
                            </div>
                          </div>

                          <div className="min-w-0">
                            <h3 className="max-w-[34em] font-display text-[26px] font-medium leading-[1.02] text-ink">
                              {rule.title}
                            </h3>
                            {rule.description && (
                              <p className="mt-2 max-w-[42em] text-[13px] leading-relaxed text-secondary">
                                {rule.description}
                              </p>
                            )}
                            {(rule.law_name || rule.section) && (
                              <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.06em] text-secondary">
                                {[rule.law_name, rule.section ? `§ ${rule.section}` : null]
                                  .filter(Boolean)
                                  .join(" · ")}
                              </p>
                            )}

                            <button
                              type="button"
                              onClick={() => setExpanded(open ? null : rule.rule_code)}
                              className="mt-3 inline-flex min-h-6 items-center gap-1.5 py-1 font-mono text-[9px] uppercase tracking-[0.08em] text-ink underline underline-offset-4"
                              aria-expanded={open}
                            >
                              {open ? "Hide condition" : "Show condition"}
                              <ChevronDown
                                className={`h-3 w-3 ${open ? "rotate-180" : ""}`}
                              />
                            </button>

                            {open && (
                              <div className="mt-3 border border-quiet bg-paper-deep p-3">
                                {rule.conditions ? (
                                  <pre className="overflow-x-auto whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-ink">
                                    {JSON.stringify(rule.conditions, null, 2)}
                                  </pre>
                                ) : (
                                  <p className="font-mono text-[10px] uppercase tracking-[0.06em] text-secondary">
                                    Catalogue metadata · evaluated by the cross-validator matrix.
                                  </p>
                                )}
                              </div>
                            )}

                            {rule.recommended_action && open && (
                              <p className="mt-3 max-w-[42em] border-l border-ink pl-3 text-[12px] leading-relaxed text-secondary">
                                {rule.recommended_action}
                              </p>
                            )}
                          </div>

                          <div className="flex flex-wrap items-start gap-2">
                            {rule.source_url && (
                              <a
                                href={rule.source_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1.5 border border-quiet px-2.5 py-2 font-mono text-[9px] uppercase tracking-[0.08em] text-secondary hover:border-ink hover:text-ink"
                              >
                                <Link2 className="h-3 w-3" />
                                Source
                                <ArrowUpRight className="h-3 w-3" />
                              </a>
                            )}
                            {isAdmin && (
                              <button
                                type="button"
                                className="btn btn-secondary btn-sm"
                                onClick={() => startEdit(rule)}
                              >
                                Edit
                              </button>
                            )}
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </section>

              <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-ink py-5">
                <p className="max-w-[44em] text-[11px] leading-relaxed text-secondary">
                  <span className="inline-flex items-center gap-1.5 font-medium text-ink">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Rule packs are evidence, not a title opinion.
                  </span>{" "}
                  A clean run only means the active checks found nothing on the uploaded documents.
                </p>
                <p className="font-mono text-[9px] uppercase tracking-[0.08em] text-secondary">
                  {pack.code} · signature {shortHash(pack.signature, 8, 6)}
                </p>
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
}

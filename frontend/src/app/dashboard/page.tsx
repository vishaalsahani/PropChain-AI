"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import {
  Activity,
  ArrowRight,
  Flag,
  Layers,
  MapPin,
  Plus,
  Ruler,
  ShieldAlert,
  ShieldCheck,
  Spinner,
} from "@/components/icons";
import { api, Property, getToken } from "@/lib/api";
import { formatArea, formatDate, humanize, propertyStatus, riskTone } from "@/lib/presentation";

const ENGINE_LABELS: Record<string, string> = {
  api: "API",
  database: "Database",
  ocr_pipeline: "OCR",
  doc_classifier: "Classifier",
  nlp_extractor: "Extraction",
  cross_validator: "Cross-check",
  ownership_builder: "Ownership",
  rule_engine: "Rules",
  blockchain: "Blockchain",
};

const ENGINE_ORDER = [
  "ocr_pipeline",
  "doc_classifier",
  "nlp_extractor",
  "cross_validator",
  "ownership_builder",
  "rule_engine",
  "blockchain",
];

function locationOf(property: Property) {
  return [property.village, property.taluka, property.district]
    .filter((part, index, parts) => Boolean(part) && parts.indexOf(part) === index)
    .join(", ");
}

export default function DashboardPage() {
  const router = useRouter();
  const [properties, setProperties] = useState<Property[]>([]);
  const [health, setHealth] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [props, h] = await Promise.all([api.listProperties(), api.health()]);
      setProperties(props);
      setHealth(h.components);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      if (/401|403|not authenticated|token/i.test(message)) {
        router.replace("/login");
        return;
      }
      setError("Unable to load your workspace. Check that the API is running and try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stats = useMemo(() => {
    const analyzed = properties.filter((p) => p.status === "analyzed").length;
    const review = properties.filter((p) => p.status === "needs_review").length;
    const flagged = properties.filter((p) => p.status === "flagged").length;
    const scored = properties.filter((p) => p.risk_score !== null);
    const average = scored.length
      ? Math.round(scored.reduce((sum, p) => sum + (p.risk_score ?? 0), 0) / scored.length)
      : null;
    return { analyzed, review, flagged, average, scored: scored.length };
  }, [properties]);

  const statCards = [
    {
      label: "Properties",
      value: properties.length,
      hint: `${stats.scored} with a risk score`,
      icon: Layers,
    },
    {
      label: "Analyzed",
      value: stats.analyzed,
      hint: "verdict recorded",
      icon: ShieldCheck,
    },
    {
      label: "Needs review",
      value: stats.review,
      hint: "open items to confirm",
      icon: ShieldAlert,
    },
    {
      label: "Flagged",
      value: stats.flagged,
      hint: stats.average === null ? "no scores yet" : `avg. risk ${stats.average}/100`,
      icon: Flag,
    },
  ];

  return (
    <>
      <Navbar />
      <main>
        <section className="border-b border-ink bg-ink text-paper">
          <div className="shell">
            <div className="dp-section section-y-md">
              <div className="dp-rail">
                <p className="eyebrow text-quiet">Portfolio overview</p>
                <p className="mt-5 max-w-[13rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-quiet">
                  Findings, not legal conclusions
                </p>
              </div>

              <div className="dp-body dp-body--inverted">
                <h1 className="font-display text-[clamp(42px,6cqw,84px)] font-medium leading-[0.98] tracking-[-0.04em] text-paper">
                  Your due-diligence desk.
                </h1>
                <p className="mt-4 max-w-[36em] text-[15px] leading-[1.55] text-quiet">
                  Upload the deed set, let the pipeline cross-check it, and read a verdict with the
                  evidence behind it.
                </p>
                <div className="mt-7 flex flex-wrap items-center gap-3">
                  <Link href="/properties/new" className="btn btn-on-ink">
                    <Plus className="h-4 w-4" />
                    Add property
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="shell">
          {error && (
            <div
              role="alert"
              className="mt-8 flex flex-wrap items-center justify-between gap-3 border border-ink px-5 py-4 text-[13px] leading-relaxed text-ink"
            >
              <p>{error}</p>
              <button onClick={load} className="btn btn-secondary btn-sm">
                Retry
              </button>
            </div>
          )}

          <section className="mt-8 grid gap-px border border-quiet bg-quiet sm:grid-cols-2 xl:grid-cols-4">
            {loading
              ? Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="bg-paper p-5">
                    <div className="skeleton h-3 w-24" />
                    <div className="skeleton mt-4 h-12 w-20" />
                    <div className="skeleton mt-3 h-3 w-32" />
                  </div>
                ))
              : statCards.map((stat) => (
                  <div key={stat.label} className="bg-paper p-5">
                    <div className="flex items-start justify-between gap-3">
                      <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-secondary">
                        {stat.label}
                      </p>
                      <stat.icon className="h-4 w-4 text-ink" />
                    </div>
                    <p className="display-number mt-4">{stat.value}</p>
                    <p className="mt-2 font-mono text-[9px] uppercase tracking-[0.07em] text-secondary">
                      {stat.hint}
                    </p>
                  </div>
                ))}
          </section>

          <section className="mt-14 border-t border-ink">
            <div className="dp-section py-10">
              <div className="dp-rail">
                <h2 className="display-heading">Your properties</h2>
                <p className="mt-4 max-w-[18rem] text-[13px] leading-relaxed text-secondary">
                  Every uploaded file belongs to one property profile.
                </p>
                <span className="mt-5 inline-block border border-quiet px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                  {properties.length} {properties.length === 1 ? "property" : "properties"}
                </span>
              </div>

              <div className="dp-body">
                {loading ? (
                  <div className="grid gap-px bg-quiet sm:grid-cols-2">
                    {Array.from({ length: 4 }).map((_, index) => (
                      <div key={index} className="bg-paper p-5">
                        <div className="skeleton h-5 w-3/4" />
                        <div className="skeleton mt-3 h-3 w-1/2" />
                        <div className="skeleton mt-5 h-6 w-2/3" />
                        <div className="skeleton mt-6 h-2 w-full" />
                      </div>
                    ))}
                  </div>
                ) : properties.length === 0 ? (
                  <div className="border border-quiet px-6 py-14 text-center">
                    <span className="mx-auto grid h-12 w-12 place-items-center border border-ink text-ink">
                      <Layers className="h-6 w-6" />
                    </span>
                    <h3 className="mt-5 font-display text-[30px] leading-none">
                      Start with a property file
                    </h3>
                    <p className="mx-auto mt-3 max-w-sm text-[13px] leading-relaxed text-secondary">
                      Create a profile with the village, survey number and area, then upload the deed
                      set to run the first analysis.
                    </p>
                    <Link href="/properties/new" className="btn btn-primary mt-6">
                      <Plus className="h-4 w-4" />
                      Add a property
                    </Link>
                  </div>
                ) : (
                  <div className="grid gap-px bg-quiet sm:grid-cols-2">
                    {properties.map((property) => {
                      const status = propertyStatus(property.status);
                      const risk = riskTone(property.risk_score);
                      const location = locationOf(property);
                      return (
                        <Link
                          key={property.id}
                          href={`/properties/${property.id}`}
                          className="group flex flex-col bg-paper p-5 hover:bg-paper-deep"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <h3 className="line-clamp-2 font-display text-[25px] leading-[1.02] text-ink">
                                {property.title}
                              </h3>
                              <p className="mt-2 flex items-center gap-1.5 font-mono text-[10px] text-secondary">
                                <MapPin className="h-3.5 w-3.5 shrink-0" />
                                {location || "Location not set"}
                              </p>
                            </div>
                            <span className={`${status.badge} shrink-0`}>
                              <span className={`h-1.5 w-1.5 ${status.dot}`} />
                              {status.label}
                            </span>
                          </div>

                          <div className="mt-4 flex flex-wrap gap-1.5">
                            {property.survey_number && (
                              <span className="chip">Survey {property.survey_number}</span>
                            )}
                            {property.gat_number && (
                              <span className="chip">Gat {property.gat_number}</span>
                            )}
                            {property.area_sqft !== null && property.area_sqft !== undefined && (
                              <span className="chip">
                                <Ruler className="h-3 w-3" />
                                {formatArea(property.area_sqft)}
                              </span>
                            )}
                          </div>

                          <div className="mt-auto pt-6">
                            <div className="flex items-center justify-between font-mono text-[10px]">
                              <span className="uppercase tracking-[0.08em] text-secondary">
                                Risk indicator
                              </span>
                              <span className={`uppercase tracking-[0.08em] ${risk.text}`}>
                                {property.risk_score === null
                                  ? "Not scored"
                                  : `${Math.round(property.risk_score)}/100`}
                              </span>
                            </div>
                            <div className="mt-2 h-1.5 w-full border border-ink">
                              <div
                                className={`h-full ${risk.bar}`}
                                style={{
                                  width: `${Math.min(Math.max(property.risk_score ?? 0, 0), 100)}%`,
                                }}
                              />
                            </div>
                            <div className="mt-4 flex items-center justify-between border-t border-quiet pt-3 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
                              <span>Created {formatDate(property.created_at)}</span>
                              <span className="inline-flex items-center gap-1 text-ink">
                                Open file
                                <ArrowRight className="h-3.5 w-3.5" />
                              </span>
                            </div>
                          </div>
                        </Link>
                      );
                    })}
                    {properties.length % 2 === 1 && (
                      <div className="hidden bg-paper sm:block" aria-hidden="true" />
                    )}
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="border-t border-ink">
            <div className="dp-section py-10">
              <div className="dp-rail">
                <h2 className="display-heading">Workspace notes</h2>
                <p className="mt-4 max-w-[18rem] text-[13px] leading-relaxed text-secondary">
                  The operational state behind this portfolio.
                </p>
              </div>

              <div className="dp-body">
                <div className="grid gap-px bg-quiet lg:grid-cols-2">
                  <div className="bg-paper p-6">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="flex items-center gap-2 font-display text-[25px] leading-none">
                        <Activity className="h-4 w-4" />
                        Analysis pipeline
                      </h3>
                      <span className="border border-quiet px-2 py-1 font-mono text-[9px] uppercase tracking-[0.08em] text-secondary">
                        Deployment
                      </span>
                    </div>
                    <p className="mt-2 font-mono text-[10px] text-secondary">
                      Engines selected for this deployment.
                    </p>

                    <div className="mt-5">
                      {(loading
                        ? ENGINE_ORDER
                        : ENGINE_ORDER.filter((key) => health[key])
                      ).map((key) => {
                        const value = health[key];
                        const isMock = value === "mock";
                        return (
                          <div
                            key={key}
                            className="flex items-center justify-between gap-3 border-t border-quiet py-2.5"
                          >
                            <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                              {ENGINE_LABELS[key] ?? humanize(key)}
                            </p>
                            {loading ? (
                              <div className="skeleton h-3 w-16" />
                            ) : (
                              <span
                                className={`border px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-[0.06em] ${
                                  isMock
                                    ? "border-quiet text-secondary"
                                    : "border-ink bg-ink text-paper"
                                }`}
                              >
                                {humanize(value ?? "—")}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-ink pt-3 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
                      <span className="inline-flex items-center gap-1.5">
                        <ShieldCheck className="h-3.5 w-3.5 text-ink" />
                        Documents stay off-chain
                      </span>
                      <span>SHA-256</span>
                    </div>
                  </div>

                  <div className="bg-paper p-6">
                    <h3 className="font-display text-[25px] leading-none">How verdicts are read</h3>
                    <p className="mt-2 font-mono text-[10px] text-secondary">
                      Project policy — findings are screening indicators.
                    </p>
                    <ul className="mt-5">
                      {[
                        {
                          icon: ShieldCheck,
                          title: "Verified",
                          body: "No medium-or-higher findings and no ownership gaps.",
                        },
                        {
                          icon: ShieldAlert,
                          title: "Needs review",
                          body: "Only low/medium items, or no completed documents yet.",
                        },
                        {
                          icon: Flag,
                          title: "Flagged",
                          body: "A high/critical finding or any gap in the ownership chain.",
                        },
                      ].map((item) => (
                        <li
                          key={item.title}
                          className="flex gap-3 border-t border-quiet py-3.5"
                        >
                          <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center border border-quiet text-ink">
                            <item.icon className="h-4 w-4" />
                          </span>
                          <div>
                            <p className="font-display text-[21px] leading-none text-ink">
                              {item.title}
                            </p>
                            <p className="mt-1 text-[11px] leading-relaxed text-secondary">
                              {item.body}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ul>
                    <p className="mt-4 border-t border-quiet pt-3 font-mono text-[9px] uppercase leading-relaxed tracking-[0.06em] text-secondary">
                      Items that could not be checked (RERA, litigation history, encumbrance) are
                      always listed alongside the verdict.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {loading && (
            <div className="flex items-center justify-center gap-2 border-t border-quiet py-5 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
              <Spinner className="h-3.5 w-3.5" />
              Loading your workspace…
            </div>
          )}
        </div>
      </main>
    </>
  );
}

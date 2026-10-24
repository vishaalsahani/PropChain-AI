export function LogoMark({ className = "h-9 w-9", tone = "brand" }: { className?: string; tone?: "brand" | "light" }) {
  return (
    <span
      className={`relative inline-grid shrink-0 place-items-center overflow-hidden rounded-[13px] ${
        tone === "light"
          ? "bg-white/10 ring-1 ring-inset ring-white/20"
          : "bg-gradient-to-br from-brand-700 via-brand-800 to-brand-950 shadow-[0_8px_20px_-10px_rgba(8,37,31,0.9)]"
      } ${className}`}
    >
      <svg viewBox="0 0 24 24" className="h-[58%] w-[58%]" fill="none" aria-hidden="true">
        <path
          d="M3.75 10.4 12 3.6l8.25 6.8"
          stroke="#f7f5ef"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M5.9 9.9v9.5h12.2V9.9"
          stroke="#f7f5ef"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M10 19.4v-4.3h4v4.3"
          stroke="#dcbb72"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

export function Wordmark({ light = false }: { light?: boolean }) {
  return (
    <span className="flex items-center gap-2">
      <span
        className={`font-display text-[19px] font-semibold leading-none tracking-tight ${
          light ? "text-white" : "text-ink"
        }`}
      >
        PropChain
      </span>
      <span
        className={`rounded-md px-1.5 py-[3px] text-[9px] font-bold uppercase leading-none tracking-[0.18em] ${
          light ? "bg-white/15 text-brand-100" : "bg-brand-900 text-brand-50"
        }`}
      >
        AI
      </span>
    </span>
  );
}

export function Brand({ light = false }: { light?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <LogoMark tone={light ? "light" : "brand"} />
      <Wordmark light={light} />
    </span>
  );
}

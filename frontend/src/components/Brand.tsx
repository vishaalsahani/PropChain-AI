export function LogoMark({
  className = "h-9 w-9",
  tone = "brand",
}: {
  className?: string;
  tone?: "brand" | "light";
}) {
  return (
    <span
      className={`inline-grid shrink-0 place-items-center border ${
        tone === "light"
          ? "border-paper/50 bg-paper text-ink"
          : "border-ink bg-ink text-paper"
      } ${className}`}
    >
      <svg viewBox="0 0 24 24" className="h-[58%] w-[58%]" fill="none" aria-hidden="true">
        <path
          d="M3.75 10.4 12 3.6l8.25 6.8"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M5.9 9.9v9.5h12.2V9.9"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M10 19.4v-4.3h4v4.3"
          stroke="currentColor"
          strokeWidth="1.5"
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
        className={`font-display text-[20px] font-medium leading-none tracking-[-0.03em] ${
          light ? "text-paper" : "text-ink"
        }`}
      >
        PropChain
      </span>
      <span
        className={`border px-1.5 py-[3px] font-mono text-[9px] font-medium uppercase leading-none tracking-[0.16em] ${
          light ? "border-paper/50 text-paper" : "border-ink text-ink"
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

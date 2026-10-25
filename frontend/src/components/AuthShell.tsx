import { Brand } from "@/components/Brand";
import { Layers, Link2, ShieldCheck } from "@/components/icons";

const FEATURES = [
  {
    icon: Layers,
    title: "Extraction in English & Marathi",
    body: "Sale deeds, 7/12 extracts, property cards, ECs and ferfars become structured fields.",
  },
  {
    icon: Link2,
    title: "Cross-document consistency",
    body: "Survey numbers, area, owners, dates and registration numbers are tested against each other.",
  },
  {
    icon: ShieldCheck,
    title: "Hash-anchored documents",
    body: "Files stay off-chain. Only their SHA-256 fingerprints are registered and verified.",
  },
];

export default function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[1.05fr_1fr]">
      <aside className="hidden bg-ink px-[var(--dp-spacing-gutter)] py-12 text-paper lg:flex lg:flex-col xl:py-14">
        <div className="flex items-center justify-between gap-4">
          <Brand light />
          <span className="border border-quiet-inverted px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.1em] text-quiet">
            Maharashtra · MVP
          </span>
        </div>

        <div className="mt-16 max-w-[34rem]">
          <p className="eyebrow text-quiet">Evidence-first due diligence</p>
          <h1 className="mt-5 font-display text-[clamp(48px,5.5cqw,82px)] font-medium leading-[0.98] tracking-[-0.035em] text-paper">
            Read the file.
            <br />
            Prove the chain.
          </h1>
          <p className="mt-6 max-w-md text-[15px] leading-[1.55] text-quiet">
            PropChain-AI turns Maharashtra property documents into structured evidence, checks them
            against each other, and traces the ownership chain — with every unknown stated plainly.
          </p>

          <ul className="mt-10 border-t border-quiet-inverted">
            {FEATURES.map((feature, index) => (
              <li
                key={feature.title}
                className="grid grid-cols-[2.5rem_1fr] gap-4 border-b border-quiet-inverted py-5"
              >
                <span className="grid h-9 w-9 place-items-center border border-quiet-inverted text-quiet">
                  <feature.icon className="h-[17px] w-[17px]" />
                </span>
                <div>
                  <p className="font-display text-[20px] leading-none text-paper">
                    {feature.title}
                  </p>
                  <p className="mt-1.5 text-[13px] leading-relaxed text-quiet">{feature.body}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="mt-auto max-w-md border-t border-quiet-inverted pt-5 font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-quiet">
          Findings are screening indicators for a reviewer — not legal determinations. Always confirm
          against government records and professional advice.
        </p>
      </aside>

      <main className="flex min-h-screen flex-col bg-paper px-5 py-8 sm:px-10 lg:px-14 lg:py-10">
        <div className="lg:hidden">
          <Brand />
        </div>

        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-[420px]">{children}</div>
        </div>

        <p className="text-center font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
          © {new Date().getFullYear()} PropChain-AI · Built for Maharashtra land records
        </p>
      </main>
    </div>
  );
}

import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Base({ children, className = "h-5 w-5", ...props }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const ArrowRight = (p: IconProps) => (
  <Base {...p}>
    <path d="M5 12h14" />
    <path d="m13 6 6 6-6 6" />
  </Base>
);

export const ArrowUpRight = (p: IconProps) => (
  <Base {...p}>
    <path d="M7 17 17 7" />
    <path d="M8 7h9v9" />
  </Base>
);

export const ArrowLeft = (p: IconProps) => (
  <Base {...p}>
    <path d="M19 12H5" />
    <path d="m11 18-6-6 6-6" />
  </Base>
);

export const Plus = (p: IconProps) => (
  <Base {...p}>
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </Base>
);

export const Mail = (p: IconProps) => (
  <Base {...p}>
    <rect x="3" y="5" width="18" height="14" rx="2.5" />
    <path d="m4 7 8 6 8-6" />
  </Base>
);

export const MapPin = (p: IconProps) => (
  <Base {...p}>
    <path d="M20 10c0 5.5-8 11-8 11s-8-5.5-8-11a8 8 0 1 1 16 0Z" />
    <circle cx="12" cy="10" r="2.5" />
  </Base>
);

export const Ruler = (p: IconProps) => (
  <Base {...p}>
    <path d="m3 17 14-14 4 4L7 21l-4-4Z" />
    <path d="m7.5 12.5 2 2" />
    <path d="m10.5 9.5 2 2" />
    <path d="m13.5 6.5 2 2" />
  </Base>
);

export const Hash = (p: IconProps) => (
  <Base {...p}>
    <path d="M5 9h14" />
    <path d="M5 15h14" />
    <path d="M10 4 8 20" />
    <path d="M16 4l-2 16" />
  </Base>
);

export const Calendar = (p: IconProps) => (
  <Base {...p}>
    <rect x="3.5" y="5" width="17" height="16" rx="3" />
    <path d="M8 3v4" />
    <path d="M16 3v4" />
    <path d="M3.5 10h17" />
  </Base>
);

export const ShieldCheck = (p: IconProps) => (
  <Base {...p}>
    <path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6l-7-3Z" />
    <path d="m9 12 2 2 4-4" />
  </Base>
);

export const ShieldAlert = (p: IconProps) => (
  <Base {...p}>
    <path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6l-7-3Z" />
    <path d="M12 8v5" />
    <path d="M12 16.5h.01" />
  </Base>
);

export const Flag = (p: IconProps) => (
  <Base {...p}>
    <path d="M5 21V4" />
    <path d="M5 5c4-2 7 2 14 0v9c-7 2-10-2-14 0" />
  </Base>
);

export const AlertTriangle = (p: IconProps) => (
  <Base {...p}>
    <path d="M10.3 4.3 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0Z" />
    <path d="M12 9v4" />
    <path d="M12 17h.01" />
  </Base>
);

export const Info = (p: IconProps) => (
  <Base {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5" />
    <path d="M12 8h.01" />
  </Base>
);

export const FileText = (p: IconProps) => (
  <Base {...p}>
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" />
    <path d="M14 3v5h5" />
    <path d="M9 13h6" />
    <path d="M9 17h4" />
  </Base>
);

export const UploadCloud = (p: IconProps) => (
  <Base {...p}>
    <path d="M7 17a4.5 4.5 0 0 1 .9-8.9A6 6 0 0 1 19.5 10a3.5 3.5 0 0 1-.5 7" />
    <path d="M12 12v8" />
    <path d="m8.5 15.5 3.5-3.5 3.5 3.5" />
  </Base>
);

export const Copy = (p: IconProps) => (
  <Base {...p}>
    <rect x="9" y="9" width="11" height="11" rx="2.5" />
    <path d="M15 6.5A2.5 2.5 0 0 0 12.5 4h-6A2.5 2.5 0 0 0 4 6.5v6A2.5 2.5 0 0 0 6.5 15" />
  </Base>
);

export const Check = (p: IconProps) => (
  <Base {...p}>
    <path d="m5 12.5 4.5 4.5L19 7" />
  </Base>
);

export const Download = (p: IconProps) => (
  <Base {...p}>
    <path d="M12 3v12" />
    <path d="m7 10 5 5 5-5" />
    <path d="M4 20h16" />
  </Base>
);

export const LogOut = (p: IconProps) => (
  <Base {...p}>
    <path d="M10 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4" />
    <path d="M15 8l4 4-4 4" />
    <path d="M9 12h10" />
  </Base>
);

export const Loader2 = (p: IconProps) => (
  <Base {...p}>
    <path d="M21 12a9 9 0 1 1-6.2-8.56" />
  </Base>
);

export const Sparkles = (p: IconProps) => (
  <Base {...p}>
    <path d="m12 4 1.6 4.4L18 10l-4.4 1.6L12 16l-1.6-4.4L6 10l4.4-1.6L12 4Z" />
    <path d="M18.5 15.5 19 17l1.5.5L19 18l-.5 1.5L18 18l-1.5-.5L18 17l.5-1.5Z" />
    <path d="M5.5 3.5 6 5l1.5.5L6 6l-.5 1.5L5 6l-1.5-.5L5 5l.5-1.5Z" />
  </Base>
);

export const Layers = (p: IconProps) => (
  <Base {...p}>
    <path d="m12 3 9 5-9 5-9-5 9-5Z" />
    <path d="m3 13 9 5 9-5" />
    <path d="m3 17 9 5 9-5" />
  </Base>
);

export const Link2 = (p: IconProps) => (
  <Base {...p}>
    <path d="M9 15.5 15.5 9" />
    <path d="M11 6.5 12.7 4.8a4 4 0 0 1 5.7 5.7L16.5 12" />
    <path d="M13 17.5 11.3 19.2a4 4 0 0 1-5.7-5.7L7.5 12" />
  </Base>
);

export const Lock = (p: IconProps) => (
  <Base {...p}>
    <rect x="4" y="10" width="16" height="11" rx="3" />
    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    <path d="M12 14.5v2" />
  </Base>
);

export const Eye = (p: IconProps) => (
  <Base {...p}>
    <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
    <circle cx="12" cy="12" r="3" />
  </Base>
);

export const EyeOff = (p: IconProps) => (
  <Base {...p}>
    <path d="M4 4.5 20 20.5" />
    <path d="M9.9 5.9A9.9 9.9 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-3 3.9" />
    <path d="M6.1 7.6A16.5 16.5 0 0 0 2.5 12S6 18.5 12 18.5a9.7 9.7 0 0 0 4.1-.9" />
    <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
  </Base>
);

export const Landmark = (p: IconProps) => (
  <Base {...p}>
    <path d="M3 9 12 4l9 5" />
    <path d="M5 9v9" />
    <path d="M9.5 9v9" />
    <path d="M14.5 9v9" />
    <path d="M19 9v9" />
    <path d="M3.5 21h17" />
  </Base>
);

export const Activity = (p: IconProps) => (
  <Base {...p}>
    <path d="M3 12h4l3-7 4 14 3-7h4" />
  </Base>
);

export const User = (p: IconProps) => (
  <Base {...p}>
    <circle cx="12" cy="8.5" r="3.5" />
    <path d="M5 20a7 7 0 0 1 14 0" />
  </Base>
);

export const KeyRound = (p: IconProps) => (
  <Base {...p}>
    <circle cx="8" cy="15" r="4" />
    <path d="m10.9 12.1 8-8" />
    <path d="m16.5 6.5 2 2" />
    <path d="m14.5 8.5 2 2" />
  </Base>
);

export const ChevronDown = (p: IconProps) => (
  <Base {...p}>
    <path d="m6 9 6 6 6-6" />
  </Base>
);

export const RefreshCw = (p: IconProps) => (
  <Base {...p}>
    <path d="M20 11a8 8 0 0 0-14.3-4.6L4 8" />
    <path d="M4 4v4h4" />
    <path d="M4 13a8 8 0 0 0 14.3 4.6L20 16" />
    <path d="M20 20v-4h-4" />
  </Base>
);

export const X = (p: IconProps) => (
  <Base {...p}>
    <path d="m6 6 12 12" />
    <path d="M18 6 6 18" />
  </Base>
);

export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return <Loader2 className={`${className} animate-spin`} />;
}

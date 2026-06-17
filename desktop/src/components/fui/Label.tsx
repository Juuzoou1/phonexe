import type { ReactNode } from "react";

/** Tiny ALL-CAPS tracked technical label (Latin/mono — never wrap Arabic). */
export function Label({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span dir="ltr" className={`fui-label text-fdim ${className}`}>
      {children}
    </span>
  );
}

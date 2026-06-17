import { useEffect, useRef } from "react";

/** RGB-split glitch text that fires a brief, rare burst (authentic, not constant). */
export function GlitchText({
  children,
  className = "",
}: {
  children: string;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    let t: number;
    const loop = () => {
      el.classList.add("is-glitching");
      window.setTimeout(() => el.classList.remove("is-glitching"), 160);
      t = window.setTimeout(loop, 3500 + Math.random() * 5000);
    };
    t = window.setTimeout(loop, 2200);
    return () => window.clearTimeout(t);
  }, []);
  return (
    <span ref={ref} className={`glitch ${className}`} data-text={children}>
      {children}
    </span>
  );
}

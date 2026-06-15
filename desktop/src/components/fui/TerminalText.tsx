import { useEffect, useState } from "react";

const SCRAMBLE = "ABCDEF0123456789#%&/<>*";

/** Char-by-char "decode" reveal (terminal/BIOS flavor); respects reduced-motion. */
export function TerminalText({
  text,
  className = "",
  speed = 24,
}: {
  text: string;
  className?: string;
  speed?: number;
}) {
  const [out, setOut] = useState(text);

  useEffect(() => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
      setOut(text);
      return;
    }
    let i = 0;
    let timer: number;
    const tick = () => {
      i += 1;
      const revealed = text.slice(0, i);
      const rest = text
        .slice(i)
        .split("")
        .map((c) => (c === " " ? " " : SCRAMBLE[(Math.random() * SCRAMBLE.length) | 0]))
        .join("");
      setOut(revealed + rest);
      if (i < text.length) timer = window.setTimeout(tick, speed);
    };
    tick();
    return () => window.clearTimeout(timer);
  }, [text, speed]);

  return <span className={className}>{out}</span>;
}

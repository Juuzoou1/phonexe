/** Deterministic SVG barcode strip from a seed string (poster micro-type). */
export function Barcode({
  seed = "phonexe",
  height = 16,
  className = "",
}: {
  seed?: string;
  height?: number;
  className?: string;
}) {
  const bars: { x: number; w: number }[] = [];
  let x = 0;
  for (let i = 0; i < seed.length * 4; i++) {
    const c = seed.charCodeAt(i % seed.length) + i * 7;
    const w = 1 + (c % 4);
    bars.push({ x, w });
    x += w + 1 + (c % 2);
  }
  return (
    <svg
      className={className}
      width={x}
      height={height}
      viewBox={`0 0 ${x} ${height}`}
      preserveAspectRatio="none"
      aria-hidden
    >
      {bars.map((b, i) =>
        i % 2 === 0 ? (
          <rect key={i} x={b.x} y={0} width={b.w} height={height} fill="currentColor" />
        ) : null,
      )}
    </svg>
  );
}

// Reusable SVG filter defs (mounted once): real 2-channel duotone for media
// + a turbulence/displacement glitch filter. Applied via filter:url(#id).
export function SvgFilterDefs() {
  return (
    <svg width="0" height="0" aria-hidden style={{ position: "absolute" }}>
      <defs>
        <filter id="duo-violet" colorInterpolationFilters="sRGB">
          <feColorMatrix
            type="matrix"
            values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 1 0"
          />
          <feComponentTransfer>
            <feFuncR type="table" tableValues="0.04 0.66" />
            <feFuncG type="table" tableValues="0.02 0.33" />
            <feFuncB type="table" tableValues="0.10 0.97" />
          </feComponentTransfer>
        </filter>
        <filter id="duo-blue" colorInterpolationFilters="sRGB">
          <feColorMatrix
            type="matrix"
            values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 1 0"
          />
          <feComponentTransfer>
            <feFuncR type="table" tableValues="0.04 0.10" />
            <feFuncG type="table" tableValues="0.06 0.65" />
            <feFuncB type="table" tableValues="0.10 1.0" />
          </feComponentTransfer>
        </filter>
        <filter id="glitch">
          <feTurbulence type="fractalNoise" baseFrequency="0 0.0001" numOctaves="1" seed="7" result="n">
            <animate attributeName="baseFrequency" dur="6s" keyTimes="0;0.04;0.08;1"
              values="0 0.0001;0 0.02;0 0.0001;0 0.0001" repeatCount="indefinite" />
          </feTurbulence>
          <feDisplacementMap in="SourceGraphic" in2="n" scale="9"
            xChannelSelector="R" yChannelSelector="G" />
        </filter>
      </defs>
    </svg>
  );
}

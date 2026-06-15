// Non-WebGL / reduced-motion fallback: a dim, static colored-box field on black.
export function StaticVoidFallback() {
  return (
    <div
      className="fixed inset-0 -z-10 bg-black"
      style={{
        backgroundImage: [
          "radial-gradient(2px 2px at 20% 30%, rgba(79,227,224,.5), transparent)",
          "radial-gradient(2px 2px at 70% 40%, rgba(168,85,247,.5), transparent)",
          "radial-gradient(2px 2px at 45% 65%, rgba(33,243,138,.45), transparent)",
          "radial-gradient(2px 2px at 60% 75%, rgba(36,168,255,.45), transparent)",
          "radial-gradient(2px 2px at 35% 50%, rgba(255,45,155,.4), transparent)",
          "radial-gradient(60% 50% at 50% 45%, rgba(36,168,255,.10), transparent)",
        ].join(","),
      }}
    />
  );
}

// Scanlines + faint flicker + vignette over the whole shell (DOM, not WebGL).
export function CrtOverlay() {
  return (
    <>
      <div className="crt-vignette" />
      <div className="grain-overlay" />
      <div className="crt-overlay" />
    </>
  );
}

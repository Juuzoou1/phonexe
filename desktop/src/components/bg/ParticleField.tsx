import { Canvas } from "@react-three/fiber";
import { PointCluster } from "./PointCluster";
import { PostFx } from "./PostFx";
import { StaticVoidFallback } from "./StaticVoidFallback";

const reduceMotion =
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

function webglAvailable(): boolean {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

/** Fixed, full-bleed hero: the animated multicolor box cluster on pure black. */
export function ParticleField() {
  if (reduceMotion || !webglAvailable()) return <StaticVoidFallback />;
  return (
    <div className="fixed inset-0 -z-10 bg-black pointer-events-none">
      <Canvas
        dpr={[1, 1.5]}
        gl={{ antialias: false, powerPreference: "high-performance" }}
        camera={{ position: [0, 0, 9], fov: 62 }}
      >
        <PointCluster />
        <PostFx />
      </Canvas>
    </div>
  );
}

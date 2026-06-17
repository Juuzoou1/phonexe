import { useMemo } from "react";
import {
  EffectComposer,
  Bloom,
  ChromaticAberration,
  Scanline,
  Glitch,
} from "@react-three/postprocessing";
import { BlendFunction, GlitchMode } from "postprocessing";
import { Vector2 } from "three";

// One composer for the whole app (perf contract). Glitch is SPORADIC + brief.
export function PostFx() {
  const caOffset = useMemo(() => new Vector2(0.0007, 0.0011), []);
  const gDelay = useMemo(() => new Vector2(3.5, 7), []);
  const gDuration = useMemo(() => new Vector2(0.1, 0.24), []);
  const gStrength = useMemo(() => new Vector2(0.1, 0.32), []);

  return (
    <EffectComposer multisampling={0}>
      <Bloom
        intensity={1.0}
        luminanceThreshold={0.04}
        luminanceSmoothing={0.9}
        mipmapBlur
      />
      <ChromaticAberration
        blendFunction={BlendFunction.NORMAL}
        offset={caOffset}
        radialModulation={false}
        modulationOffset={0}
      />
      <Scanline blendFunction={BlendFunction.OVERLAY} density={1.25} opacity={0.1} />
      <Glitch
        mode={GlitchMode.SPORADIC}
        delay={gDelay}
        duration={gDuration}
        strength={gStrength}
        ratio={0.85}
      />
    </EffectComposer>
  );
}

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

// HERO-ONLY multicolor palette (the single place rainbow is allowed).
const PALETTE: [number, number, number][] = [
  [0.31, 0.89, 0.88], // #4FE3E0 cyan
  [0.14, 0.66, 1.0], // #24A8FF blue
  [0.66, 0.33, 0.97], // #A855F7 violet
  [0.13, 0.95, 0.54], // #21F38A green
  [1.0, 0.18, 0.61], // #FF2D9B magenta
  [1.0, 1.0, 1.0], // white sparks
];

// Camera-facing instanced quads (NOT gl_PointSize points — those clamp to 1px
// under software WebGL). Each instance is a small colored box; the cluster
// drifts and every box flickers independently.
// NOTE: don't declare attribute position/uv — three's ShaderMaterial injects
// them. We pass the quad corner (position.xy, range ±0.5) to build a round dot.
const VERT = /* glsl */ `
attribute vec3 iOffset;
attribute vec3 iColor;
attribute float iSeed;
uniform float uTime;
uniform float uSize;
varying vec3 vColor;
varying float vSeed;
varying vec2 vQuad;
void main() {
  vColor = iColor;
  vSeed = iSeed;
  vQuad = position.xy;                  // ±0.5 quad corner -> circle in frag
  // slow, gentle drift (calm)
  vec3 drift = 0.16 * sin(uTime * vec3(0.35, 0.45, 0.3) + iSeed);
  vec4 mv = modelViewMatrix * vec4(iOffset + drift, 1.0);
  float s = uSize * (0.75 + 0.25 * sin(uTime * 0.9 + iSeed));
  mv.xy += position.xy * s;             // billboard the quad toward the camera
  gl_Position = projectionMatrix * mv;
}
`;

// Soft ROUND dots (discard outside the inscribed circle), gentle flicker.
const FRAG = /* glsl */ `
precision highp float;
varying vec3 vColor;
varying float vSeed;
varying vec2 vQuad;
uniform float uTime;
void main() {
  float d = length(vQuad);             // 0 at centre, 0.5 at edge midpoint
  float dot = smoothstep(0.5, 0.04, d);
  if (dot <= 0.01) discard;
  float f = 0.5 + 0.5 * fract(sin(vSeed + floor(uTime * 3.5)) * 43758.5453);
  gl_FragColor = vec4(vColor, dot * mix(0.5, 1.0, f));
}
`;

export function PointCluster() {
  const mesh = useMemo(() => {
    const N = 4800;
    const base = new THREE.PlaneGeometry(1, 1);
    const geo = new THREE.InstancedBufferGeometry();
    geo.index = base.index;
    geo.setAttribute("position", base.attributes.position);
    geo.setAttribute("uv", base.attributes.uv);

    const off = new Float32Array(N * 3);
    const col = new Float32Array(N * 3);
    const seed = new Float32Array(N);
    for (let i = 0; i < N; i++) {
      // wider, more even spread so the field covers the whole backdrop
      const r = Math.pow(Math.random(), 0.85) * 9.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      off[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      off[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      off[i * 3 + 2] = r * Math.cos(phi) * 0.4;
      const c = PALETTE[(Math.random() * PALETTE.length) | 0];
      col[i * 3] = c[0];
      col[i * 3 + 1] = c[1];
      col[i * 3 + 2] = c[2];
      seed[i] = Math.random() * 1000;
    }
    geo.setAttribute("iOffset", new THREE.InstancedBufferAttribute(off, 3));
    geo.setAttribute("iColor", new THREE.InstancedBufferAttribute(col, 3));
    geo.setAttribute("iSeed", new THREE.InstancedBufferAttribute(seed, 1));
    geo.instanceCount = N;

    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0 }, uSize: { value: 0.18 } },
    });
    return new THREE.Mesh(geo, mat);
  }, []);

  const meshRef = useRef(mesh);
  meshRef.current = mesh;

  useFrame((state) => {
    const m = mesh.material as THREE.ShaderMaterial;
    m.uniforms.uTime.value = state.clock.elapsedTime;
  });

  return <primitive object={mesh} />;
}

// SPDX-License-Identifier: MIT
/**
 * Procedural low-poly "forest of avoided emissions" (React Three Fiber).
 *
 * Aesthetic: organic / biomorphic, golden-hour calm — a small green island with
 * faceted trees that grow in on mount, gently turning. Engineering: everything
 * is generated in code (zero GLTF/texture/HDRI binaries), trunks and foliage are
 * each a single InstancedMesh (≈4 draw calls total), DPR is capped at 2, and no
 * objects are allocated inside the render loop (one shared dummy reused). This
 * module is the default export so it can be `React.lazy`-loaded into its own
 * async chunk; callers gate it behind reduced-motion / WebGL checks.
 */

import { useLayoutEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, type ThreeEvent } from "@react-three/fiber";
import * as THREE from "three";

import { treeCountForSaved } from "./savingsModel";

interface SavingsSceneProps {
  savedKg: number;
}

interface TreePlacement {
  x: number;
  z: number;
  scale: number;
  delay: number;
}

const ISLAND_RADIUS = 4.2;
const GROW_DURATION = 0.7;
const TRUNK_HEIGHT = 0.6;
const FOLIAGE_HEIGHT = 0.9;

/** Deterministic pseudo-random in [0,1) from an integer seed (no allocation). */
function seeded(seed: number): number {
  const value = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return value - Math.floor(value);
}

/** Even, natural-looking placement via the golden-angle spiral. */
function placeTrees(count: number): TreePlacement[] {
  const golden = Math.PI * (3 - Math.sqrt(5));
  const trees: TreePlacement[] = [];
  for (let i = 0; i < count; i += 1) {
    const t = (i + 0.5) / count;
    const radius = ISLAND_RADIUS * 0.86 * Math.sqrt(t);
    const theta = i * golden;
    const jitter = (seeded(i) - 0.5) * 0.5;
    trees.push({
      x: radius * Math.cos(theta) + jitter,
      z: radius * Math.sin(theta) - jitter,
      scale: 0.8 + seeded(i + 99) * 0.6,
      delay: t * 1.1,
    });
  }
  return trees;
}

/** Shared scratch object — reused every frame so the loop allocates nothing. */
const dummy = new THREE.Object3D();

function Forest({ savedKg }: SavingsSceneProps) {
  const count = treeCountForSaved(savedKg);
  const trees = useMemo(() => placeTrees(count), [count]);

  const trunkRef = useRef<THREE.InstancedMesh>(null);
  const foliageRef = useRef<THREE.InstancedMesh>(null);
  const groupRef = useRef<THREE.Group>(null);
  const grownRef = useRef(false);
  const pointerRef = useRef({ dragging: false, lastX: 0, spin: 0 });

  const writeMatrices = (progressFor: (tree: TreePlacement) => number) => {
    const trunk = trunkRef.current;
    const foliage = foliageRef.current;
    if (!trunk || !foliage) return;
    for (let i = 0; i < trees.length; i += 1) {
      const tree = trees[i];
      if (!tree) continue;
      const grow = progressFor(tree);
      const scale = tree.scale * grow;

      dummy.position.set(tree.x, (TRUNK_HEIGHT * 0.5) * scale, tree.z);
      dummy.scale.set(scale, scale, scale);
      dummy.rotation.set(0, seeded(i + 7) * Math.PI, 0);
      dummy.updateMatrix();
      trunk.setMatrixAt(i, dummy.matrix);

      dummy.position.set(
        tree.x,
        (TRUNK_HEIGHT + FOLIAGE_HEIGHT * 0.5) * scale,
        tree.z,
      );
      dummy.updateMatrix();
      foliage.setMatrixAt(i, dummy.matrix);
    }
    trunk.instanceMatrix.needsUpdate = true;
    foliage.instanceMatrix.needsUpdate = true;
  };

  // Seed the instances at zero scale so the first frame isn't a full forest.
  useLayoutEffect(() => {
    grownRef.current = false;
    writeMatrices(() => 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trees]);

  function easeOut(x: number): number {
    return 1 - Math.pow(1 - x, 3);
  }

  useFrame((state, delta) => {
    const group = groupRef.current;
    if (group) {
      const pointer = pointerRef.current;
      if (!pointer.dragging) pointer.spin += delta * 0.12;
      group.rotation.y = pointer.spin;
    }

    if (!grownRef.current) {
      const elapsed = state.clock.elapsedTime;
      // `allDone` is mutated from inside the per-tree callback below (a closure)
      // so one pass both writes the matrices and reports whether every tree has
      // finished growing — avoiding a second loop over the instances each frame.
      let allDone = true;
      writeMatrices((tree) => {
        const local = (elapsed - tree.delay) / GROW_DURATION;
        if (local < 1) allDone = false;
        return easeOut(Math.min(1, Math.max(0, local)));
      });
      if (allDone) grownRef.current = true;
    }
  });

  const onPointerDown = (event: ThreeEvent<PointerEvent>) => {
    pointerRef.current.dragging = true;
    pointerRef.current.lastX = event.clientX;
  };
  const onPointerMove = (event: ThreeEvent<PointerEvent>) => {
    const pointer = pointerRef.current;
    if (!pointer.dragging) return;
    pointer.spin += (event.clientX - pointer.lastX) * 0.01;
    pointer.lastX = event.clientX;
  };
  const endDrag = () => {
    pointerRef.current.dragging = false;
  };

  return (
    <group
      ref={groupRef}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerLeave={endDrag}
    >
      {/* Island platform */}
      <mesh receiveShadow position={[0, -0.35, 0]}>
        <cylinderGeometry args={[ISLAND_RADIUS, ISLAND_RADIUS * 0.82, 0.7, 32]} />
        <meshStandardMaterial color="#2f8f5b" roughness={0.95} flatShading />
      </mesh>
      <mesh position={[0, 0.02, 0]}>
        <cylinderGeometry args={[ISLAND_RADIUS * 0.98, ISLAND_RADIUS * 0.98, 0.08, 32]} />
        <meshStandardMaterial color="#4fb07a" roughness={0.9} flatShading />
      </mesh>

      <instancedMesh
        ref={trunkRef}
        args={[undefined, undefined, Math.max(count, 1)]}
        castShadow
      >
        <cylinderGeometry args={[0.07, 0.1, TRUNK_HEIGHT, 5]} />
        <meshStandardMaterial color="#7a4a25" roughness={1} flatShading />
      </instancedMesh>

      <instancedMesh
        ref={foliageRef}
        args={[undefined, undefined, Math.max(count, 1)]}
        castShadow
      >
        <coneGeometry args={[0.5, FOLIAGE_HEIGHT, 6]} />
        <meshStandardMaterial color="#1f7a4d" roughness={0.85} flatShading />
      </instancedMesh>
    </group>
  );
}

export default function SavingsScene({ savedKg }: SavingsSceneProps) {
  const label = `An interactive 3D forest representing ${treeCountForSaved(
    savedKg,
  )} trees of avoided emissions. Drag to rotate.`;

  return (
    <div className="savings-canvas" role="img" aria-label={label}>
      <Canvas
        dpr={[1, 2]}
        shadows
        camera={{ position: [0, 4.5, 9], fov: 42 }}
        gl={{ antialias: true, powerPreference: "high-performance" }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.05;
        }}
      >
        <color attach="background" args={["#eaf4ee"]} />
        <fog attach="fog" args={["#eaf4ee", 12, 26]} />

        <hemisphereLight args={["#fdf3d8", "#26543a", 0.85]} />
        <directionalLight
          position={[6, 9, 4]}
          intensity={1.5}
          color="#ffe6b0"
          castShadow
          shadow-mapSize-width={1024}
          shadow-mapSize-height={1024}
        />

        <Forest savedKg={savedKg} />
      </Canvas>
    </div>
  );
}

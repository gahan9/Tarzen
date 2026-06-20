# 3D Web Tech Playbook

Deep-dive companion to `SKILL.md`. Read the section you need; don't load it all.

## Stack & libraries

| Concern | Library | Notes |
|---------|---------|-------|
| Core renderer | `three` | WebGL by default; `WebGPURenderer` + TSL for compute-heavy/instanced work |
| React bindings | `@react-three/fiber` | Declarative scene graph; `useFrame` for the loop |
| Helpers | `@react-three/drei` | Controls, loaders, `Environment`, `Html`, `useProgress`, `Bvh` |
| Postprocessing | `postprocessing` + `@react-three/postprocessing` | Bloom, DOF, SSAO, vignette — measure cost |
| Loaders/compression | `GLTFLoader` + `DRACOLoader` + `KTX2Loader` + `meshopt` | Compressed geometry & textures |
| Timeline / scroll | `gsap` (+ ScrollTrigger), drei `ScrollControls` | Choreography and scroll-driven scenes |
| UI/spring motion | `framer-motion`, `@react-spring/three` | HTML overlays and physical springs |
| Physics | `@react-three/rapier` | Rapier WASM; deterministic, fast |
| XR | `@react-three/xr` | WebXR sessions, controllers, hands |
| Profiling | `r3f-perf`, `stats.js`, `three`'s `renderer.info` | Draw calls, triangles, frame time |

## Asset pipeline (the biggest perf lever)

1. **Geometry**: export `.glb` (binary), not `.gltf`+bin+textures. Compress with
   **Draco** or **meshopt**. Decimate in Blender; you rarely need full-res CAD.
2. **Textures**: convert to **KTX2 / Basis Universal** (GPU-compressed, stays
   compressed in VRAM). Keep power-of-two sizes; generate mipmaps. Use `gltf-transform`:
   ```bash
   npx @gltf-transform/cli optimize in.glb out.glb --texture-compress ktx2
   ```
3. **Environment**: prefer a small `.hdr`/`.exr` for IBL over many lights; drei's
   `<Environment preset=... />` is a fast start.
4. **Budget per asset**. Decide a download budget for the hero up front and hold
   the line. Lazy-load everything below the fold / after first interaction.

## Render-loop discipline

- Never `new THREE.Vector3()` / allocate inside `useFrame`. Hoist scratch objects
  to module/instance scope and mutate them.
- Throttle non-essential work (raycasting, expensive updates) off the 60Hz path.
- Use `frameloop="demand"` (R3F) for static scenes that only change on input —
  huge battery/CPU win.
- Dispose on unmount: geometries, materials, textures, render targets. Watch
  React StrictMode's double-mount; guard so you don't dispose shared resources.

## Cutting draw calls

- **InstancedMesh** for many copies of one geometry (forests, crowds, particles).
- **Merge** static geometries (`BufferGeometryUtils.mergeGeometries`).
- Share materials; avoid a unique material per mesh.
- Enable frustum culling (default on) and add **LOD** for distant detail.
- Use a **BVH** (`three-mesh-bvh` / drei `Bvh`) for fast raycasting on big meshes.

## Lighting & materials for "the look"

- Start with `MeshStandardMaterial`/`MeshPhysicalMaterial` + an HDRI environment;
  tune `roughness`/`metalness`/`transmission` before writing shaders.
- Limit real-time lights; bake where possible. Each shadow-casting light is
  expensive — prefer 1 shadow light + soft contact shadows (`<ContactShadows>`).
- Set `renderer.toneMapping = ACESFilmicToneMapping` and correct color space
  (`SRGBColorSpace`) for filmic, non-washed-out output.

## Shaders (GLSL / TSL)

- Reach for shaders for effects standard materials can't do: dissolve,
  iridescence, vertex displacement, procedural patterns, GPU particles.
- In R3F use `shaderMaterial` (drei) to define `uniforms`/`vertexShader`/
  `fragmentShader`; drive uniforms in `useFrame` (mutate `.value`, don't realloc).
- Keep fragment shaders cheap — they run per-pixel. Move math to the vertex
  shader or precompute when you can. Avoid branches and big loops in fragments.
- WebGPU/TSL: prefer for compute (GPGPU particles, simulations) and when you want
  node-based materials without raw GLSL.

## Postprocessing (use sparingly)

- `EffectComposer` adds full-screen passes; each one costs fill-rate. Bloom and
  SSAO are the usual budget-killers.
- Lazy-init the composer; skip it entirely on the low-end tier.
- Many "glow" looks are cheaper via emissive materials + a single Bloom than via
  multiple passes.

## Scroll- & input-driven scenes

- drei `ScrollControls` + `useScroll` for scroll-tied camera/animation; GSAP
  ScrollTrigger when you need timeline precision and pinning.
- Clamp `OrbitControls` (`minPolarAngle`/`maxPolarAngle`, `minDistance`/
  `maxDistance`, `enablePan=false`) so users can't get lost or clip through geometry.
- Provide a "reset view" and an idle auto-orbit that stops on interaction.

## Performance budgets & verification

| Metric | Desktop | Mobile | How to check |
|--------|---------|--------|--------------|
| Frame time | ≤ 16.6ms | ≤ 16.6ms (degrade if not) | `r3f-perf`, DevTools Performance |
| Draw calls | < ~150 | < ~50–80 | `renderer.info.render.calls` |
| Triangles | a few M | < 1M | `renderer.info.render.triangles` |
| Programs/materials | low, stable | low, stable | `renderer.info.programs` |
| `devicePixelRatio` | cap ≈ ≤2 | cap ≈ ≤1.5–2 | `gl.setPixelRatio(Math.min(window.devicePixelRatio, 2))` |
| WebXR | 72–90+ fps | — | headset stats / no dropped frames |

Workflow: **measure → find the dominant cost (draw calls? fill-rate? CPU? GC?) →
fix that one thing → re-measure.** Test on the device floor, watch for thermal
throttling on sustained scenes.

## Accessibility & fallback recipes

- Detect support before mounting; on failure render an `<img>`/`<video>`/HTML hero.
- Listen for `webglcontextlost` / `webglcontextrestored`; pause and recover or
  fall back gracefully.
- Gate motion on `window.matchMedia('(prefers-reduced-motion: reduce)')`.
- Mirror key 3D interactions in real, focusable HTML controls (drei `<Html>` or a
  sibling DOM layer) so keyboard and screen-reader users have a path.
- Auto-tier: if median fps over a few seconds is low, drop DPR, disable
  postprocessing, and reduce particle/instance counts.

## Reference links

- Three.js manual & examples: <https://threejs.org/docs/>, <https://threejs.org/examples/>
- React Three Fiber: <https://r3f.docs.pmnd.rs/> · drei: <https://drei.docs.pmnd.rs/>
- Discover Three.js (book): <https://discoverthreejs.com/> · Bruno Simon course: <https://threejs-journey.com/>
- gltf-transform: <https://gltf-transform.dev/> · KTX2/Basis: <https://github.khronos.org/KTX-Software/>
- WebGPU fundamentals: <https://webgpufundamentals.org/> · The Book of Shaders: <https://thebookofshaders.com/>
- WebXR: <https://immersiveweb.dev/>

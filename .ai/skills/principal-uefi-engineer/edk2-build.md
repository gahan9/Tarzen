# EDK II Build System, File Formats & CI (Reference)

Repos: `edk2` (core), `edk2-platforms` (boards/silicon), `edk2-non-osi` (binary blobs). Tooling: BaseTools + edk2-pytool-extensions/library (Stuart).

## Workspace & toolchains

- **WORKSPACE**: top-level working dir. **PACKAGES_PATH**: colon/semicolon-separated list of repo roots the build searches for `.dsc`/INF resolution.
- Toolchain tags: `GCC5` (gcc 5+), `CLANGPDB`/`CLANGDWARF`, `VS2019`/`VS2022` (Windows). Cross prefixes via `{TAG}_{ARCH}_PREFIX` (e.g., `GCC5_AARCH64_PREFIX=aarch64-linux-gnu-`).
- `TARGET`: `DEBUG` | `RELEASE` | `NOOPT`. `-a` arch (`IA32`,`X64`,`AARCH64`,`ARM`,`RISCV64`,`LOONGARCH64`). `-n` parallelism.

## Two build flows

```bash
# Classic
. edk2/edksetup.sh
make -C edk2/BaseTools
build -a X64 -t GCC5 -p OvmfPkg/OvmfPkgX64.dsc -b DEBUG

# Stuart (CI parity, self-managed deps)
pip install -r edk2/pip-requirements.txt
stuart_setup  -c <PlatformBuild.py>
stuart_update -c <PlatformBuild.py>
stuart_build  -c <PlatformBuild.py> TOOL_CHAIN_TAG=GCC5 -a X64
# Core/package CI (unit tests + checks):
stuart_ci_build -c .pytool/CISettings.py TOOL_CHAIN_TAG=GCC5 -a X64,IA32
```

Output firmware volumes: `Build/{Platform}/{TARGET}_{TOOLCHAIN}/FV/`.

## File formats (the four you must know)

- **DEC** (`*.dec`) — *package declaration*. Declares the package's public GUIDs, protocols/PPIs, PCDs, and include paths. The package's published interface.
- **INF** (`*.inf`) — *module definition*. One per module: `[Sources]`, `[Packages]`, `[LibraryClasses]`, `[Protocols]`/`[Ppis]`/`[Guids]`, `[Pcd]`, `[Depex]`, and `MODULE_TYPE` (e.g., `PEIM`, `DXE_DRIVER`, `DXE_RUNTIME_DRIVER`, `UEFI_DRIVER`, `DXE_SMM_DRIVER`, `MM_STANDALONE`, `UEFI_APPLICATION`, `HOST_APPLICATION`).
- **DSC** (`*.dsc`) — *platform description*. What to build and how: `[LibraryClasses]` mappings (class -> instance), `[Components]` (module list), `[PcdsFixedAtBuild]`/`[PcdsDynamic]`, build options. **This is where vendor-agnostic wiring happens.**
- **FDF** (`*.fdf`) — *flash description*. Physical layout of the flash image: firmware volumes (FV), FD regions, file placement, compression, capsule layout.

## PCDs (Platform Configuration Database)

Mechanism to parameterize code without `#ifdef`. Types by binding time/scope:

- `FixedAtBuild` — constant baked at build (smallest/fastest).
- `PatchableInModule` — patchable in the binary post-build.
- `Dynamic` / `DynamicEx` — runtime-settable (HII/setup, board logic); `Ex` adds a token-space GUID for cross-module access.
- `FeatureFlag` — boolean feature gates.

Principle: prefer PCDs + library classes for board/silicon variation; keep `Silicon/{Vendor}` and `Platform/{Vendor}/{Board}` thin and declarative.

## Library classes & instances

- A **library class** (declared in DEC, header in `Include/Library/`) is an interface; a **library instance** (an INF with `LIBRARY_CLASS`) implements it. The DSC binds class->instance per module type.
- Use `NULL` library classes for constructor-injected behavior (e.g., serial-port hooks).
- This is the primary abstraction for vendor-agnostic + arch-agnostic code.

## CI & quality gates

- Core CI matrix builds Windows VS / Ubuntu GCC / CLANGPDB / CLANGDWARF across DEBUG/RELEASE/NOOPT (see edk2 README badges).
- Plugins: compiler warnings-as-errors, `EccCheck` (coding standard), spell/markdown lint, dependency/`GuidCheck`, host-based unit tests.
- Run `stuart_ci_build` locally before sending patches to match upstream gates.

## Debugging

- **OVMF + QEMU (x86)**: build `OvmfPkgX64.dsc`, boot the `.fd`; enable debug serial (`DEBUG_ON_SERIAL_PORT`). Wiki: "How to debug OVMF with QEMU using GDB" / "...using WinDbg".
- **ArmVirt + QEMU (AARCH64)**: `ArmVirtQemu.dsc`; GDB attach via QEMU `-s -S`, load symbols from the per-module `.debug`/`.dll` with the runtime load address from the DEBUG log.
- **Source-level debug**: `SourceLevelDebugPkg` (Intel) for hardware/Simics; `EmulatorPkg` for host-OS hosted debugging.
- **Logging**: `DEBUG((DEBUG_INFO, ...))`, `ASSERT`, `RETURN_STATUS`; status-code (`ReportStatusCode`) for progress/error in production.
- **Profiling/analysis**: memory profile feature, SMI handler profile, Host-Based Firmware Analyzer.

## Useful entry points

- New module: start from a sibling INF in the relevant package; declare deps in `[Packages]`, list the library classes, set `MODULE_TYPE`/`ENTRY_POINT`, write the depex.
- New board: follow **MinPlatform** (`Platform/Intel/MinPlatformPkg`) — split into board-agnostic core + board overrides; scalable, well-documented porting model.
- Capsule/firmware update: `FmpDevicePkg` + `SignedCapsulePkg`; see wiki "Capsule Based System Firmware Update".

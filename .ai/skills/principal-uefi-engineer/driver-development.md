# UEFI Driver Development: Patterns, Arch, Tables & Testing (Reference)

## Step 0 — Decide driver type before coding

| Type | `MODULE_TYPE` | Runs in | Use for |
|------|---------------|---------|---------|
| PEIM | `PEIM` | PEI | Early/pre-DRAM init, memory init, S3 helpers |
| DXE driver | `DXE_DRIVER` | DXE | Platform/chipset init, producing protocols |
| UEFI driver | `UEFI_DRIVER` | DXE/BDS | I/O devices via UEFI Driver Model (bus/device) |
| Runtime driver | `DXE_RUNTIME_DRIVER` | DXE->RT | Services callable after `ExitBootServices` |
| SMM driver | `DXE_SMM_DRIVER` | SMM (x86) | Privileged handlers (variable, security) |
| Standalone MM | `MM_STANDALONE` | MM | Isolated MM (ARM/modern x86) |
| Application | `UEFI_APPLICATION` | DXE/Shell | Tools, OS loaders, tests |

## UEFI Driver Model (for device drivers)

Implement `EFI_DRIVER_BINDING_PROTOCOL`:

- **Supported()** — fast, side-effect-free check that this driver manages the given controller (test device-path/protocols). Open protocols `BY_DRIVER` to test.
- **Start()** — install child handles/protocols, open parent protocols `BY_DRIVER`, build device state.
- **Stop()** — release everything Start() acquired; must be idempotent and leak-free.
- Add `Component Name 2` (human-readable names) and, where relevant, `Driver Diagnostics 2` / `Driver Configuration`.
- Respect protocol open modes (`BY_DRIVER`, `EXCLUSIVE`, `GET_PROTOCOL`) and the handle database; never leak `OpenProtocol` references.

## Vendor-agnostic vs vendor-specific design

Goal: maximize reuse, isolate silicon. Layering (highest to lowest):

1. **Generic core** — `MdeModulePkg`/`NetworkPkg` etc. Vendor-neutral; reuse, don't fork.
2. **Library classes** — express behavioral differences as swappable instances (DSC binds class->instance). Arch and vendor differences hide here.
3. **PCDs / Configuration Manager** — express *data* differences (addresses, sizes, feature flags, table contents) as configuration, not code.
4. **`Silicon/{Vendor}`** — silicon-specific drivers/libraries (register defs, reference code, FSP wrappers).
5. **`Platform/{Vendor}/{Board}`** — board glue: DSC/FDF, board-specific PCD values, GPIO/clock tables.

Anti-pattern: `#ifdef VENDOR_X` forests in shared code. Replace with a library class or PCD. Cite this in reviews as Recommended/Critical depending on blast radius.

## x86 vs ARM specifics

**x86 (IA32/X64)**

- Silicon init often via **FSP** (`IntelFsp2Pkg`/Wrapper) — binary memory/silicon init called from PEI; or native MRC.
- **SMM** for privileged operations; **MP services** (`UefiCpuPkg`) for multi-core bring-up; legacy/CSM concerns (largely deprecated).
- Boot flow: SEC (CAR) -> FSP/MRC in PEI -> DXE.

**ARM (AARCH64)**

- Platform boot stack: BL1/BL2 (TF-A) -> **BL31 (EL3 runtime, PSCI)** -> UEFI as BL33. UEFI uses **PSCI** for CPU on/off/reset.
- Description via **ACPI** (servers, SBBR/BSA compliance) and/or **Device Tree** (embedded). **GIC** for interrupts; **Standalone MM** at S-EL0 for secure services.
- Use `ArmPkg`/`ArmPlatformPkg` library classes; keep EL3/secure handoff assumptions explicit.

Keep all of the above behind library classes so the same generic drivers serve both arches.

## ACPI, SMBIOS & dynamic tables

- **Static**: install `.aml`/`.asl` (ASL compiled by iASL) and SMBIOS records directly — simple, but per-board and error-prone at scale.
- **DynamicTablesPkg (preferred for scale)**: a **Configuration Manager** supplies platform data; generators emit ACPI/SMBIOS tables programmatically. Vendor-agnostic, less duplication, easier multi-board maintenance.
- Validate ACPI against **ACPI 6.6**; validate SMBIOS against the **DMTF SMBIOS** spec. Run OS-side checkers (e.g., `acpidump`/`iasl -d`, FWTS) during bring-up.

## Security in drivers (review every time)

- **SMM/MM**: validate every field of the `CommBuffer`; never trust pointers/lengths from the OS; check buffer is outside SMRAM; guard against TOCTOU and integer overflow.
- **Variables**: use **Variable Policy** and authenticated variables for security-sensitive data; respect `BS`/`RT`/`NV` attribute semantics.
- **Secure/measured boot**: image authentication (`SecurityPkg`), extend PCRs for measured boot (`TcgTpmPkg`), capsule signing for updates.
- **Crypto**: use `CryptoPkg` (OpenSSL/MbedTLS) — do not roll your own. For attestation/secure transport consider **SPDM** (`libspdm`, DMTF).
- Treat untrusted FVs, network input, and OS->firmware boundaries as hostile.

## Testing strategy (shift left)

1. **Host-based unit tests** — `UnitTestFrameworkPkg` (cmocka / GoogleTest), `MODULE_TYPE = HOST_APPLICATION`. Test pure logic off-target; runs in CI on every patch. Mock protocols/PPIs.
2. **Emulation** — `EmulatorPkg` (host OS), OVMF/ArmVirt on QEMU for integration without silicon.
3. **Conformance** — **UEFI SCT** (`edk2-test`) for spec compliance of produced protocols/services.
4. **Functional** — **UEFI Shell 2.2** scripts (`.nsh`) driving the platform; `dh`, `drivers`, `devtree`, `memmap`, `pci`, `smbiosview`, `acpiview` for inspection.
5. **On-silicon** — serial DEBUG logs, status codes, source-level debug (SourceLevelDebugPkg), and POST-code/telemetry.

Aim: every new logic path has a host-based test; every produced protocol has SCT coverage; every board has a shell smoke script.

## Review checklist (driver-specific)

- Correct `MODULE_TYPE` and phase; depex lists real dependencies.
- Driver Binding `Stop()` fully reverses `Start()`; no protocol/handle leaks.
- All error paths free resources and return precise `EFI_STATUS`/`RETURN_STATUS`.
- No Boot Services calls in runtime/`AfterExitBootServices` paths.
- Silicon/board specifics isolated via library class + PCD, not `#ifdef`.
- Security boundaries validated (SMM CommBuffer, variable attributes, image auth).
- Tables (ACPI/SMBIOS) generated via Configuration Manager where feasible and spec-validated.

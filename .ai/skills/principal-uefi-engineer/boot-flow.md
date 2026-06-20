# PI / UEFI Boot Flow (Reference)

Source of truth: PI Specification 1.9 (Vols 1–5) and UEFI 2.11. Wiki summary: <https://github.com/tianocore/tianocore.github.io/wiki/PI-Boot-Flow>.

Anchor every design and review to the correct phase. Wrong-phase logic (e.g., heavy work in PEI, boot-services calls at runtime, allocations in SMM from untrusted input) is the most common and most dangerous firmware error.

## SEC — Security

- First code after reset; handles all platform restart events.
- Establishes the **root of trust** (verified/measured boot anchor) and creates **temporary memory** (Cache-as-RAM on x86; on-chip SRAM/CAR on ARM) for an early stack.
- Passes mandatory handoff to PEI Core; may pass optional PPIs (e.g., SEC Platform Information, processor health).
- Mostly assembly; keep it minimal and fault-tolerant.

## PEI — Pre-EFI Initialization

- Invoked early after SEC on every restart. Runs from temporary memory until permanent DRAM is initialized.
- **PEIMs** (PEI Modules) are dispatched by the PEI Foundation, gated by **PPI**-based dependency expressions (depex).
- Responsibilities:
  - Initialize a permanent memory complement (DRAM init / memory reference code).
  - Describe memory and firmware-volume locations in **HOBs** (Hand-Off Blocks).
  - Hand control to DXE via the DXE IPL PPI.
- Keep it the *thinnest possible* code: it must fit a small fault-tolerant block for **crisis recovery** and must be fast for **S3 resume** (minimize the resume code path).
- More processor-architecture-dependent than any other phase.

### Key PEI constructs

- **PPI** (PEIM-to-PEIM Interface): the only call mechanism between PEIMs.
- **HOB list**: position-independent data structures describing system state handed to DXE (memory map, FVs, CPU info, platform data).
- **S3 / recovery**: special boot paths originating in PEI; S3 restores via boot script, recovery reflashes from a trusted store.

## DXE — Driver eXecution Environment

Where the bulk of initialization happens. Components:

- **DXE Foundation/Core**: consumes the HOB list, produces **Boot Services**, **Runtime Services**, and **DXE Services**, and the system table.
- **DXE Dispatcher**: discovers and runs DXE drivers in dependency order, evaluating each driver's **depex** (protocol GUIDs that must be present first).
- **DXE Drivers**: init CPU/chipset/platform, and provide software abstractions (consoles, block/disk, PCI, USB, network) via **protocols** installed on **handles**.
- Architectural Protocols (e.g., `gEfiCpuArchProtocolGuid`, Runtime, Variable, WatchdogTimer, Security) must be produced to complete the DXE environment.
- DXE Core code is boot-services memory — none of it persists into the OS; only runtime data and runtime-DXE-driver services survive.

### Key DXE constructs

- **Protocol**: interface (GUID + structure of function pointers/data) installed on a handle; the core IPC mechanism of UEFI.
- **Depex**: dependency expression controlling dispatch order (`DEPEX` section in the INF / generated `.depex`).
- **Events & TPLs**: notification + task-priority-level synchronization model.
- **GCD** (Global Coherency Domain): DXE Services managing system memory and I/O resource maps.

## BDS — Boot Device Selection

- Entered after the DXE Dispatcher has run all satisfiable drivers; implemented as the **BDS Architectural Protocol**.
- Implements the platform **boot policy** (UEFI Boot Manager chapter): initialize consoles, connect/load device drivers, enumerate and attempt **boot options** (`Boot####`, `BootOrder`).
- Supports short-form device paths starting with a firmware-volume node (matched by FV name GUID).
- If it cannot make forward progress, it re-invokes the DXE Dispatcher to pick up newly satisfiable drivers.

## TSL — Transient System Load

- First stage of OS boot: the OS loader runs as an EFI application using Boot Services.

## RT — Runtime

- The limited **Runtime Services** available after the OS takes over: variable get/set, real-time clock, monotonic counter, `ResetSystem`, capsule update (`UpdateCapsule`).
- The OS may call `SetVirtualAddressMap` once (one-way gate); runtime code fixes itself up for virtual addressing. Isolate such code in **runtime-only drivers** and runtime memory.

## AF — After Life

- Minimal firmware left behind after the OS owns the machine. Possible crash/recovery remediation. No PI/UEFI-mandated behavior.

## Phase decision checklist (use during review)

- Is the work in the **earliest phase that has the needed resources**, and no earlier? (Defer complexity from PEI to DXE.)
- Are inter-module calls using the **right mechanism** (PPI in PEI, protocol in DXE)?
- Is **depex** correct so the driver dispatches after its dependencies?
- Does anything called at **runtime** avoid Boot Services and live in runtime memory?
- Are **S3 resume** and **recovery** paths preserved and fast?
- Is data handed across phases via **HOBs** (PEI->DXE) rather than ad-hoc globals?

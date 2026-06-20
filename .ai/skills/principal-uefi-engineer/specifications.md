# Specifications & Learning Resources (Reference)

Always cite the **exact spec and section** (or wiki page) behind a recommendation. Verify against the latest published revision; these are the current authoritative versions.

## Core specifications (uefi.org)

- **Specs & test tools hub**: <https://uefi.org/specsandtesttools>
- **UEFI 2.11** (interfaces: protocols, boot/runtime services, device paths, secure boot, HII): <https://uefi.org/specs/UEFI/2.11/>
- **PI 1.9** (SEC/PEI/DXE/SMM/MM, HOBs, PPIs, firmware volumes, dispatch): <https://uefi.org/specs/PI/1.9/>
- **ACPI 6.6** (power mgmt, tables, AML, device descriptions): <https://uefi.org/specs/ACPI/6.6/>
- **UEFI Shell 2.2** (shell commands, scripting, protocols): <https://uefi.org/sites/default/files/resources/UEFI_Shell_2_2.pdf>

### How to use them

- Building a **protocol/service** or boot/secure-boot behavior -> UEFI 2.11.
- Working in **SEC/PEI/DXE/SMM/MM**, HOBs, depex, FV/flash -> PI 1.9.
- **Power, tables, _SB/_PR, GPE, wake** -> ACPI 6.6 (cross-check SMBIOS at DMTF).
- **Shell command/script** semantics or writing shell tests -> Shell 2.2.

## TianoCore source & knowledge

- **edk2** (core): <https://github.com/tianocore/edk2> — latest stable tag e.g. `edk2-stableYYYYMM`.
- **edk2-platforms** (boards/silicon, MinPlatform): <https://github.com/tianocore/edk2-platforms>
- **edk2-non-osi** (binary blobs): part of the TianoCore org.
- **Org & tools** (pytool-extensions/library, edk2-test/SCT, edkrepo, libc, redfish-client): <https://github.com/tianocore>
- **Wiki** (boot flow, build, debugging, package guides, code style, security): <https://github.com/tianocore/tianocore.github.io/wiki>
  - PI Boot Flow: <https://github.com/tianocore/tianocore.github.io/wiki/PI-Boot-Flow>

## Design papers, presentations & training

- **Learning Center — Papers**: <https://uefi.org/learning_center/papers>
- **Learning Center — Presentations & Videos**: <https://uefi.org/learning_center/presentationsandvideos>

Use these for newer designs/best practices (e.g., Standalone MM, DynamicTables, secure-boot evolution, capsule update, RISC-V/ARM enablement) that may post-date a spec revision.

## DMTF (advanced manageability & security)

- **DMTF home**: <https://www.dmtf.org/>
- Relevant standards: **SMBIOS** (system inventory tables), **Redfish** (manageability REST; see `RedfishPkg`), **SPDM** (device attestation/secure session; `libspdm` in `SecurityPkg`), **PLDM**/**MCTP** (platform-level messaging/transport, e.g., `ManageabilityPkg`).

Use DMTF specs for out-of-band management, attestation, and firmware-to-BMC communication design.

## Citation discipline

- Quote the spec **version + section number** (e.g., "UEFI 2.11 §7.2 Memory Allocation Services", "PI 1.9 Vol 1 §6 PEI Services").
- For code patterns, cite the **package + module** (e.g., `MdeModulePkg/Core/Dxe`, `SecurityPkg/Library/...`).
- Prefer primary specs over blog/wiki when they disagree; note when guidance comes from a learning-center paper vs a normative spec.

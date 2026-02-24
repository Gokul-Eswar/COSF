# Implementation Plan: Expanded Adapter Ecosystem

## Phase 1: Web Security Adapters (ZAP & Burp)
- [x] Implement `ZapAdapter` in `cosf/engine/adapters/zap.py` with container support.
- [ ] Implement `BurpAdapter` with support for Burp Suite's REST API.
- [x] Ensure DAST results are mapped to `Vulnerability` and `Asset` objects in SOM.

## Phase 2: Offensive Security Adapters (Metasploit)
- [ ] Implement `MetasploitAdapter` using the `pymetasploit3` library or direct RPC calls.
- [ ] Focus on "Exploit Validation" (confirming a vulnerability exists by attempting a non-destructive exploit).

## Phase 3: Generic & Extensible Adapters
- [x] Implement `PythonAdapter` to run custom user-provided Python scripts.
- [ ] Implement `ShellAdapter` (optional, for running local binary commands with caution).

## Phase 4: Verification & Documentation
- [x] Create unit tests for each new adapter (`tests/test_zap_adapter.py`, etc.).
- [ ] Update the `cosf/engine/adapters/README.md` with detailed parameter documentation for all supported tools.

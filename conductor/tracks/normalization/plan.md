# Implementation Plan: Centralized Normalization Pipeline

## Phase 1: Normalization Engine Foundations
- [x] Implement `cosf/engine/normalization.py` with `BaseNormalizer` and `NormalizationEngine`.
- [x] Implement `SeverityMapper` utility to unify "Critical/High/Med/Low" across tools.
- [x] Implement basic validation logic to ensure normalized objects match SOM schemas. (Inherent in Pydantic SOM models)
- [x] **Verification:** Unit test for the base engine with a mock normalizer.

## Phase 2: Refactoring Discovery Normalizers
- [x] Implement `NmapNormalizer` in `cosf/engine/normalization.py` (moved from `nmap.py`).
- [x] Refactor `cosf/engine/adapters/nmap.py` to use the central engine.
- [x] Implement `NucleiNormalizer` in `cosf/engine/normalization.py` (moved from `nuclei.py`).
- [x] Refactor `cosf/engine/adapters/nuclei.py` to use the central engine.
- [x] **Verification:** Re-run `verify_adapters.py` and ensure SOM entities are still created correctly.

## Phase 3: Advanced Metadata Mapping
- [x] Enhance normalizers to capture more tool-specific metadata into the `metadata` JSON field of SOM objects. (Initial implementation done)
- [ ] Implement a `FingerprintRule` that standardizes OS and service version strings.
- [x] **Verification:** Verify that `Asset` objects have rich, standardized tags after an Nmap/Nuclei run.

## Phase 4: Integration & Global Config
- [ ] Update `BaseAdapter` to automatically invoke the `NormalizationEngine` if a normalizer is registered for the adapter name.
- [ ] Add a "Normalization Quality" report to the dashboard summary.
- [ ] **Verification:** Trigger a workflow via the Web UI and verify high-quality standardized data in the graph.

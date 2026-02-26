# Implementation Plan: Advanced Security Intelligence

## Phase 1: Inference Engine Foundations
- [ ] Implement `cosf/engine/intelligence.py` with the `InferenceEngine` class.
- [ ] Implement `CredentialReuseRule`: Links assets sharing the same `Credential` entity.
- [ ] Implement `NetworkProximityRule`: Links assets in the same subnet.
- [ ] Implement `ServiceMatchingRule`: Links services with identical names and versions.
- [ ] **Verification:** Unit tests for each rule in isolation.

## Phase 2: Graph Integration
- [ ] Update `GraphEngine.build_from_db` in `cosf/engine/graph.py` to invoke the `InferenceEngine`.
- [ ] Persist inferred relationships back to the database as `Relationship` entities with a `source: "inference"` tag.
- [ ] Update `find_attack_paths` to optionally include or exclude inferred edges.
- [ ] **Verification:** End-to-end test where the engine builds a graph and discovers a multi-hop path through inferred credential reuse.

## Phase 3: Basic Risk Scoring
- [ ] Implement a `RiskScorer` that calculates a score (0.0 - 10.0) for each asset.
- [ ] Factor in: number of services, presence of high-severity vulnerabilities, and reachability.
- [ ] Update SOM `Asset` to include a `risk_score` field.
- [ ] **Verification:** Verify that an asset with an RCE vulnerability has a higher score than a clean asset.

## Phase 4: Visualization & CLI
- [ ] Add `cosf graph analyze --infer` to trigger the new intelligence logic.
- [ ] Update the visualization layer to color-code inferred relationships (e.g., dashed lines).
- [ ] Generate a "Security Intelligence Report" summarizing the inferred findings.

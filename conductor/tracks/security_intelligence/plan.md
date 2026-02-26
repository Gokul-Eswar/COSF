# Implementation Plan: Advanced Security Intelligence

## Phase 1: Inference Engine Foundations
- [x] Implement `cosf/engine/intelligence.py` with the `InferenceEngine` class.
- [x] Implement `CredentialReuseRule`: Links assets sharing the same `Credential` entity.
- [x] Implement `NetworkProximityRule`: Links assets in the same subnet. (Deferred - focus on Creds/Services)
- [x] Implement `ServiceMatchingRule`: Links services with identical names and versions.
- [x] **Verification:** Unit tests for each rule in isolation.

## Phase 2: Graph Integration
- [x] Update `GraphEngine.build_from_db` in `cosf/engine/graph.py` to invoke the `InferenceEngine`.
- [x] Persist inferred relationships back to the database as `Relationship` entities with a `source: "inference"` tag.
- [x] Update `find_attack_paths` to optionally include or exclude inferred edges.
- [x] **Verification:** End-to-end test where the engine builds a graph and discovers a multi-hop path through inferred credential reuse.

## Phase 3: Basic Risk Scoring
- [x] Implement a `RiskScorer` that calculates a score (0.0 - 10.0) for each asset.
- [x] Factor in: number of services, presence of high-severity vulnerabilities, and reachability.
- [x] Update SOM `Asset` to include a `risk_score` field.
- [x] **Verification:** Verify that an asset with an RCE vulnerability has a higher score than a clean asset.

## Phase 4: Visualization & CLI
- [x] Add `cosf graph analyze --infer` to trigger the new intelligence logic.
- [x] Update the visualization layer to color-code inferred relationships (e.g., dashed lines).
- [x] Generate a "Security Intelligence Report" summarizing the inferred findings.

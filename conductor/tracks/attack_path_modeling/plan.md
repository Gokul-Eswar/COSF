# Implementation Plan: Attack Path Modeling & Graph Visualization

## Phase 1: Security Object Model (SOM) Expansion
- [ ] Implement `Credential`, `AttackStep`, and `Relationship` models in `cosf/models/som.py`.
- [ ] Update the database schema (`cosf/models/database.py`) to support these new entities.
- [ ] Run migrations to update the PostgreSQL schema.

## Phase 2: Graph Engine Implementation
- [ ] Implement a `GraphEngine` in `cosf/engine/graph.py`.
- [ ] Add support for syncing SOM objects from the relational database to a Neo4j instance.
- [ ] Implement algorithms for "Exploitability Path" discovery (find a chain from an internet-facing asset to a core DB).

## Phase 3: CLI & Reporting
- [ ] Add a `cosf graph analyze` command to run the analysis engine.
- [ ] Add a `cosf graph visualize` command that starts a local server to view the graph.
- [ ] Integrate a static graph view into the existing HTML reports using D3.js or Sigma.js.

## Phase 4: Verification & Tests
- [ ] Create `tests/test_graph_analysis.py`.
- [ ] Mock a multi-hop vulnerability chain (Asset A -> Vuln 1 -> Cred 1 -> Asset B) and verify the engine detects the path.
- [ ] Test the visualization output for consistency.

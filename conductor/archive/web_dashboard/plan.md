# Implementation Plan: Web Dashboard

## Phase 1: Dashboard Scaffolding & Static Assets
- [x] Create `cosf/api/static/` and `cosf/api/templates/` directories.
- [x] Implement a basic `index.html` using **Vanilla JS and Tailwind CSS (via CDN)** for simplicity and "zero-install" self-hosting.
- [x] Scafffold the main layout: Sidebar, Navbar, and Content Area.
- [x] **Verification:** Start `cosf serve` and verify `http://localhost:8000/dashboard` (or root) loads the empty shell.

## Phase 2: Execution & Risk Components
- [x] Implement `fetchExecutions()`: Populate a table with historical runs from `/executions`.
- [x] Implement `fetchHighRiskAssets()`: Display cards for assets with risk scores > 7.0 from `/assets`.
- [x] Implement a "Trigger Workflow" button that opens a modal to paste YAML.
- [x] **Verification:** Verify the table and cards populate correctly with data from previous runs.

## Phase 3: Interactive Graph Visualization
- [x] Integrate **D3.js** for graph rendering.
- [x] Map `/graph` API response to D3 nodes and links.
- [x] Implement color-coding for nodes (Asset = Blue, Service = Green, Vuln = Red).
- [x] Implement "Inferred Relationship" styling (dashed lines for logic-based edges).
- [x] **Verification:** Verify the graph correctly displays Asset-Service-Vulnerability chains.

## Phase 4: Full Integration & Polish
- [x] Add "Live Updates" (basic polling or WebSockets) to show workflow progress.
- [x] Finalize responsive design for various screen sizes.
- [x] Add "Download Report" links directly in the UI. (Partial - dashboard integration ready)
- [x] **Verification:** Perform an end-to-end operation: Trigger a scan from the UI, monitor it, and view the updated graph.

# Track Specification: Unified Web Dashboard & Visualization

## Overview
This track introduces a centralized web-based command center for COSF. It provides a "Single Pane of Glass" to visualize workflow executions, attack paths, and risk scores, transforming COSF into a mature security management platform.

## Objectives
1.  **Attack Path Visualization:** Implement an interactive graph view using D3.js or Sigma.js to show relationships between assets, services, and vulnerabilities.
2.  **Execution Monitoring:** Provide a real-time (or near real-time) dashboard to track active and historical workflow runs.
3.  **Risk Management View:** Display high-risk assets and inferred intelligence findings in a user-friendly table and card layout.
4.  **Operational Insights:** Summary statistics on total vulnerabilities, top attack vectors, and infrastructure coverage.

## Scope

### In-Scope
-   **Frontend Scaffolding:** A lightweight React or Vanilla JS application.
-   **Graph Integration:** Interactive nodes and edges representing the SOM graph.
-   **API Integration:** Connecting the dashboard to the FastAPI Control Plane.
-   **Dashboard Components:** Cards for risk scores, tables for execution history, and a detail view for specific assets.

### Out-of-Scope
-   Interactive workflow builder (editing YAML in the browser - focus on visualization first).
-   User authentication/login (relying on the Control Plane's basic security for now).

## Success Criteria
-   A user can open a browser and see a visual map of their scanned environment.
-   Clicking a node in the graph displays detailed information (IP, services, vulnerabilities).
-   The dashboard correctly identifies and highlights the highest-risk assets.

# Track Specification: Advanced Security Intelligence & Autonomous Inference

## Overview
This track enhances the COSF `GraphEngine` to autonomously infer relationships between security entities based on logical security patterns (e.g., credential reuse, lateral movement, exploit chains). It transforms raw SOM data into a high-fidelity "Security Context Graph".

## Objectives
1.  **Autonomous Relationship Inference:** Automatically discover connections between assets, services, and vulnerabilities without explicit workflow steps.
2.  **Exploit Chain Modeling:** Link vulnerabilities to potential lateral movement or privilege escalation steps.
3.  **Credential Correlation:** Automatically map credentials across multiple assets to identify "Golden Path" scenarios.
4.  **Security Risk Scoring:** Calculate dynamic risk scores for assets based on their position in the attack graph.

## Scope

### In-Scope
-   **Inference Rules Engine:** A module that applies predefined security logic to SOM entities (e.g., `same_ip`, `matching_creds`).
-   **Enhanced GraphEngine:** Support for the new inference rules during graph building.
-   **Risk Scoring Model:** A basic algorithm to weigh assets based on their criticality and proximity to vulnerabilities.
-   **Visualization Improvements:** Differentiating between "Implicit" and "Inferred" relationships in graph views.

### Out-of-Scope
-   AI/ML-based inference (focus on rule-based logic first).
-   Real-time monitoring of live traffic to update the graph (focus on static analysis of collected SOM data).

## Success Criteria
-   If an Nmap scan finds Asset A and Asset B both running the same version of an SSH service, COSF should suggest a `SAME_SERVICE` relationship.
-   If a credential discovered on Asset A is also valid for Asset B, the graph must show a `CREDENTIAL_REUSE` edge.
-   The `find_attack_paths` method correctly identifies paths that traverse inferred relationships.

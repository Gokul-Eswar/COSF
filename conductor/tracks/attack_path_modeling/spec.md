# Specification: Attack Path Modeling & Graph Visualization

## Objective
Enable COSF to model and visualize relationships between security objects (Assets, Services, Vulnerabilities, Credentials) as a graph, helping security engineers identify potential "Attack Paths."

## Requirements
1.  **Expanded SOM**: Add new security entities to `cosf/models/som.py`:
    - `Credential`: Represents discovered usernames, passwords, or hashes.
    - `AttackStep`: Represents a specific step in an attack (e.g., exploitation, lateral movement).
    - `Relationship`: Explicitly define connections (e.g., `Service -> Vulnerability`, `Asset -> Asset via lateral movement`).
2.  **Graph Database Integration**: Support for **Neo4j** or a similar graph storage for querying relationships.
3.  **Graph Analysis Utility**: A library to compute shortest paths from "Initial Access" to "Critical Asset."
4.  **Interactive Visualization**: An interactive graph dashboard (HTML/D3.js) to explore the assessment results visually.

## Key Design Considerations
-   The current relational model in PostgreSQL is good for structured history, but not for traversing deep relationship chains. A graph-based view will complement it.
-   The "Attack Graph" should be generated dynamically after the workflow completes based on the objects persisted in the SOM.

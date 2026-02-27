# Track Specification: Centralized Normalization Pipeline (OCSF Layer)

## Overview
This track introduces a unified data normalization engine that transforms heterogeneous security tool outputs into standardized Security Object Model (SOM) entities. It moves parsing logic away from individual adapters into a central, versioned pipeline inspired by the Open Cybersecurity Schema Framework (OCSF).

## Objectives
1.  **Decouple Parsing from Execution:** Extract tool-specific parsing logic from adapters into reusable "Normalizers".
2.  **Standardize Tool Mappings:** Ensure consistent mapping of severity, asset types, and vulnerability metadata across all supported tools.
3.  **Future-Proofing:** Make it easy to add new tools by providing a common interface for data transformation.
4.  **Data Quality Enforcement:** Validate that all normalized data meets the strict requirements of the SOM before it hits the database or attack graph.

## Scope

### In-Scope
-   **Central Normalization Engine:** A core module to register and invoke tool-specific normalizers.
-   **Nmap Normalizer:** Refactored parsing logic for Nmap XML output.
-   **Nuclei Normalizer:** Refactored parsing logic for Nuclei JSON output.
-   **Severity Normalization:** A central mapping for high/medium/low severity levels across tools.
-   **Validation Layer:** Post-normalization checks to ensure SOM integrity.

### Out-of-Scope
-   Full OCSF implementation (using it as a reference for field naming and structure, but staying compatible with current SOM).
-   Real-time data stream normalization (focus on batch output from adapters).

## Success Criteria
-   Adapters (`nmap.py`, `nuclei.py`) contain < 50 lines of code focused purely on execution.
-   Adding a new tool only requires implementing a single `normalize()` function in the pipeline.
-   All vulnerabilities in the database use a consistent severity scale (e.g., Critical, High, Medium, Low, Info).

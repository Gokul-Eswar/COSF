# Track Specification: Advanced SOM & Evidence Management

## Overview
This track focuses on evolving the Security Object Model (SOM) from a simple data container into a legally defensible and comprehensive evidence chain. This is critical for forensic integrity and complex attack modeling.

## Core Objectives
1.  **Binary Evidence Support:** Enable the framework to capture and store raw tool artifacts (PCAPs, screenshots, binary logs) rather than just text summaries.
2.  **Chain of Custody (Signing):** Implement cryptographic signing for all execution results to ensure data has not been tampered with after collection.
3.  **Semantic Relationship Expansion:** Add specialized relationship types to support advanced attack graph analysis (e.g., lateral movement, credential reuse).

## Technical Requirements
-   **Storage:** Local filesystem storage for binary blobs with a database index.
-   **Cryptography:** Use `cryptography` or `PyNaCl` for Ed25519 signatures.
-   **Database:** Update schema to include `Evidence` entities and expanded `Relationship` metadata.

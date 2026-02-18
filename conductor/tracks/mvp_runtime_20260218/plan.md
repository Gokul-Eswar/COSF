# Track: MVP: Core Runtime & Initial Adapters Implementation Plan

## Phase 1: Core Engine & SOM Foundation
- [ ] **Task: Define Core Security Object Model (SOM)**
    - [ ] Write failing tests for Asset, Service, and Vulnerability Pydantic models
    - [ ] Implement SOM entities using Pydantic
- [ ] **Task: Build Asynchronous Workflow Parser**
    - [ ] Write failing tests for YAML workflow schema validation
    - [ ] Implement the workflow parser using Pydantic and PyYAML
- [ ] **Task: Implement Base Execution Engine**
    - [ ] Write failing tests for task orchestration and state management
    - [ ] Build the core `asyncio` execution loop for task sequencing
- [ ] **Task: Conductor - User Manual Verification 'Phase 1: Core Engine & SOM Foundation' (Protocol in workflow.md)**

## Phase 2: Adapter Architecture & Tool Integration
- [ ] **Task: Define Pluggable Adapter Interface**
    - [ ] Write failing tests for the base adapter abstract class
    - [ ] Implement the tool adapter interface and registration system
- [ ] **Task: Implement Nmap Adapter**
    - [ ] Write failing tests for Nmap output parsing to SOM
    - [ ] Implement the Nmap adapter with Docker-based execution
- [ ] **Task: Implement Nuclei Adapter**
    - [ ] Write failing tests for Nuclei output parsing to SOM
    - [ ] Implement the Nuclei adapter with Docker-based execution
- [ ] **Task: Conductor - User Manual Verification 'Phase 2: Adapter Architecture & Tool Integration' (Protocol in workflow.md)**

## Phase 3: CLI & Initial Workflow Execution
- [ ] **Task: Build Basic CLI**
    - [ ] Write failing tests for the `cosf run` command
    - [ ] Implement the CLI using Typer
- [ ] **Task: End-to-End Workflow Execution**
    - [ ] Create an E2E test for a combined Nmap + Nuclei workflow
    - [ ] Verify execution, normalization, and result aggregation
- [ ] **Task: Conductor - User Manual Verification 'Phase 3: CLI & Initial Workflow Execution' (Protocol in workflow.md)**

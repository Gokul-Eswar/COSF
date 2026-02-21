# Track: MVP: Core Runtime & Initial Adapters Implementation Plan

## Phase 1: Core Engine & SOM Foundation [checkpoint: a5b3c0d]
- [x] **Task: Define Core Security Object Model (SOM)** fccd7d4
    - [ ] Write failing tests for Asset, Service, and Vulnerability Pydantic models
    - [ ] Implement SOM entities using Pydantic
- [x] **Task: Build Asynchronous Workflow Parser** 5befec9
    - [ ] Write failing tests for YAML workflow schema validation
    - [ ] Implement the workflow parser using Pydantic and PyYAML
- [x] **Task: Implement Base Execution Engine** f64f18d
    - [ ] Write failing tests for task orchestration and state management
    - [ ] Build the core `asyncio` execution loop for task sequencing
- [x] **Task: Conductor - User Manual Verification 'Phase 1: Core Engine & SOM Foundation' (Protocol in workflow.md)** a5b3c0d

## Phase 2: Adapter Architecture & Tool Integration [checkpoint: 10aef18]
- [x] **Task: Define Pluggable Adapter Interface** 5378b76
    - [ ] Write failing tests for the base adapter abstract class
    - [ ] Implement the tool adapter interface and registration system
- [x] **Task: Implement Nmap Adapter** 5d1ca70
    - [ ] Write failing tests for Nmap output parsing to SOM
    - [ ] Implement the Nmap adapter with Docker-based execution
- [x] **Task: Implement Nuclei Adapter** afb22a4
    - [ ] Write failing tests for Nuclei output parsing to SOM
    - [ ] Implement the Nuclei adapter with Docker-based execution
- [x] **Task: Conductor - User Manual Verification 'Phase 2: Adapter Architecture & Tool Integration' (Protocol in workflow.md)** 10aef18

## Phase 3: CLI & Initial Workflow Execution
- [x] **Task: Build Basic CLI** e9769e0
    - [ ] Write failing tests for the `cosf run` command
    - [ ] Implement the CLI using Typer
- [x] **Task: End-to-End Workflow Execution** fda7ec0
    - [ ] Create an E2E test for a combined Nmap + Nuclei workflow
    - [ ] Verify execution, normalization, and result aggregation
- [ ] **Task: Conductor - User Manual Verification 'Phase 3: CLI & Initial Workflow Execution' (Protocol in workflow.md)**

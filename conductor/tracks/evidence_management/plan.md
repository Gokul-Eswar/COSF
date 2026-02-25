# Implementation Plan: Advanced SOM & Evidence Management

## Phase 1: Binary Evidence Store
- [x] Create `Evidence` model in `cosf/models/som.py`.
- [x] Create `DBEvidence` table in `cosf/models/database.py` with path/hash fields.
- [x] Implement `EvidenceManager` in `cosf/models/evidence.py` to handle file I/O and deduplication.
- [x] Update `ExecutionEngine` to support attaching raw files to tasks.

## Phase 2: Cryptographic Integrity
- [x] Implement `cosf/utils/crypto.py` for key generation and message signing.
- [x] Add `signature` and `public_key` fields to `WorkflowExecution` and `TaskExecution` models.
- [x] Implement a CLI command `cosf verify <execution_id>` to validate signatures.

## Phase 3: Relationship & Graph Expansion
- [x] Add new relationship types: `LATERAL_MOVEMENT`, `CREDENTIAL_REUSE`, `PRIVILEGE_ESCALATION`.
- [ ] Update `GraphEngine` to handle these specific types with specialized weights/attributes.

## Phase 4: Verification & Tests
- [x] Create `tests/test_evidence_management.py`.
- [x] Verify that binary files are correctly hashed and stored.
- [x] Test the verification command with both valid and tampered data.

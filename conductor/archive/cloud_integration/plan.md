# Implementation Plan: Cloud Integration

## Phase 1: Cloud-Native Storage (Evidence Management)
- [x] Create `cosf/utils/storage.py` to abstract storage backends (Local vs. S3).
- [x] Refactor `EvidenceManager` in `cosf/models/evidence.py` to use the new storage abstraction.
- [x] Implement `S3StorageProvider` using `boto3`.
- [x] Add configuration support for S3 (endpoint, bucket, credentials).
- [x] **Verification:** Unit tests for S3 storage (using `moto` or a local MinIO container).

## Phase 2: Cloud Adapter Foundations
- [x] Implement `AwsAdapter` in `cosf/engine/adapters/aws.py`.
- [x] Support `s3_list_buckets` and `s3_get_policy` as initial tasks.
- [x] Map AWS resources to `Asset` or a new `CloudResource` SOM object.
- [x] **Verification:** A sample workflow `cloud_recon.yaml` that lists buckets.

## Phase 3: Cloud Credential Management
- [x] Enhance `ExecutionEngine` to securely pass cloud credentials to adapters.
- [x] Support AWS Profile and Environment variable based authentication.
- [x] **Verification:** Test authentication with invalid credentials to ensure graceful failure.

## Phase 4: Integration & Documentation
- [x] Update `cosf/engine/adapters/README.md` with Cloud adapter details.
- [x] Add a "Cloud" section to `details.md` or `product.md`.
- [x] Update `pyproject.toml` with new dependencies (`boto3`, `moto`).

# Implementation Plan: Template Marketplace

## Phase 1: Foundation & Registry (Backend)
- [ ] **Define Schema:** Create a Pydantic model for Marketplace Templates.
- [ ] **Local Registry Setup:** Create a `cosf/marketplace/` directory to store static JSON/YAML template metadata.
- [ ] **Sample Templates:** Add 3-5 initial playbooks (e.g., "Basic Recon," "AWS Asset Inventory," "Shodan Audit").
- [ ] **API Endpoints:**
    - [ ] `GET /api/marketplace/templates` (List)
    - [ ] `GET /api/marketplace/templates/{id}` (Details)
    - [ ] `POST /api/marketplace/install/{id}` (Logic for importing playbooks to `DBWorkflowDraft`)

## Phase 2: Frontend Implementation
- [ ] **New View Component:** Create `MarketplaceView.tsx` and register the route in `App.tsx`.
- [ ] **Template Grid:** Implement cards displaying name, category, and "Verified" status.
- [ ] **Preview Modal:** Use a code viewer (e.g., `react-syntax-highlighter`) to show the WDL.
- [ ] **Install Logic:** Wire up the backend `install` call and redirect to the Visual Builder.

## Phase 3: Adapter Support (Advanced)
- [ ] **Adapter Metadata Schema:** Extend the marketplace to support tool adapter definitions.
- [ ] **Installation Logic:** Implement (mocked for now) the ability to "install" an adapter by downloading its source to the adapter directory.

## Phase 4: Verification & Polishing
- [ ] **Verified Badges:** Add logic/metadata to mark community-verified content.
- [ ] **Testing:** Unit tests for marketplace API endpoints and integration tests for "installation" flow.
- [ ] **UX Refinement:** Ensure the marketplace design is consistent with the rest of the dashboard.

## Verification Tasks
- [ ] **Automated Tests:**
    - [ ] `pytest tests/test_marketplace_api.py`
    - [ ] Verify playbook installation creates a database record.
- [ ] **Manual Validation:**
    - [ ] Confirm marketplace page is accessible in the browser.
    - [ ] Successfully "Install" a template and verify it appears in the Drafts list.

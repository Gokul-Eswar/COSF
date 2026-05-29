# Track Specification: Template Marketplace

## Goal
Develop an integrated "Store" within the COSF dashboard for users to discover, preview, and install community-verified playbooks (WDL) and adapters. This enhances the "Security-as-Code" vision by promoting sharing and reuse.

## Core Features
1.  **Template Discovery:** A searchable and filterable list of playbooks and adapters.
2.  **Preview Mode:** View the contents of a WDL file or adapter metadata before installing.
3.  **One-Click Installation:**
    *   **Playbooks:** Imported as a new "Draft" in the Visual Workflow Builder.
    *   **Adapters:** Registered and made available for use in workflows.
4.  **Community-Verified Badge:** Visual indication of templates that have been audited for safety.

## Technical Architecture
### 1. Template Registry
A structured directory of metadata files (JSON/YAML).
- **Playbook Template:**
    - ID, Name, Description, Category, Tags
    - Content (The raw WDL YAML)
- **Adapter Template:**
    - ID, Name, Description, Category, Tags
    - Python source code or Docker image reference

### 2. Backend API (`/api/marketplace`)
- `GET /api/marketplace/templates`: List all templates with optional filtering.
- `GET /api/marketplace/templates/{id}`: Get full details and content.
- `POST /api/marketplace/install/{id}`: 
    - For playbooks: Create a new `DBWorkflowDraft`.
    - For adapters: (Future) Dynamically register or download the adapter.

### 3. Frontend Component
- **Marketplace View:** Grid layout with template cards.
- **Search Bar:** Filter by name, category, or tags.
- **Template Details Modal:**
    - Full description.
    - Code preview (using a syntax-highlighted editor component).
    - "Install" button.

## Security Considerations
- **Sandboxing:** Installed playbooks/adapters should be treated as untrusted until verified.
- **Content Verification:** Use checksums or digital signatures for "Verified" templates.
- **Access Control:** Restrict installation to users with "admin" or "operator" roles.

## Success Criteria
- Users can browse a catalog of at least 5 sample templates.
- A user can select a playbook template and have it appear as a draft in their builder.
- The UI is intuitive and follows the established minimalist, technical brand.

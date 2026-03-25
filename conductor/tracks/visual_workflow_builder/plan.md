# Track: Visual Workflow Builder (Frontend)

## 1. Objective
Develop a low-code, drag-and-drop web interface for visually composing WDL (Workflow Definition Language) files. This allows users to build and edit security workflows (playbooks) without writing YAML directly.

## 2. Technical Stack
- **Framework:** React with TypeScript.
- **Styling:** Vanilla CSS (TailwindCSS will not be used, per defaults).
- **Visual Node Graph:** Custom Vanilla CSS / SVG or a lightweight wrapper like React Flow for node-based drag-and-drop interfaces.
- **Build Tool:** Vite.
- **Backend Integration:** Connects to the existing FastAPI backend (`/api/drafts`, `/api/adapters`).

## 3. Architecture & Components

### 3.1. Directory Structure
The frontend application will reside in a new top-level directory: `/frontend`.

### 3.2. Core Components
- **`Sidebar`**: Fetches and displays a list of available adapters from `/api/adapters`. Users can drag these onto the canvas to create tasks.
- **`Canvas / Builder`**: The central visual workspace. Displays tasks as nodes and dependencies as connecting edges.
- **`PropertiesPanel`**: When a node is selected on the canvas, this panel displays a form to configure the task (Name, Parameters, Dependencies, Retry logic, When conditions).
- **`Toolbar`**: Actions to Save Draft (`POST /api/drafts`), Load Draft (`GET /api/drafts`), and Export WDL (`POST /api/drafts/{id}/export`).

### 3.3. API Integration
The frontend will communicate with the existing Control Plane API:
- `GET /api/adapters` - Populate the Sidebar palette.
- `GET /api/drafts` - List saved workflows.
- `POST /api/drafts` - Create a new workflow draft.
- `PUT /api/drafts/{draft_id}` - Update a draft.
- `POST /api/drafts/{draft_id}/export` - Convert the visual representation to standard WDL YAML.

### 3.4. Aesthetics & Design
- **Theme**: Dark mode by default, matching cybersecurity aesthetics (dark grays, neon accents).
- **Feedback**: Interactive hover states, active states for selected nodes, and clear visual indicators for invalid configurations.
- **Vanilla CSS**: Procedural patterns and gradients for backgrounds to provide a "living" modern feel.

## 4. Backend Adjustments (if any)
- **CORS Configuration**: Ensure `cosf/api/main.py` has CORS middleware configured to allow the Vite dev server (e.g., `http://localhost:5173`) to communicate with the FastAPI backend during development.

## 5. Implementation Steps
1. **Initialize Project:** Run `npm create vite@latest frontend -- --template react-ts` and clear out boilerplate.
2. **CORS Setup:** Add `CORSMiddleware` to `cosf/api/main.py`.
3. **Core Layout:** Build the HTML/CSS structure for Sidebar, Canvas, and PropertiesPanel.
4. **Drag & Drop Logic:** Implement state management for nodes (tasks) and edges (dependencies).
5. **API Wiring:** Connect the components to the FastAPI endpoints using `fetch`.
6. **Validation & Polish:** Add styling, animations, and verify complete E2E flow from visual building to WDL export.

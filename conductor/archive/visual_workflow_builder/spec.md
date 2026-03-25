# Specification: Visual Workflow Builder (Frontend)

## 1. Overview
The Visual Workflow Builder provides a drag-and-drop interface for composing Cyber Operations workflows (WDL). It allows security operators to build complex multi-tool playbooks without deep knowledge of YAML syntax.

## 2. Features
- **Adapter Toolbox:** Fetches available tool adapters from the backend and displays them as draggable items.
- **Node-Based Canvas:** Uses React Flow to manage task nodes and their dependency edges.
- **Task Configuration:** Contextual properties panel for editing task names, adapter parameters (JSON), and retry logic.
- **Workflow Management:**
  - Name and save drafts to the central database.
  - Export visual layouts to standardized WDL YAML.
  - One-click "Run" button to execute the workflow via the Execution Engine.

## 3. Technical Design
- **Frontend Framework:** React 19 + TypeScript + Vite.
- **State Management:** `reactflow` hooks (`useNodesState`, `useEdgesState`) for canvas state.
- **Backend API:** FastAPI with CORS enabled for the frontend origin.
- **Styling:** Vanilla CSS with a modern dark theme ("Cyber" aesthetic).

## 4. Components
- `App.tsx`: Main entry point and layout container.
- `Sidebar`: Palette for tool adapters.
- `Canvas`: Interactive node graph.
- `PropertiesPanel`: Detail editor for the selected node.
- `Header`: Global actions and workflow metadata.

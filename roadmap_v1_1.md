# COSF Roadmap: v1.1 & Beyond

With the core framework stabilized at v1.0, the next phase focuses on usability, autonomous action, and ecosystem depth.

---

## 1. Advanced Workflow UX
- [x] **Visual Workflow Builder (Backend):** CRUD endpoints for drafts, adapter metadata, and WDL export logic.
- [x] **Visual Workflow Builder (Frontend):** A low-code, drag-and-drop web interface for composing WDL files.
- [ ] **Template Marketplace:** An integrated "Store" in the dashboard to discover and install community-verified playbooks and adapters.

## 2. Intelligence & Autonomous Action
- [x] **Auto-Remediation Agents:** RemediationAdapter and InferenceEngine logic to suggest and execute fixes.
- [ ] **Predictive Attack Pathing:** Use ML to predict the next likely move of an attacker based on historical drift and graph centrality.
- [ ] **Natural Language Query (NLQ):** An AI-powered search bar to ask questions like "Which of my assets are vulnerable to Log4Shell and accessible from the internet?"

## 3. Enterprise Integration
- [x] **External Hook System (Foundation):** Slack and Jira notification support integrated into ExecutionEngine.
- [ ] **Global Asset Inventory (GAI):** Continuous, background discovery across AWS, Azure, GCP, and On-Prem to maintain a "Living Graph."
- [ ] **SAML/OIDC Support:** Enterprise-grade identity provider integration for SSO.

## 4. Technical Debt & Performance
- [ ] **C++ Core Optimization:** Porting high-volume normalization logic to a compiled language for massive scale.
- [ ] **Graph Database Migration:** Moving from NetworkX/PostgreSQL to a dedicated graph store (Neo4j) for complex path queries.

# COSF: The Road to v1.0 (Release Candidate)

The Cyber Operations Standardization Framework (COSF) has achieved its core architectural goals. The following tasks define the path to a stable v1.0 release.

---

## 1. Enterprise Orchestration & Deployment
- [ ] **Docker Compose Orchestration:** Provide a `docker-compose.yaml` to spin up the API, PostgreSQL, and a Redis worker for asynchronous task execution.
- [ ] **Worker Scaling:** Implement a standalone `cosf worker` command to scale execution horizontally across multiple nodes.
- [ ] **Persistent Vault Integration:** Support HashiCorp Vault or AWS Secrets Manager for storing sensitive adapter credentials (API keys, SSH keys).

## 2. Advanced Security Intelligence & Graph
- [ ] **Cross-Tool Correlation Rules:** Implement rules that link findings from different tools (e.g., Nmap service discovery + Nuclei vulnerability detection + Shodan external data).
- [ ] **Temporal Graph Analysis:** Track how the security posture of an asset changes over multiple workflow executions.
- [ ] **Impact Analysis Engine:** Predict the "Blast Radius" of a vulnerability based on the inferred relationship graph.

## 3. Web UI & Reporting Enhancements
- [ ] **Interactive Workflow Builder:** A drag-and-drop interface in the dashboard to compose and validate YAML workflows.
- [ ] **Executive Compliance Reports:** Generate PDF reports mapped to common frameworks (SOC2, NIST, ISO 27001) based on SOM findings.
- [ ] **User Role Management (RBAC):** Implement a full multi-tenant system with granular permissions for Admin, Operator, and Auditor roles.

## 4. Ecosystem Expansion
- [ ] **Official Adapter Repository:** Create a centralized registry for community-contributed tool adapters.
- [ ] **Cloud-Native Discovery:** Deep integration with AWS/Azure/GCP to automatically discover and audit cloud resources based on account permissions.
- [ ] **Incident Response Playbooks:** Pre-built WDL templates for common IR tasks (containment, forensic collection, evidence preservation).

---

## Recent Milestone Accomplishments (Completed):
- [x] **Enterprise CLI:** Added `cosf monitor` for real-time SSE log streaming.
- [x] **Intelligence:** Added `NetworkProximityRule` for subnet-based relationship inference.
- [x] **Normalization:** Enhanced `ShellAdapter` and `PythonAdapter` with automatic JSON-to-SOM normalization.
- [x] **Adapters:** Integrated **Shodan** for external asset reconnaissance.

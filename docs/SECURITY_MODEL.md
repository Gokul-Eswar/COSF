# Security & Non-Repudiation Model

A primary directive of COSF is to make security execution auditable and tamper-evident. The framework implements several layers of defense and auditing.

## 1. Cryptographic Signatures

Every time a workflow executes, a unique Ed25519 public/private key pair is generated.

1.  **Task Signatures:** When an adapter successfully completes and returns an output, the execution engine signs the output payload along with the task ID:
    ```python
    db_task.signature = CryptoManager.sign_message(private_key, f"{db_task.id}:{db_task.raw_output}")
    ```
2.  **Execution Signatures:** The entire workflow execution completion state is also signed.
3.  **Auditability:** Because outputs are signed instantly at runtime, any downstream modification of the database or report can be mathematically proven as tampering. This satisfies compliance standards requiring verifiable non-repudiation (e.g., SOC2, FedRAMP).

## 2. Dynamic Policy Engine

Traditional security automation runs the risk of a tool targeting the wrong asset or using banned parameters. COSF solves this with a two-pass `PolicyEngine`.

*   **Static Pass (`check_plan`):** Validates the parsed workflow graph before anything is scheduled.
*   **Dynamic Pass (`check_task`):** After variables (like injected IPs or credentials) are resolved, and immediately before the adapter is invoked, the policy engine re-evaluates the payload.
    *   *Example:* If a dynamic variable resolves to an internal production subnet (`10.0.0.0/8`), the policy engine can abort the task to prevent an unauthorized scan.

## 3. Sandboxed Adapters

COSF never executes a third-party security tool natively on the host OS. 

*   **Containerization:** The `BaseAdapter` leverages the Docker Engine API. When `Nmap` or `Nuclei` is requested, COSF spins up an ephemeral container (e.g., `instrumentisto/nmap`), executes the tool, captures the `stdout/stderr`, and destroys the container.
*   **Benefits:**
    *   Zero dependency pollution on the host.
    *   Prevents exploit payloads from breaking out of the security tool and compromising the runtime environment.
    *   Ensures consistent execution environments regardless of where COSF is deployed.

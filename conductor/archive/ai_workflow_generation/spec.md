# Specification: AI-Assisted Workflow Generation

## Objective
Enable users to generate complex COSF workflows (YAML) from natural language instructions using LLMs.

## Requirements
1.  **Instruction to YAML**: Translate user prompts (e.g., "Scan my local network and check for high-severity vulnerabilities") into valid COSF WDL.
2.  **Schema Awareness**: The AI must be aware of available adapters (`nmap`, `nuclei`, etc.) and their required parameters.
3.  **Local & Remote LLM Support**: Support for **Ollama** (for local privacy) and **OpenAI/Anthropic** (for high-performance generation).
4.  **CLI Generation Command**: A new CLI command `cosf generate --prompt "..."` to generate and optionally run a workflow.
5.  **Interactive Refinement**: Allow users to refine the generated workflow via a chat-like interface.

## Key Design Considerations
-   The "Prompt" should be combined with a "System Instruction" that includes the COSF JSON Schema and list of registered adapters.
-   Security: Ensure generated workflows are validated before execution to prevent malicious parameter injection.

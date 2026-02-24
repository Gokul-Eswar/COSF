# Implementation Plan: AI-Assisted Workflow Generation

## Phase 1: AI Prompt Engineering
- [x] Create a `PromptManager` in `cosf/ai/prompts.py` to generate the system instructions.
- [x] Include the current JSON schema of `WorkflowSchema` in the prompt for accuracy.
- [x] Implement a tool-discovery mechanism that dynamically injects registered adapters and their capabilities into the AI's context.

## Phase 2: LLM Integration
- [x] Implement a `GenerativeEngine` in `cosf/ai/engine.py` using **LangChain** or a simple `requests`-based wrapper.
- [x] Add configuration support for OpenAI API keys or local Ollama endpoints.

## Phase 3: CLI & Validation
- [x] Add a `cosf generate` command.
- [x] Implement a "Dry Run" and "Validation" step for AI-generated YAML to ensure it passes the `WorkflowParser` schema check.

## Phase 4: Verification & Tests
- [x] Create `tests/test_ai_generation.py`.
- [x] Use mock LLM responses to verify the parsing and validation of generated workflows.
- [x] Test various prompts (e.g., "discovery only," "full assessment," "specific target") and verify the resulting YAML structure.

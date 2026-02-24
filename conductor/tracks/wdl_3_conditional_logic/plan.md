# Implementation Plan: WDL 3.0 - Conditional & Dynamic Logic

## Phase 1: DSL Updates
- [x] Update `WorkflowTask` Pydantic model in `cosf/parser/workflow.py` to include a `when` field (string).
- [x] Add support for boolean logic flags like `continue_on_failure` at the task level.

## Phase 2: Engine Logic (Condition Evaluator)
- [x] Create a `ConditionEvaluator` utility in `cosf/engine/runtime.py` to parse and evaluate the `when` strings against the current execution context.
- [x] Integrate the evaluator into the `ExecutionEngine.run` loop. Before running a task, check its `when` condition.

## Phase 3: Task Skipping Mechanism
- [x] Implement logic to mark tasks as "SKIPPED" in the database (`TaskExecution` model).
- [x] Ensure dependent tasks can still run if their dependency was "SKIPPED" (but completed its evaluation).

## Phase 4: Verification & Tests
- [x] Create `tests/test_conditional_logic.py`.
- [x] Test a workflow where a task is skipped.
- [x] Test a workflow where a task is executed based on a positive match.
- [x] Test complex logical expressions (e.g., `ports contains 443 AND os == 'Linux'`).

# Workflow Definition Language (WDL)

The core mechanism for interacting with COSF is the Workflow Definition Language (WDL), a declarative YAML-based syntax used to define security operations.

## Schema Structure

A workflow consists of a top-level `name` and a list of `tasks`.

```yaml
name: "Example Security Workflow"
tasks:
  - id: step_1
    name: "Run Nmap"
    adapter: "nmap"
    params:
      target: "192.168.1.1"

  - id: step_2
    name: "Run Nuclei"
    adapter: "nuclei"
    depends_on: ["step_1"]
    when: "{{ tasks.step_1.outputs.target_ip }} != None"
    params:
      target: "{{ tasks.step_1.outputs.target_ip }}"
```

### Task Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id` | `string` | No | A unique identifier for the task. If omitted, a UUID is generated. |
| `name` | `string` | Yes | Human-readable name for the step. |
| `adapter` | `string` | Yes | The registered name of the tool adapter (e.g., `nmap`, `nuclei`, `aws`). |
| `depends_on` | `list[string]`| No | A list of task IDs that must complete before this task begins. |
| `params` | `dict` | No | Arguments passed to the adapter. |
| `retries` | `integer` | No | Number of times to retry on failure. Default: `0`. |
| `timeout` | `integer` | No | Maximum execution time in seconds. Default: `300`. |
| `when` | `string` | No | A conditional expression evaluated before execution. |
| `continue_on_failure`| `bool` | No | If true, workflow continues even if this task fails. Default: `false`. |

## Variable Resolution Context

Parameters and `when` conditions can dynamically access outputs from previously executed tasks.

**Syntax:** `{{ tasks.<task_id>.outputs.<key> }}`

**Example:**
If an `aws` adapter task named `get_ips` returns a list of IPs in `target_ips`, a downstream task can reference it:
```yaml
params:
  target: "{{ tasks.get_ips.outputs.target_ips }}"
```

## Conditional Execution (`when`)

The `when` clause allows branching logic. It evaluates string expressions against the resolved context.

Supported Operators:
*   `==` (Equals)
*   `!=` (Not Equals)
*   `contains` (Substring match)
*   `in` (Reverse substring match)

**Example:**
```yaml
when: "{{ tasks.recon.outputs.os_type }} contains 'Linux'"
```
If the condition evaluates to `false`, the task is marked as `SKIPPED`.
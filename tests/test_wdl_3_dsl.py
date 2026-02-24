import pytest
from cosf.parser.workflow import WorkflowParser, WorkflowSchema

def test_workflow_task_conditional_fields():
    yaml_content = """
    name: Conditional Workflow
    tasks:
      - name: Scan
        adapter: nmap
        params: {target: "127.0.0.1"}
      - name: Vulnerability Scan
        adapter: nuclei
        depends_on: [Scan]
        when: "tasks.Scan.outputs.port_80 == 'open'"
        continue_on_failure: true
    """
    parser = WorkflowParser()
    workflow = parser.parse(yaml_content)
    
    assert workflow.name == "Conditional Workflow"
    assert len(workflow.tasks) == 2
    
    scan_task = workflow.tasks[0]
    vuln_task = workflow.tasks[1]
    
    assert scan_task.when is None
    assert scan_task.continue_on_failure is False
    
    assert vuln_task.when == "tasks.Scan.outputs.port_80 == 'open'"
    assert vuln_task.continue_on_failure is True

def test_workflow_task_defaults():
    yaml_content = """
    name: Default Workflow
    tasks:
      - name: Simple Task
        adapter: mock
    """
    parser = WorkflowParser()
    workflow = parser.parse(yaml_content)
    
    task = workflow.tasks[0]
    assert task.when is None
    assert task.continue_on_failure is False

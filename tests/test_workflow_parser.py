import pytest
from pydantic import ValidationError
from cosf.parser.workflow import WorkflowParser

def test_parse_valid_workflow():
    yaml_content = """
name: Network Assessment
tasks:
  - name: Scan Target
    adapter: nmap
    params:
      target: 192.168.1.1
  - name: Check Vulnerabilities
    adapter: nuclei
    params:
      target: 192.168.1.1
"""
    parser = WorkflowParser()
    workflow = parser.parse(yaml_content)
    assert workflow.name == "Network Assessment"
    assert len(workflow.tasks) == 2
    assert workflow.tasks[0].adapter == "nmap"

def test_parse_invalid_workflow_missing_name():
    yaml_content = """
tasks:
  - name: Scan Target
    adapter: nmap
    params:
      target: 192.168.1.1
"""
    parser = WorkflowParser()
    with pytest.raises(ValidationError):
        parser.parse(yaml_content)

def test_parse_invalid_yaml():
    yaml_content = """
name: Network Assessment
tasks:
  - name: Scan Target
    adapter: nmap
    params:
      target: 192.168.1.1
  - name: Check [Vulnerabilities]
    invalid_yaml
"""
    parser = WorkflowParser()
    with pytest.raises(Exception): # Specific YAML error or our custom error
        parser.parse(yaml_content)

def test_parse_empty_workflow():
    parser = WorkflowParser()
    with pytest.raises(Exception, match="Workflow file is empty"):
        parser.parse("")

def test_parse_non_dict_workflow():
    parser = WorkflowParser()
    with pytest.raises(Exception, match="Invalid workflow structure"):
        parser.parse("Just a string, not a dict")

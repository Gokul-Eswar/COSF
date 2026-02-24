import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from cosf.ai.prompts import PromptManager
from cosf.ai.engine import GenerativeEngine
from cosf.parser.workflow import WorkflowSchema

def test_prompt_manager_generation():
    adapters = {"nmap": MagicMock(ADAPTER_DESCRIPTION="Nmap Desc")}
    pm = PromptManager(adapters)
    system_prompt = pm.get_system_prompt()
    
    assert "Cybersecurity Workflow Architect" in system_prompt
    assert "nmap: Nmap Desc" in system_prompt
    assert '"WorkflowSchema"' in system_prompt

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_generative_engine_openai(mock_post):
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": """```yaml
name: AI Workflow
tasks:
  - id: t1
    name: Task 1
    adapter: nmap
```"""}}
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response
    
    pm = PromptManager({})
    engine = GenerativeEngine(pm, provider="openai", api_key="test-key")
    
    yaml_out = await engine.generate_workflow("Create a scan")
    assert "name: AI Workflow" in yaml_out
    
    # Test validation
    workflow = engine.validate_generated_yaml(yaml_out)
    assert isinstance(workflow, WorkflowSchema)
    assert workflow.name == "AI Workflow"

def test_extract_yaml_fallback():
    engine = GenerativeEngine(PromptManager({}))
    text = """Here is your workflow:
name: Simple
tasks:
  - id: 1
    adapter: mock"""
    
    extracted = engine._extract_yaml(text)
    assert extracted.startswith("name: Simple")

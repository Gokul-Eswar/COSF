import pytest
import asyncio
from cosf.engine.adapters.shell import ShellAdapter
from cosf.engine.adapter import TaskResult

@pytest.mark.asyncio
async def test_shell_adapter_echo():
    adapter = ShellAdapter()
    params = {"command": "echo 'hello world'"}
    result = await adapter.run(params)
    
    assert isinstance(result, TaskResult)
    assert result.outputs["stdout"] == "'hello world'" # Windows echo might keep quotes or behave differently
    assert result.outputs["exit_code"] == 0

@pytest.mark.asyncio
async def test_shell_adapter_failure():
    adapter = ShellAdapter()
    # Use a command that is likely to fail on both Windows and Linux
    params = {"command": "non_existent_command_12345"}
    
    # create_subprocess_shell might not raise immediately but return non-zero or stderr
    result = await adapter.run(params)
    assert result.outputs["exit_code"] != 0

@pytest.mark.asyncio
async def test_shell_adapter_missing_command():
    adapter = ShellAdapter()
    with pytest.raises(ValueError, match="Shell adapter requires a 'command' parameter"):
        await adapter.run({})

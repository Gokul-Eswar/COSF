import pytest
from typer.testing import CliRunner
from cosf.cli import app
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio

runner = CliRunner()

def test_cli_monitor_success():
    """Test monitor command successfully streaming logs."""
    execution_id = "test-exec-id"
    
    # Mock httpx.AsyncClient
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    async def mock_aiter_lines():
        yield "data: [10:00:00] INFO: Starting task"
        yield "data: [10:00:05] SUCCESS: Task completed"
    
    mock_response.aiter_lines = mock_aiter_lines
    
    # We need to mock the context manager of client.stream
    # It must support async with
    mock_stream_cm = AsyncMock()
    mock_stream_cm.__aenter__.return_value = mock_response
    
    mock_client = MagicMock() # Use MagicMock for the client itself
    # stream() should return the context manager
    mock_client.stream.return_value = mock_stream_cm
    # __aenter__ and __aexit__ are needed if we mock the client context manager, 
    # but here we use it as 'async with httpx.AsyncClient() as client:'
    
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        result = runner.invoke(app, ["monitor", execution_id])
        
    assert result.exit_code == 0
    assert "Connecting to log stream" in result.output
    assert "[10:00:00] INFO: Starting task" in result.output
    assert "[10:00:05] SUCCESS: Task completed" in result.output

def test_cli_monitor_server_error():
    """Test monitor command handling server errors."""
    execution_id = "test-exec-id"
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    mock_stream_cm = AsyncMock()
    mock_stream_cm.__aenter__.return_value = mock_response
    
    mock_client = MagicMock()
    mock_client.stream.return_value = mock_stream_cm
    
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        result = runner.invoke(app, ["monitor", execution_id])
        
    assert "Error: Server returned status 404" in result.output

def test_cli_monitor_connection_failed():
    """Test monitor command handling connection failures."""
    execution_id = "test-exec-id"
    
    mock_client = MagicMock()
    mock_client.stream.side_effect = Exception("Connection refused")
    
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value = mock_client
    
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        result = runner.invoke(app, ["monitor", execution_id])
        
    assert "Error: Connection lost or failed: Connection refused" in result.output

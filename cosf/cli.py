import asyncio
import typer
from pathlib import Path
from cosf.parser.workflow import WorkflowParser
from cosf.engine.runtime import ExecutionEngine
from cosf.engine.adapter import AdapterRegistry
from cosf.engine.adapters.nmap import NmapAdapter
from cosf.engine.adapters.nuclei import NucleiAdapter
from cosf.engine.adapters.mock import MockAdapter
from cosf.models.database import WorkflowExecution
from cosf.models.db_session import AsyncSessionLocal
from sqlalchemy import select

app = typer.Typer(no_args_is_help=True)

def get_engine():
    """Initializes and returns an ExecutionEngine with default adapters.

    Returns:
        An ExecutionEngine instance with 'nmap', 'nuclei', and 'mock' adapters registered.
    """
    registry = AdapterRegistry()
    registry.register("nmap", NmapAdapter())
    registry.register("nuclei", NucleiAdapter())
    registry.register("mock", MockAdapter())
    return ExecutionEngine(adapter_registry=registry)

@app.command()
def version():
    """Show the current version of COSF."""
    typer.echo("COSF v0.1.0")

@app.command(name="run")
def run(workflow_file: str = typer.Argument(..., help="Path to the workflow YAML file")):
    """Run a security workflow from a YAML file.

    Args:
        workflow_file: The string path to the YAML workflow definition.

    Raises:
        typer.Exit: If the file is not found, parsing fails, or execution fails.
    """
    workflow_path = Path(workflow_file)
    if not workflow_path.exists():
        typer.echo(f"Error: File '{workflow_file}' not found", err=True)
        raise typer.Exit(code=1)

    try:
        content = workflow_path.read_text()
        parser = WorkflowParser()
        workflow = parser.parse(content)
    except Exception as e:
        typer.echo(f"Error: Failed to parse workflow: {e}", err=True)
        raise typer.Exit(code=1)

    engine = get_engine()
    try:
        asyncio.run(engine.run(workflow))
        typer.echo(f"Workflow '{workflow.name}' completed successfully.")
    except Exception as e:
        typer.echo(f"Error: Workflow execution failed: {e}", err=True)
        raise typer.Exit(code=1)

@app.command(name="history")
def history():
    """Show execution history of security workflows."""
    async def get_history():
        async with AsyncSessionLocal() as session:
            stmt = select(WorkflowExecution).order_by(WorkflowExecution.start_time.desc())
            result = await session.execute(stmt)
            executions = result.scalars().all()
            
            if not executions:
                typer.echo("No execution history found.")
                return

            typer.echo(f"{'ID':<38} | {'Workflow':<20} | {'Status':<10} | {'Started':<20}")
            typer.echo("-" * 95)
            for e in executions:
                start_str = e.start_time.strftime("%Y-%m-%d %H:%M:%S")
                typer.echo(f"{e.id:<38} | {e.workflow_name:<20} | {e.status:<10} | {start_str:<20}")

    try:
        asyncio.run(get_history())
    except Exception as e:
        typer.echo(f"Error: Failed to retrieve history: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()

import asyncio
import typer
import json
import os
from pathlib import Path
from typing import Optional
from cosf.parser.workflow import WorkflowParser
from cosf.engine.runtime import ExecutionEngine
from cosf.engine.adapter import AdapterRegistry
from cosf.engine.loader import load_adapters, list_available_plugins
from cosf.models.database import WorkflowExecution
from cosf.models.db_session import AsyncSessionLocal
from sqlalchemy import select

from cosf.engine.reporting import ReportingEngine
from cosf.engine.graph import GraphEngine
from cosf.ai.prompts import PromptManager
from cosf.ai.engine import GenerativeEngine
from sqlalchemy.orm import selectinload

app = typer.Typer(no_args_is_help=True)
plugins_app = typer.Typer(help="Manage and list adapter plugins")
graph_app = typer.Typer(help="Analyze and visualize attack paths")
app.add_typer(plugins_app, name="plugins")
app.add_typer(graph_app, name="graph")

def get_engine():
    """Initializes and returns an ExecutionEngine with dynamically loaded adapters.

    Returns:
        An ExecutionEngine instance with discovered adapters registered.
    """
    registry = AdapterRegistry()
    load_adapters(registry)
    return ExecutionEngine(adapter_registry=registry)

@app.command()
def version():
    """Show the current version of COSF."""
    typer.echo("COSF v0.1.0")

@app.command(name="run")
def run(workflow_file: str = typer.Argument(..., help="Path to the workflow YAML file")):
    """Run a security workflow from a YAML file."""
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

@app.command(name="report")
def report(
    execution_id: str = typer.Argument(..., help="The ID of the execution to report on"),
    format: str = typer.Option("markdown", "--format", "-f", help="Report format (markdown, json, html)")
):
    """Generate a report for a specific workflow execution."""
    async def generate():
        async with AsyncSessionLocal() as session:
            stmt = select(WorkflowExecution).where(WorkflowExecution.id == execution_id).options(selectinload(WorkflowExecution.tasks))
            result = await session.execute(stmt)
            execution = result.scalar_one_or_none()
            
            if not execution:
                typer.echo(f"Error: Execution ID '{execution_id}' not found", err=True)
                return

            engine = ReportingEngine()
            report_path = await engine.generate_report(execution, format=format)
            typer.echo(f"Report generated successfully: {report_path}")

    try:
        asyncio.run(generate())
    except Exception as e:
        typer.echo(f"Error: Failed to generate report: {e}", err=True)
        raise typer.Exit(code=1)

@plugins_app.command(name="list")
def list_plugins():
    """List all available tool adapter plugins."""
    plugins = list_available_plugins()
    if not plugins:
        typer.echo("No plugins found.")
        return

    typer.echo(f"{'Adapter Name':<20} | {'Plugin Path'}")
    typer.echo("-" * 60)
    for name, path in plugins.items():
        typer.echo(f"{name:<20} | {path}")

@graph_app.command(name="analyze")
def analyze_graph():
    """Analyze the security relationship graph based on all execution results."""
    async def analyze():
        engine = GraphEngine()
        await engine.build_from_db()
        num_nodes = engine.graph.number_of_nodes()
        num_edges = engine.graph.number_of_edges()
        
        typer.echo(f"Graph Analysis Summary:")
        typer.echo(f"----------------------")
        typer.echo(f"Total Nodes: {num_nodes}")
        typer.echo(f"Total Edges: {num_edges}")
        
        types = {}
        for _, attrs in engine.graph.nodes(data=True):
            ntype = attrs.get('type', 'unknown')
            types[ntype] = types.get(ntype, 0) + 1
        
        typer.echo("\nNode Type Distribution:")
        for t, count in types.items():
            typer.echo(f"- {t}: {count}")

    try:
        asyncio.run(analyze())
    except Exception as e:
        typer.echo(f"Error: Failed to analyze graph: {e}", err=True)
        raise typer.Exit(code=1)

@graph_app.command(name="visualize")
def visualize_graph():
    """Export the graph as JSON for visualization (D3.js)."""
    async def visualize():
        engine = GraphEngine()
        await engine.build_from_db()
        data = engine.get_graph_data()
        typer.echo(json.dumps(data, indent=2))

    try:
        asyncio.run(visualize())
    except Exception as e:
        typer.echo(f"Error: Failed to export graph: {e}", err=True)
        raise typer.Exit(code=1)

@app.command(name="generate")
def generate_workflow_cli(
    prompt: str = typer.Argument(..., help="Instruction for the workflow to generate"),
    provider: str = typer.Option("ollama", "--provider", "-p", help="AI provider (ollama, openai)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="OPENAI_API_KEY", help="OpenAI API Key")
):
    """Generate a COSF workflow from a natural language prompt."""
    async def generate():
        registry = AdapterRegistry()
        load_adapters(registry)
        
        prompt_mgr = PromptManager(registered_adapters=registry.list_adapters())
        ai_engine = GenerativeEngine(prompt_manager=prompt_mgr, provider=provider, api_key=api_key)
        
        typer.echo(f"Generating workflow with {provider}...")
        yaml_content = await ai_engine.generate_workflow(prompt)
        
        typer.echo("\n--- Generated Workflow ---")
        typer.echo(yaml_content)
        typer.echo("--------------------------")
        
        try:
            ai_engine.validate_generated_yaml(yaml_content)
            typer.echo("\nWorkflow validation: SUCCESS")
        except Exception as e:
            typer.echo(f"\nWorkflow validation: FAILED - {e}", err=True)

    try:
        asyncio.run(generate())
    except Exception as e:
        typer.echo(f"Error: Failed to generate workflow: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()

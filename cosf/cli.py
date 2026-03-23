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
from cosf.utils.crypto import CryptoManager

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

@app.command(name="serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind the server to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind the server to")
):
    """Start the COSF API Control Plane server."""
    import uvicorn
    typer.echo(f"Starting COSF API server on {host}:{port}...")
    uvicorn.run("cosf.api.main:app", host=host, port=port, reload=True)

@app.command(name="run")
def run(
    workflow_file: str = typer.Argument(..., help="Path to the workflow YAML file"),
    remote: Optional[str] = typer.Option(None, "--remote", "-r", help="URL of a remote COSF server to run the workflow on"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Run the workflow in simulation mode (dry run)")
):
    """Run a security workflow from a YAML file (Locally or Remotely)."""
    workflow_path = Path(workflow_file)
    if not workflow_path.exists():
        typer.echo(f"Error: File '{workflow_file}' not found", err=True)
        raise typer.Exit(code=1)

    try:
        content = workflow_path.read_text()
        if remote:
            # Remote execution mode
            import httpx
            typer.echo(f"Sending workflow to remote server: {remote}...")
            response = httpx.post(
                f"{remote.rstrip('/')}/workflows/run",
                json={"workflow_yaml": content, "dry_run": dry_run},
                timeout=30.0
            )
            response.raise_for_status()
            typer.echo(f"Workflow accepted by remote: {response.json().get('message')}")
            return

        # Local execution mode
        parser = WorkflowParser()
        workflow = parser.parse(content)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    engine = get_engine()
    
    if dry_run:
        typer.echo(f"MODE: DRY RUN (Simulation)")
        plan = engine.generate_plan(workflow)
        typer.echo("\n--- Execution Plan ---")
        typer.echo(f"{'Step':<5} | {'ID':<15} | {'Adapter':<10} | {'Name':<25}")
        typer.echo("-" * 65)
        for i, task in enumerate(plan, 1):
            typer.echo(f"{i:<5} | {task['id']:<15} | {task['adapter']:<10} | {task['name']:<25}")
        typer.echo("----------------------\n")

    try:
        asyncio.run(engine.run(workflow, dry_run=dry_run))
        status_msg = "simulated successfully" if dry_run else "completed successfully"
        typer.echo(f"Workflow '{workflow.name}' {status_msg}.")
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

@app.command(name="monitor")
def monitor(
    execution_id: str = typer.Argument(..., help="The ID of the execution to monitor"),
    remote: str = typer.Option("http://127.0.0.1:8000", "--remote", "-r", help="URL of the COSF server"),
    api_key: str = typer.Option("admin-key-123", "--api-key", "-k", help="API Key for authentication")
):
    """Monitor real-time logs of a workflow execution via SSE."""
    async def stream_logs():
        import httpx
        url = f"{remote.rstrip('/')}/api/executions/{execution_id}/logs?token={api_key}"
        typer.echo(f"Connecting to log stream for execution {execution_id}...")
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        typer.echo(f"Error: Server returned status {response.status_code}", err=True)
                        return
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            log_msg = line[6:]
                            typer.echo(log_msg)
        except Exception as e:
            typer.echo(f"Error: Connection lost or failed: {e}", err=True)

    try:
        asyncio.run(stream_logs())
    except KeyboardInterrupt:
        typer.echo("\nMonitoring stopped by user.")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
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

@app.command(name="worker")
def worker(
    queue_name: str = typer.Option("default", "--queue", "-q", help="Name of the queue to listen on"),
    redis_url: str = typer.Option("redis://localhost:6379", "--redis", "-u", envvar="REDIS_URL", help="Redis connection URL")
):
    """Start a COSF distributed worker node."""
    from redis import Redis
    from rq import Worker, Queue, Connection
    
    typer.echo(f"Starting COSF worker on queue: {queue_name}...")
    try:
        conn = Redis.from_url(redis_url)
        with Connection(conn):
            worker = Worker([Queue(queue_name)])
            worker.work()
    except Exception as e:
        typer.echo(f"Error: Worker failed: {e}", err=True)
        raise typer.Exit(code=1)

@app.command(name="verify")
def verify(execution_id: str = typer.Argument(..., help="Execution ID to verify")):
    """Verify the cryptographic integrity of a workflow execution."""
    async def verify_integrity():
        async with AsyncSessionLocal() as session:
            stmt = select(WorkflowExecution).where(WorkflowExecution.id == execution_id).options(selectinload(WorkflowExecution.tasks))
            result = await session.execute(stmt)
            execution = result.scalar_one_or_none()
            
            if not execution:
                typer.echo(f"Error: Execution ID '{execution_id}' not found", err=True)
                return

            pub_key = execution.public_key
            if not pub_key:
                typer.echo("Error: No public key found for this execution (old or unsigned version)", err=True)
                return

            typer.echo(f"Verifying integrity for execution: {execution.id}")
            
            # Verify overall workflow signature
            workflow_msg = f"{execution.id}:{execution.status}"
            if CryptoManager.verify_signature(pub_key, workflow_msg, execution.signature):
                 typer.echo("[SUCCESS] Workflow execution state signature is valid.")
            else:
                 typer.echo("[FAILED] Workflow execution state signature is INVALID or missing.")

            # Verify individual task signatures
            for task in execution.tasks:
                task_msg = f"{task.id}:{task.raw_output or ''}"
                if CryptoManager.verify_signature(pub_key, task_msg, task.signature):
                    typer.echo(f"[SUCCESS] Task '{task.task_name}' signature is valid.")
                else:
                    typer.echo(f"[FAILED] Task '{task.task_name}' signature is INVALID or missing.")

    try:
        asyncio.run(verify_integrity())
    except Exception as e:
        typer.echo(f"Error: Verification failed: {e}", err=True)
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
def analyze_graph(infer: bool = typer.Option(False, "--infer", "-i", help="Perform autonomous relationship inference")):
    """Analyze the security relationship graph based on all execution results."""
    async def analyze():
        engine = GraphEngine()
        await engine.build_from_db(infer=infer)
        num_nodes = engine.graph.number_of_nodes()
        num_edges = engine.graph.number_of_edges()
        
        typer.echo(f"Graph Analysis Summary:")
        typer.echo(f"----------------------")
        typer.echo(f"Total Nodes: {num_nodes}")
        typer.echo(f"Total Edges: {num_edges}")
        
        types = {}
        high_risk_assets = []
        for node_id, attrs in engine.graph.nodes(data=True):
            ntype = attrs.get('type', 'unknown')
            types[ntype] = types.get(ntype, 0) + 1
            
            if ntype == "asset" and attrs.get("risk_score", 0) > 7.0:
                high_risk_assets.append((attrs.get("label"), attrs.get("risk_score")))
        
        typer.echo("\nNode Type Distribution:")
        for t, count in types.items():
            typer.echo(f"- {t}: {count}")

        if high_risk_assets:
            typer.echo("\nHigh Risk Assets Found (>7.0):")
            for name, score in sorted(high_risk_assets, key=lambda x: x[1], reverse=True):
                typer.echo(f"- {name}: {score:.1f}/10.0")
        elif infer:
             typer.echo("\nNo High Risk Assets Found.")

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

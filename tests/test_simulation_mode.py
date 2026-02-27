import pytest
import asyncio
from cosf.engine.runtime import ExecutionEngine
from cosf.parser.workflow import WorkflowParser
from cosf.engine.adapter import AdapterRegistry
from cosf.engine.adapters.nmap import NmapAdapter
from cosf.engine.adapters.nuclei import NucleiAdapter
from cosf.models.database import WorkflowExecution, TaskExecution, DBAsset, DBVulnerability
from cosf.models.db_session import AsyncSessionLocal
from sqlalchemy import select

@pytest.mark.asyncio
async def test_execution_engine_dry_run():
    # Setup registry with real adapters (but we expect them NOT to be called for real)
    registry = AdapterRegistry()
    registry.register("nmap", NmapAdapter())
    registry.register("nuclei", NucleiAdapter())
    
    engine = ExecutionEngine(registry)
    
    yaml_content = """
    name: Simulation Test
    description: Tests the dry run mode
    tasks:
      - id: discovery
        name: Network Discovery
        adapter: nmap
        params:
          target: 127.0.0.1
      - id: vuln_scan
        name: Vulnerability Scan
        adapter: nuclei
        depends_on: [discovery]
        params:
          target: "{{ tasks.discovery.outputs.target_ip }}"
    """
    
    parser = WorkflowParser()
    workflow = parser.parse(yaml_content)
    
    # Run in dry_run mode
    await engine.run(workflow, dry_run=True)
    
    # Verify database state
    async with AsyncSessionLocal() as session:
        # Check WorkflowExecution
        stmt = select(WorkflowExecution).where(WorkflowExecution.workflow_name == "Simulation Test (Dry Run)")
        result = await session.execute(stmt)
        execution = result.scalar_one_or_none()
        assert execution is not None
        assert execution.status == "completed"
        
        # Check TaskExecutions
        stmt = select(TaskExecution).where(TaskExecution.execution_id == execution.id)
        result = await session.execute(stmt)
        tasks = result.scalars().all()
        assert len(tasks) == 2
        for task in tasks:
            assert task.status == "completed"
            assert "simulated" in task.result_json.get("outputs", {}).get("status", "")
            
        # Check generated entities (SOM)
        stmt = select(DBAsset)
        result = await session.execute(stmt)
        assets = result.scalars().all()
        assert len(assets) > 0
        
        stmt = select(DBVulnerability)
        result = await session.execute(stmt)
        vulns = result.scalars().all()
        assert len(vulns) > 0

if __name__ == "__main__":
    asyncio.run(test_execution_engine_dry_run())

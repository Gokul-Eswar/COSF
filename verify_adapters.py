import asyncio
from cosf.engine.adapters.nmap import NmapAdapter
from cosf.engine.adapters.nuclei import NucleiAdapter
from cosf.engine.adapter import TaskResult
from cosf.models.som import Asset, Service, Vulnerability

async def main():
    print("Testing Nmap Adapter (Dry Run)...")
    nmap = NmapAdapter()
    try:
        # Use dry_run=True to avoid real Docker container start if not needed for verification
        result = await nmap.run({"target": "scanme.nmap.org"}, dry_run=True)
        if isinstance(result, TaskResult):
            assets = [e for e in result.entities if isinstance(e, Asset)]
            services = [e for e in result.entities if isinstance(e, Service)]
            print(f"Nmap Results: {len(assets)} assets, {len(services)} services found.")
        else:
            print(f"Nmap Results: Unexpected result type {type(result)}")
    except Exception as e:
        print(f"Nmap Adapter Failed: {e}")

    print("\nTesting Nuclei Adapter (Dry Run)...")
    nuclei = NucleiAdapter()
    try:
        result = await nuclei.run({"target": "https://scanme.nmap.org"}, dry_run=True)
        if isinstance(result, TaskResult):
            vulns = [e for e in result.entities if isinstance(e, Vulnerability)]
            print(f"Nuclei Results: {len(vulns)} vulnerabilities found.")
        else:
            print(f"Nuclei Results: Unexpected result type {type(result)}")
    except Exception as e:
        print(f"Nuclei Adapter Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from cosf.engine.adapters.nmap import NmapAdapter
from cosf.engine.adapters.nuclei import NucleiAdapter

async def main():
    print("Testing Nmap Adapter...")
    nmap = NmapAdapter()
    try:
        # Use a safe target
        results = await nmap.run({"target": "scanme.nmap.org"})
        print(f"Nmap Results: {len(results.get('assets', []))} assets, {len(results.get('services', []))} services found.")
    except Exception as e:
        print(f"Nmap Adapter Failed: {e}")

    print("
Testing Nuclei Adapter...")
    nuclei = NucleiAdapter()
    try:
        results = await nuclei.run({"target": "https://scanme.nmap.org"})
        print(f"Nuclei Results: {len(results.get('vulnerabilities', []))} vulnerabilities found.")
    except Exception as e:
        print(f"Nuclei Adapter Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

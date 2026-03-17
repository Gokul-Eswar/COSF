import httpx
from typing import Dict, Any, List
from cosf.engine.adapter import BaseAdapter, TaskResult

class ShodanAdapter(BaseAdapter):
    """Adapter for Shodan search engine to discover external assets."""
    
    ADAPTER_NAME = "shodan"
    ADAPTER_DESCRIPTION = "Searches Shodan for host information. Requires 'query' and 'api_key'."

    async def _run(self, params: Dict[str, Any]) -> TaskResult:
        query = params.get("query")
        api_key = params.get("api_key")
        
        if not api_key:
            raise ValueError("Shodan adapter requires an 'api_key'.")
        if not query:
            raise ValueError("Shodan adapter requires a 'query'.")

        self.logger.info(f"Searching Shodan for: {query}")
        
        url = "https://api.shodan.io/shodan/host/search"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    params={"key": api_key, "query": query},
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_msg = response.json().get("error", "Unknown Shodan API error")
                    raise RuntimeError(f"Shodan API failed: {error_msg}")
                
                data = response.json()
                raw_output = response.text
                
                return TaskResult(
                    entities=self.normalize(raw_output),
                    outputs={
                        "total": data.get("total", 0),
                        "matches_count": len(data.get("matches", []))
                    },
                    raw_output=raw_output
                )
        except Exception as e:
            self.logger.error(f"Shodan search failed: {e}")
            raise

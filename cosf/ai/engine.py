import httpx
import yaml
import re
from typing import Optional, Dict, Any
from cosf.ai.prompts import PromptManager
from cosf.parser.workflow import WorkflowParser, WorkflowSchema

class GenerativeEngine:
    """Engine for interacting with LLMs to generate COSF workflows."""

    def __init__(self, prompt_manager: PromptManager, provider: str = "openai", api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.prompt_manager = prompt_manager
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url or ("http://localhost:11434/api/generate" if provider == "ollama" else "https://api.openai.com/v1/chat/completions")

    async def generate_workflow(self, instruction: str) -> str:
        """Sends instruction to LLM and returns the generated YAML workflow."""
        system_prompt = self.prompt_manager.get_system_prompt()
        user_prompt = self.prompt_manager.get_user_prompt(instruction)

        if self.provider == "ollama":
            return await self._call_ollama(system_prompt, user_prompt)
        else:
            return await self._call_openai(system_prompt, user_prompt)

    async def _call_openai(self, system: str, user: str) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API Key is required")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4-turbo-preview",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    "temperature": 0.2
                },
                timeout=60.0
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._extract_yaml(content)

    async def _call_ollama(self, system: str, user: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json={
                    "model": "codellama", # or 'mistral', 'llama2'
                    "prompt": f"{system}\n\nUser Instruction: {user}",
                    "stream": False,
                    "options": {"temperature": 0.2}
                },
                timeout=120.0
            )
            response.raise_for_status()
            content = response.json()["response"]
            return self._extract_yaml(content)

    def _extract_yaml(self, text: str) -> str:
        """Extracts YAML content from markdown code blocks if present."""
        pattern = r"```yaml\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: if no code block, try to find the first line starting with 'name:' or 'tasks:'
        if "name:" in text and "tasks:" in text:
            start_index = min(text.find("name:"), text.find("tasks:"))
            return text[start_index:].strip()
            
        return text.strip()

    def validate_generated_yaml(self, yaml_content: str) -> WorkflowSchema:
        """Parses and validates the generated YAML against the COSF schema."""
        parser = WorkflowParser()
        return parser.parse(yaml_content)

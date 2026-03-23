import httpx
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class ExternalHook(ABC):
    """Base class for external system notifications and hooks."""
    
    @abstractmethod
    async def send(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Sends a notification to the external system."""
        pass

class SlackHook(ExternalHook):
    """Sends notifications to Slack via Webhooks."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger("cosf.hooks.slack")

    async def send(self, message: str, context: Optional[Dict[str, Any]] = None):
        payload = {"text": message}
        if context:
            # Optionally add blocks or attachments for richer context
            pass
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")

class JiraHook(ExternalHook):
    """Creates/Updates Jira tickets based on findings."""
    
    def __init__(self, url: str, api_token: str, project_key: str):
        self.url = url
        self.api_token = api_token
        self.project_key = project_key
        self.logger = logging.getLogger("cosf.hooks.jira")

    async def send(self, message: str, context: Optional[Dict[str, Any]] = None):
        # Implementation for Jira issue creation
        self.logger.info(f"Mock Jira Ticket Creation: {message}")

class HookManager:
    """Orchestrates multiple external hooks."""
    
    def __init__(self):
        self.hooks: List[ExternalHook] = []

    def register_hook(self, hook: ExternalHook):
        self.hooks.append(hook)

    async def notify_all(self, message: str, context: Optional[Dict[str, Any]] = None):
        for hook in self.hooks:
            await hook.send(message, context)

def get_hook_manager() -> HookManager:
    """Factory to create and configure a HookManager from environment."""
    manager = HookManager()
    
    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    if slack_url:
        manager.register_hook(SlackHook(slack_url))
        
    jira_url = os.getenv("JIRA_URL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    jira_project = os.getenv("JIRA_PROJECT")
    if jira_url and jira_token and jira_project:
        manager.register_hook(JiraHook(jira_url, jira_token, jira_project))
        
    return manager

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TemplateCategory(str, Enum):
    RECON = "recon"
    VULNERABILITY = "vulnerability"
    EXPLOITATION = "exploitation"
    CLOUD = "cloud"
    COMPLIANCE = "compliance"
    GENERAL = "general"

class TemplateType(str, Enum):
    PLAYBOOK = "playbook"
    ADAPTER = "adapter"

class MarketplaceTemplate(BaseModel):
    id: str
    name: str
    description: str
    category: TemplateCategory
    tags: List[str] = Field(default_factory=list)
    type: TemplateType
    content: Any # WDL dict for playbooks, source/metadata for adapters
    verified: bool = False
    author: str = "COSF Community"
    created_at: str # ISO format

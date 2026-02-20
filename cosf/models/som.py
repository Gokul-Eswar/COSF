from typing import List, Optional, Union
from pydantic import BaseModel, Field, IPvAnyAddress
from uuid import UUID, uuid4

class SOMBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))

class Asset(SOMBase):
    name: str
    ip_address: IPvAnyAddress
    os: Optional[str] = None
    tags: List[str] = []

class Service(SOMBase):
    asset_id: str
    port: int
    protocol: str
    name: Optional[str] = None
    state: Optional[str] = None

class Vulnerability(SOMBase):
    asset_id: str
    cve_id: Optional[str] = None
    severity: str
    description: str
    remediation: Optional[str] = None
    service_id: Optional[str] = None

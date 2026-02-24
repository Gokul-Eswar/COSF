from typing import List, Optional, Union, Dict, Any
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

class Credential(SOMBase):
    asset_id: Optional[str] = None
    username: str
    password: Optional[str] = None
    password_hash: Optional[str] = None
    type: str = "password"  # password, hash, token, key
    source_task_id: Optional[str] = None

class AttackStep(SOMBase):
    name: str
    description: str
    technique_id: Optional[str] = None  # MITRE ATT&CK ID
    status: str = "potential"  # potential, attempted, successful, failed
    evidence_ids: List[str] = []

class Relationship(SOMBase):
    source_id: str
    target_id: str
    type: str  # HAS_VULNERABILITY, RUNS_SERVICE, ACCESSIBLE_VIA, EXPLOITS, USES_CREDENTIAL
    metadata: Dict[str, Any] = {}

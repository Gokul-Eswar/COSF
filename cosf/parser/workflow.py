import yaml
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

def generate_task_id():
    return str(uuid.uuid4())[:8]

class WorkflowTask(BaseModel):
    id: str = Field(default_factory=generate_task_id)
    name: str
    adapter: str
    depends_on: List[str] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)
    retries: int = Field(default=0, ge=0)
    timeout: int = Field(default=300, ge=1)  # Default 5 minutes
    when: Optional[str] = Field(default=None)
    continue_on_failure: bool = Field(default=False)

class WorkflowSchema(BaseModel):
    name: str
    tasks: List[WorkflowTask]

class WorkflowParser:
    def parse(self, content: str) -> WorkflowSchema:
        try:
            data = yaml.safe_load(content)
            if data is None:
                raise ValueError("Workflow file is empty")
            return WorkflowSchema(**data)
        except yaml.YAMLError as e:
            raise Exception(f"Failed to parse YAML: {e}")
        except ValidationError:
            raise
        except (ValueError, TypeError) as e:
             raise Exception(f"Invalid workflow structure: {e}")

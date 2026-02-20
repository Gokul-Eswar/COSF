import yaml
from typing import List, Dict, Any
from pydantic import BaseModel, Field, ValidationError

class WorkflowTask(BaseModel):
    name: str
    adapter: str
    params: Dict[str, Any] = Field(default_factory=dict)

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

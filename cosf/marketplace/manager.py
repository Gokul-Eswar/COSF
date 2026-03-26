import os
import json
from pathlib import Path
from typing import List, Optional
from cosf.marketplace.schema import MarketplaceTemplate, TemplateType

class MarketplaceManager:
    def __init__(self, templates_dir: str = "cosf/marketplace/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self, category: Optional[str] = None, template_type: Optional[TemplateType] = None) -> List[MarketplaceTemplate]:
        templates = []
        for file_path in self.templates_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    template = MarketplaceTemplate(**data)
                    
                    if category and template.category != category:
                        continue
                    if template_type and template.type != template_type:
                        continue
                        
                    templates.append(template)
            except Exception as e:
                print(f"Error loading template {file_path}: {e}")
        return templates

    def get_template(self, template_id: str) -> Optional[MarketplaceTemplate]:
        # Simple lookup by ID (scanning files or mapping)
        for template in self.list_templates():
            if template.id == template_id:
                return template
        return None

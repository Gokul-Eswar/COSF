import json
from pathlib import Path
from typing import List, Any, Dict
from datetime import datetime
from jinja2 import Template
from cosf.models.database import WorkflowExecution, TaskExecution, DBAsset, DBService, DBVulnerability

class ReportingEngine:
    """Engine for generating reports from workflow execution data."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_report(self, execution: WorkflowExecution, format: str = "markdown"):
        """Generates a report for a specific workflow execution."""
        if format == "markdown":
            return self._generate_markdown(execution)
        elif format == "json":
            return self._generate_json(execution)
        elif format == "html":
            return self._generate_html(execution)
        else:
            raise ValueError(f"Unsupported report format: {format}")

    def _generate_markdown(self, execution: WorkflowExecution) -> str:
        report = f"""# Security Assessment Report: {execution.workflow_name}

- **Execution ID:** {execution.id}
- **Status:** {execution.status}
- **Started:** {execution.start_time}
- **Ended:** {execution.end_time}

## Task Summary

| Task Name | Adapter | Status | Duration |
|-----------|---------|--------|----------|
"""
        for task in execution.tasks:
            duration = (task.end_time - task.start_time).total_seconds() if task.end_time else "N/A"
            report += f"| {task.task_name} | {task.adapter} | {task.status} | {duration}s |\n"

        report += "\n## Detailed Results\n\n"
        for task in execution.tasks:
            report += f"### {task.task_name}\n"
            if task.error:
                report += f"**Error:** {task.error}\n\n"
            if task.result_json:
                report += "#### Extracted Entities\n"
                report += "```json\n"
                report += json.dumps(task.result_json, indent=2)
                report += "\n```\n\n"
            
            if task.raw_output:
                report += "#### Raw Tool Output (Evidence)\n"
                report += "```\n"
                report += task.raw_output
                report += "\n```\n\n"
        
        output_file = self.output_dir / f"report_{execution.id}.md"
        output_file.write_text(report)
        return str(output_file)

    def _generate_json(self, execution: WorkflowExecution) -> str:
        data = {
            "execution_id": execution.id,
            "workflow_name": execution.workflow_name,
            "status": execution.status,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "tasks": [
                {
                    "name": t.task_name,
                    "adapter": t.adapter,
                    "status": t.status,
                    "results": t.result_json,
                    "error": t.error
                } for t in execution.tasks
            ]
        }
        output_file = self.output_dir / f"report_{execution.id}.json"
        output_file.write_text(json.dumps(data, indent=2))
        return str(output_file)

    def _generate_html(self, execution: WorkflowExecution) -> str:
        # Simplified HTML template
        template_str = """
        <html>
        <head>
            <title>COSF Report - {{ execution.workflow_name }}</title>
            <style>
                body { font-family: sans-serif; margin: 40px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .status-completed { color: green; }
                .status-failed { color: red; }
            </style>
        </head>
        <body>
            <h1>Security Assessment Report: {{ execution.workflow_name }}</h1>
            <p><strong>Execution ID:</strong> {{ execution.id }}</p>
            <p><strong>Status:</strong> <span class="status-{{ execution.status }}">{{ execution.status }}</span></p>
            
            <h2>Tasks</h2>
            <table>
                <tr><th>Task</th><th>Adapter</th><th>Status</th></tr>
                {% for task in execution.tasks %}
                <tr>
                    <td>{{ task.task_name }}</td>
                    <td>{{ task.adapter }}</td>
                    <td>{{ task.status }}</td>
                </tr>
                {% endfor %}
            </table>
        </body>
        </html>
        """
        template = Template(template_str)
        html_content = template.render(execution=execution)
        output_file = self.output_dir / f"report_{execution.id}.html"
        output_file.write_text(html_content)
        return str(output_file)

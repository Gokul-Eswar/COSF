import json
from pathlib import Path
from typing import List, Any, Dict
from datetime import datetime
from jinja2 import Template
from cosf.models.database import WorkflowExecution, TaskExecution, DBAsset, DBService, DBVulnerability

class ReportingEngine:
    """Engine for generating reports from workflow execution data."""

    def __init__(self, output_base_dir: str = "reports"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

    async def generate_report(self, execution: WorkflowExecution, format: str = "markdown"):
        """Generates a report for a specific workflow execution."""
        # Create execution-specific directory for evidence
        exec_dir = self.output_base_dir / execution.id
        exec_dir.mkdir(parents=True, exist_ok=True)
        evidence_dir = exec_dir / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        # Save evidence files
        for task in execution.tasks:
            if task.raw_output:
                # Use task name and adapter for filename
                clean_name = task.task_name.lower().replace(" ", "_")
                ext = "xml" if task.adapter == "nmap" else "json" if task.adapter == "nuclei" else "txt"
                evidence_file = evidence_dir / f"{clean_name}_{task.adapter}.{ext}"
                evidence_file.write_text(task.raw_output)
                # Store relative path for report linking
                task.evidence_path = f"evidence/{evidence_file.name}"

        if format == "markdown":
            return self._generate_markdown(execution, exec_dir)
        elif format == "json":
            return self._generate_json(execution, exec_dir)
        elif format == "html":
            return self._generate_html(execution, exec_dir)
        else:
            raise ValueError(f"Unsupported report format: {format}")

    def _generate_markdown(self, execution: WorkflowExecution, exec_dir: Path) -> str:
        report = f"""# Security Assessment Report: {execution.workflow_name}

- **Execution ID:** {execution.id}
- **Status:** {execution.status}
- **Started:** {execution.start_time}
- **Ended:** {execution.end_time}

## Task Summary

| Task Name | Adapter | Status | Duration | Evidence |
|-----------|---------|--------|----------|----------|
"""
        for task in execution.tasks:
            duration = (task.end_time - task.start_time).total_seconds() if task.end_time else "N/A"
            evidence_link = f"[View]({getattr(task, 'evidence_path', '#')})" if hasattr(task, 'evidence_path') else "N/A"
            report += f"| {task.task_name} | {task.adapter} | {task.status} | {duration}s | {evidence_link} |\n"

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
                report += f"#### Raw Tool Output\nStored at: `{getattr(task, 'evidence_path', 'N/A')}`\n\n"
        
        output_file = exec_dir / "report.md"
        output_file.write_text(report)
        return str(output_file)

    def _generate_json(self, execution: WorkflowExecution, exec_dir: Path) -> str:
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
                    "evidence_file": getattr(t, 'evidence_path', None),
                    "error": t.error
                } for t in execution.tasks
            ]
        }
        output_file = exec_dir / "report.json"
        output_file.write_text(json.dumps(data, indent=2))
        return str(output_file)

    def _generate_html(self, execution: WorkflowExecution, exec_dir: Path) -> str:
        # Calculate normalization statistics
        total_entities = 0
        entity_counts = {"Asset": 0, "Service": 0, "Vulnerability": 0, "Other": 0}
        
        for task in execution.tasks:
            if task.result_json:
                # result_json can be a dict with "entities" key or a list directly
                entities = []
                if isinstance(task.result_json, dict) and "entities" in task.result_json:
                    entities = task.result_json["entities"]
                elif isinstance(task.result_json, list):
                    entities = task.result_json
                
                total_entities += len(entities)
                for e in entities:
                    # Very basic heuristic to count types from JSON
                    if "ip_address" in e: entity_counts["Asset"] += 1
                    elif "port" in e: entity_counts["Service"] += 1
                    elif "severity" in e: entity_counts["Vulnerability"] += 1
                    else: entity_counts["Other"] += 1

        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>COSF Dashboard - {{ execution.workflow_name }}</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono&display=swap');
                body { font-family: 'Inter', sans-serif; }
                code, pre { font-family: 'JetBrains Mono', monospace; }
                .status-completed { @apply bg-green-100 text-green-800 border-green-200; }
                .status-failed { @apply bg-red-100 text-red-800 border-red-200; }
                .status-running { @apply bg-blue-100 text-blue-800 border-blue-200; }
            </style>
        </head>
        <body class="bg-gray-50 text-gray-900 min-h-screen">
            <header class="bg-slate-900 text-white py-8 px-6 shadow-lg mb-8">
                <div class="max-w-6xl mx-auto flex justify-between items-center">
                    <div>
                        <h1 class="text-3xl font-bold tracking-tight">Cyber Operations Report</h1>
                        <p class="text-slate-400 mt-2">Workflow: <span class="text-white font-semibold">{{ execution.workflow_name }}</span></p>
                    </div>
                    <div class="text-right">
                        <span class="px-4 py-2 rounded-full text-sm font-bold uppercase border-2 
                            {% if execution.status == 'completed' %}status-completed{% elif execution.status == 'failed' %}status-failed{% else %}status-running{% endif %}">
                            {{ execution.status }}
                        </span>
                        <p class="text-slate-400 text-sm mt-3">ID: {{ execution.id }}</p>
                    </div>
                </div>
            </header>

            <main class="max-w-6xl mx-auto px-6 pb-12">
                <!-- Summary Section -->
                <section class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <h3 class="text-gray-500 text-sm font-semibold uppercase tracking-wider mb-2">Started</h3>
                        <p class="text-xl font-bold">{{ execution.start_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                    </div>
                    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <h3 class="text-gray-500 text-sm font-semibold uppercase tracking-wider mb-2">Duration</h3>
                        <p class="text-xl font-bold">
                            {% if execution.end_time %}
                                {{ ((execution.end_time - execution.start_time).total_seconds()) | round(2) }}s
                            {% else %}
                                N/A
                            {% endif %}
                        </p>
                    </div>
                    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <h3 class="text-gray-500 text-sm font-semibold uppercase tracking-wider mb-2">Tasks Executed</h3>
                        <p class="text-xl font-bold">{{ execution.tasks | length }}</p>
                    </div>
                </section>

                <!-- Normalization Quality Section -->
                <section class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-8">
                    <div class="px-6 py-4 border-b border-gray-100 bg-indigo-50">
                        <h2 class="text-lg font-bold text-indigo-900 flex items-center">
                            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Normalization Quality Report
                        </h2>
                    </div>
                    <div class="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <p class="text-gray-500 text-xs font-bold uppercase mb-1">Total SOM Objects</p>
                            <p class="text-2xl font-black text-indigo-600">{{ total_entities }}</p>
                        </div>
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <p class="text-gray-500 text-xs font-bold uppercase mb-1">Assets</p>
                            <p class="text-2xl font-black">{{ entity_counts['Asset'] }}</p>
                        </div>
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <p class="text-gray-500 text-xs font-bold uppercase mb-1">Services</p>
                            <p class="text-2xl font-black">{{ entity_counts['Service'] }}</p>
                        </div>
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <p class="text-gray-500 text-xs font-bold uppercase mb-1">Vulnerabilities</p>
                            <p class="text-2xl font-black text-red-600">{{ entity_counts['Vulnerability'] }}</p>
                        </div>
                    </div>
                </section>

                <!-- Tasks List -->
                <section class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-8">
                    <div class="px-6 py-4 border-b border-gray-100 bg-gray-50">
                        <h2 class="text-lg font-bold">Workflow Timeline</h2>
                    </div>
                    <table class="w-full">
                        <thead class="bg-gray-50 text-gray-500 text-xs font-semibold uppercase">
                            <tr>
                                <th class="px-6 py-4 text-left">Task Name</th>
                                <th class="px-6 py-4 text-left">Adapter</th>
                                <th class="px-6 py-4 text-left">Status</th>
                                <th class="px-6 py-4 text-left">Evidence</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            {% for task in execution.tasks %}
                            <tr class="hover:bg-gray-50 transition-colors">
                                <td class="px-6 py-4 font-semibold">{{ task.task_name }}</td>
                                <td class="px-6 py-4"><code class="text-indigo-600 bg-indigo-50 px-2 py-1 rounded text-sm">{{ task.adapter }}</code></td>
                                <td class="px-6 py-4">
                                    <span class="px-3 py-1 rounded-full text-xs font-bold uppercase 
                                        {% if task.status == 'completed' %}status-completed{% elif task.status == 'failed' %}status-failed{% else %}status-running{% endif %}">
                                        {{ task.status }}
                                    </span>
                                </td>
                                <td class="px-6 py-4">
                                    {% if task.evidence_path %}
                                        <a href="{{ task.evidence_path }}" target="_blank" class="text-blue-600 hover:underline flex items-center">
                                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                            View Raw
                                        </a>
                                    {% else %}
                                        <span class="text-gray-400">N/A</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </section>

                <!-- Detailed Task Results -->
                <h2 class="text-2xl font-bold mb-6">Execution Details</h2>
                <div class="space-y-8">
                    {% for task in execution.tasks %}
                    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                            <h3 class="text-xl font-bold">{{ task.task_name }}</h3>
                            <code class="text-sm bg-gray-200 px-2 py-1 rounded">{{ task.adapter }}</code>
                        </div>
                        <div class="p-6">
                            {% if task.error %}
                            <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
                                <p class="text-red-700 font-bold">Error Encountered</p>
                                <p class="text-red-600 text-sm mt-1">{{ task.error }}</p>
                            </div>
                            {% endif %}

                            {% if task.result_json %}
                            <h4 class="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4">Normalized Security Objects</h4>
                            <div class="bg-slate-900 rounded-lg p-4 overflow-x-auto">
                                <pre class="text-indigo-300 text-sm">{{ task.result_json | tojson(indent=2) }}</pre>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </main>
            <footer class="bg-white border-t border-gray-200 py-8 text-center text-gray-500 text-sm">
                Generated by Cyber Operations Standardization Framework (COSF) &bull; {{ execution.end_time.strftime('%Y-%m-%d %H:%M:%S') if execution.end_time else 'Running' }}
            </footer>
        </body>
        </html>
        """
        template = Template(template_str)
        html_content = template.render(
            execution=execution, 
            total_entities=total_entities, 
            entity_counts=entity_counts
        )
        output_file = exec_dir / "dashboard.html"
        output_file.write_text(html_content)
        return str(output_file)

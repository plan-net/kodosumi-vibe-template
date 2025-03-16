# CrewAI Flow Reference Guide

## Overview

This guide provides detailed reference documentation for the CrewAI flow components in the Kodosumi template. It covers the structure, configuration, and usage of agents, tasks, tools, and crews.

## Directory Structure

```
workflows/crewai_flow/
├── agents/              # Agent definitions
├── crews/              # Crew definitions
│   └── first_crew/     # Example crew implementation
├── tasks/              # Task definitions
├── tools/              # Tool definitions
├── templates/          # HTML templates for web interface
├── __init__.py
├── main.py            # Flow implementation
└── serve.py           # Kodosumi service definition
```

## Flow State

The flow state is defined using Pydantic models:

```python
from pydantic import BaseModel

class CrewAIFlowState(BaseModel):
    datasets: list[str] = []
    output_format: str = "markdown"
    results: dict = {}
```

## Flow Implementation

The main flow is implemented in `main.py`:

```python
from crewai.flow import Flow, listen, start
from workflows.common.utils import initialize_ray, shutdown_ray

class CrewAIFlow(Flow[CrewAIFlowState]):
    @start()
    def validate_inputs(self):
        """Validate input datasets"""
        if not self.state.datasets:
            raise ValueError("No datasets selected")

    @listen(validate_inputs)
    def analyze_data(self):
        """Run data analysis using CrewAI"""
        # Initialize crew and run analysis
        crew = self.setup_crew()
        result = crew.run()
        self.state.results = result

    @listen(analyze_data)
    def format_results(self):
        """Format results based on output_format"""
        from workflows.common.formatters import format_output
        return format_output(
            self.state.results,
            self.state.output_format
        )

async def kickoff(inputs: dict = None):
    """Entry point for Kodosumi"""
    flow = CrewAIFlow()
    if inputs:
        for key, value in inputs.items():
            if hasattr(flow.state, key):
                setattr(flow.state, key, value)
    return await flow.kickoff_async()
```

## Kodosumi Service

The service is defined in `serve.py`:

```python
from pathlib import Path
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ray.serve import deployment, ingress
from kodosumi.serve import Launch, ServeAPI

app = ServeAPI()
templates = Jinja2Templates(
    directory=Path(__file__).parent.joinpath("templates"))

@deployment
@ingress(app)
class CrewAIFlowService:
    @app.get("/", name="CrewAI Flow")
    async def get(self, request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="form.html",
            context={"title": "CrewAI Flow"}
        )

    @app.post("/")
    async def post(self, request: Request):
        form_data = await request.form()
        datasets = form_data.getlist("datasets")
        return Launch(request, "workflows.crewai_flow.main:kickoff", {
            "datasets": datasets,
            "output_format": form_data.get("output_format", "markdown")
        })

fast_app = CrewAIFlowService.bind()
```

## Crew Definition

Crews are defined using the `@CrewBase` decorator:

```python
from crewai.project import CrewBase, agent, crew, task
from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

@CrewBase
class AnalysisCrew:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2
        )
    
    @agent
    def researcher(self) -> Agent:
        return Agent(
            role="Research Analyst",
            goal="Analyze data and extract insights",
            backstory="Expert data analyst",
            llm=self.llm
        )
    
    @agent
    def writer(self) -> Agent:
        return Agent(
            role="Technical Writer",
            goal="Create clear and concise reports",
            backstory="Experienced technical writer",
            llm=self.llm
        )
    
    @task
    def analyze_data(self) -> Task:
        return Task(
            description="Analyze the provided datasets",
            agent=self.researcher()
        )
    
    @task
    def write_report(self) -> Task:
        return Task(
            description="Write a report based on the analysis",
            agent=self.writer()
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
```

## Web Interface

The HTML template for the web interface:

```html
<!-- workflows/crewai_flow/templates/form.html -->
{% extends "_base.html" %}
{% block main %}
<form method="post">
    <label>
        Select Datasets:
        <select name="datasets" multiple required>
            <option value="dataset1">Dataset 1</option>
            <option value="dataset2">Dataset 2</option>
        </select>
    </label>
    <label>
        Output Format:
        <select name="output_format">
            <option value="markdown">Markdown</option>
            <option value="json">JSON</option>
        </select>
    </label>
    <button type="submit">Run Analysis</button>
</form>
{% endblock %}
```

## Configuration

Example Kodosumi configuration:

```yaml
# config.yaml
applications:
- name: crewai_flow
  route_prefix: /crewai
  import_path: workflows.crewai_flow.serve:fast_app
  runtime_env:
    env_vars:
      PYTHONPATH: .
      OPENAI_API_KEY: ${OPENAI_API_KEY}
```

## Error Handling

```python
from workflows.common.processors import handle_flow_error

try:
    result = crew.run()
except Exception as e:
    return handle_flow_error(flow_state, output_format)
```

## Resource Management

```python
# Let Kodosumi handle Ray in production
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"
initialize_ray(is_kodosumi)
try:
    # Flow code
finally:
    shutdown_ray(is_kodosumi)
```

## API Reference

### Flow Methods

- `validate_inputs()`: Validates input datasets
- `analyze_data()`: Runs data analysis using CrewAI
- `format_results()`: Formats results based on output format
- `kickoff(inputs: dict = None)`: Entry point for Kodosumi

### Service Methods

- `get(request: Request)`: Renders the web interface
- `post(request: Request)`: Handles form submission and launches flow

### Crew Methods

- `researcher()`: Creates research analyst agent
- `writer()`: Creates technical writer agent
- `analyze_data()`: Creates data analysis task
- `write_report()`: Creates report writing task
- `crew()`: Creates and configures the crew

## Additional Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [Ray Documentation](https://docs.ray.io/)
- [Kodosumi Documentation](https://docs.kodosumi.com/) 
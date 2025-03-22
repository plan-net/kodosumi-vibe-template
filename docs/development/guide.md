# Development Guide

## Overview

This guide explains how to develop CrewAI flows using the Kodosumi template. You'll learn how to:
- Create new workflows
- Define crews and agents
- Add tasks and tools
- Test and debug your flows
- Deploy with Kodosumi

## Project Structure

```
workflows/
├── common/
│   ├── formatters.py    # Output formatting utilities
│   ├── processors.py    # Data processing utilities
│   ├── static/          # Shared static files (CSS, JS, images)
│   └── utils.py         # General utilities
├── example/
│   ├── agents/          # Agent definitions
│   ├── crews/           # Crew definitions
│   ├── tasks/           # Task definitions
│   ├── tools/           # Tool definitions
│   ├── templates/       # HTML templates for web interface
│   ├── static/          # Workflow-specific static files
│   ├── main.py          # Flow implementation
│   └── serve.py         # Kodosumi service definition
└── another_flow/        # Another workflow package
```

## Creating a New Workflow

1. **Create Workflow Directory**
   ```bash
   mkdir -p workflows/my_workflow/{agents,crews,tasks,tools,templates}
   touch workflows/my_workflow/{__init__.py,main.py,serve.py}
   ```

2. **Define Flow State and Steps**
   ```python
   # workflows/my_workflow/main.py
   from crewai.flow import Flow, listen, start
   from pydantic import BaseModel
   
   class MyFlowState(BaseModel):
       input_text: str
       output_format: str = "markdown"
       results: dict = {}
   
   class MyFlow(Flow[MyFlowState]):
       @start()
       def validate_inputs(self):
           print("Validating inputs...")
           # Input validation logic
   
       @listen(validate_inputs)
       def process_data(self):
           print("Processing data...")
           # Processing logic
   
       @listen(process_data)
       def finalize_results(self):
           print("Finalizing results...")
           # Format and return results
   
   async def kickoff(inputs: dict = None):
       """Entry point for Kodosumi"""
       flow = MyFlow()
       if inputs:
           for key, value in inputs.items():
               if hasattr(flow.state, key):
                   setattr(flow.state, key, value)
       return await flow.kickoff_async()
   ```

3. **Create Kodosumi Service**
   ```python
   # workflows/my_workflow/serve.py
   from pathlib import Path
   from fastapi import Request
   from fastapi.responses import HTMLResponse
   from fastapi.templating import Jinja2Templates
   from fastapi.staticfiles import StaticFiles
   from ray.serve import deployment, ingress
   from kodosumi.serve import Launch, ServeAPI
   
   app = ServeAPI()
   templates = Jinja2Templates(
       directory=Path(__file__).parent.joinpath("templates"))
   
   # Mount workflow-specific static files (if needed)
   app.mount("/static", StaticFiles(
       directory=Path(__file__).parent.joinpath("static")), name="static")
   
   # Mount common static files
   app.mount("/common/static", StaticFiles(
       directory=Path(__file__).parent.parent.joinpath("common/static")), name="common_static")
   
   @deployment
   @ingress(app)
   class MyWorkflowService:
       @app.get("/", name="My Workflow")
       async def get(self, request: Request) -> HTMLResponse:
           return templates.TemplateResponse(
               request=request,
               name="form.html",
               context={"title": "My Workflow"}
           )
   
       @app.post("/")
       async def post(self, request: Request):
           form_data = await request.form()
           return Launch(request, "workflows.my_workflow.main:kickoff", {
               "input_text": form_data.get("input_text", ""),
               "output_format": form_data.get("output_format", "markdown")
           })
   
   fast_app = MyWorkflowService.bind()
   ```

## Defining Crews

Create crews using the `@CrewBase` decorator:

```python
# workflows/my_workflow/crews/analysis_crew.py
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
    def analyst(self) -> Agent:
        return Agent(
            role="Data Analyst",
            goal="Analyze data and provide insights",
            backstory="Expert data analyst",
            llm=self.llm
        )
    
    @task
    def analyze_task(self) -> Task:
        return Task(
            description="Analyze the data",
            agent=self.analyst()
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

## Ray Integration

The template handles Ray initialization automatically:

```python
from workflows.common.utils import initialize_ray, shutdown_ray

# Check if running in Kodosumi
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"

# Initialize Ray (Kodosumi handles this in production)
initialize_ray(is_kodosumi)

try:
    # Your workflow code here
    pass
finally:
    # Shutdown Ray (Kodosumi handles this in production)
    shutdown_ray(is_kodosumi)
```

### Ray Example Scripts

The repository includes example scripts in `examples/ray/` that demonstrate key Ray patterns used in the Kodosumi framework:

#### Basic Remote Functions

`ray_test.py` demonstrates the fundamentals of Ray:
- Initializing Ray
- Defining remote functions with `@ray.remote`
- Submitting tasks with `.remote()`
- Retrieving results with `ray.get()`

This pattern is used for simple, stateless task offloading.

#### Parallel Processing

`ray_parallel_test.py` demonstrates parallel processing of multiple tasks:
- Submitting multiple tasks concurrently
- Aggregating results from parallel execution
- Organizing results by priority

This is the pattern used in the `process_insights_in_parallel` method in workflows.

#### Actor Model

`ray_actor_model.py` demonstrates stateful processing with Ray Actors:
- Creating actor instances with specializations
- Maintaining state across method calls
- Routing tasks to appropriate actors
- Tracking processing history

This pattern is useful for stateful agents and workflow components.

#### Running Examples

```bash
# Run all examples
python examples/ray/run_all_examples.py

# Run specific examples
python examples/ray/run_all_examples.py basic     # Just the basic example
python examples/ray/run_all_examples.py parallel  # Parallel processing
python examples/ray/run_all_examples.py actor     # Actor model
```

These examples serve as both learning resources and documentation of recommended Ray patterns.

## Web Interface

Create HTML templates for your workflow:

```html
<!-- workflows/my_workflow/templates/form.html -->
{% extends "_base.html" %}
{% block main %}
<form method="post">
    <label>
        Input Text:
        <textarea name="input_text" required></textarea>
    </label>
    <label>
        Output Format:
        <select name="output_format">
            <option value="markdown">Markdown</option>
            <option value="json">JSON</option>
        </select>
    </label>
    <button type="submit">Run Workflow</button>
</form>
{% endblock %}
```

### Shared Static Files

The template includes a shared static files directory at `workflows/common/static` that contains common assets used across different workflows:

- CSS files (Beer CSS framework and Kodosumi styles)
- JavaScript libraries
- Common images and icons

To use these shared assets in your templates:

```html
<!-- Reference common static files in your HTML templates -->
<link rel="icon" href="/common/static/favicon.ico" type="image/x-icon">
<link href="/common/static/beer.css" rel="stylesheet">
<link href="/common/static/kodosumi.css" rel="stylesheet">
<script src="/common/static/beer.min.js"></script>

<!-- Include images -->
<img src="/common/static/logo.png" alt="Kodosumi Logo">
```

This approach prevents duplication of assets across multiple workflows and ensures consistent styling and behavior.

## Testing

### Unit Tests

```python
# tests/workflows/my_workflow/test_crew.py
import pytest
from workflows.my_workflow.crews.analysis_crew import AnalysisCrew

def test_crew_creation():
    crew_instance = AnalysisCrew()
    crew = crew_instance.crew()
    assert len(crew.agents) > 0
    assert len(crew.tasks) > 0

def test_task_execution(mocker):
    crew_instance = AnalysisCrew()
    task = crew_instance.analyze_task()
    result = task.execute()
    assert result is not None
```

### Integration Tests

```python
# tests/workflows/my_workflow/test_workflow.py
from fastapi.testclient import TestClient
from workflows.my_workflow.serve import fast_app

def test_workflow_endpoint():
    client = TestClient(fast_app)
    response = client.post(
        "/",
        data={
            "input_text": "Test data",
            "output_format": "json"
        }
    )
    assert response.status_code == 200
```

## Debugging

### Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Processing task...")
```

### Ray Dashboard

Monitor Ray tasks:
```bash
ray start --head --dashboard-host=0.0.0.0
# Access at http://localhost:8265
```

## Deployment

1. **Configure Kodosumi**
   ```yaml
   # config.yaml
   applications:
   - name: my_workflow
     route_prefix: /my_workflow
     import_path: workflows.my_workflow.serve:fast_app
     runtime_env:
       env_vars:
         PYTHONPATH: .
         OPENAI_API_KEY: ${OPENAI_API_KEY}
   ```

2. **Deploy**
   ```bash
   # Start Ray
   ray start --head

   # Start Kodosumi services
   python -m kodosumi.cli spool
   serve deploy config.yaml
   python -m kodosumi.cli serve --register http://localhost:8001/-/routes

   # Access at http://localhost:3370/my_workflow
   ```

## Best Practices

1. **Flow Organization**
   - Keep flow logic in `main.py`
   - Use `serve.py` for web interface
   - Organize crews in subdirectories

2. **Error Handling**
   ```python
   from workflows.common.processors import handle_flow_error

   try:
       result = crew.run(input_data)
   except Exception as e:
       return handle_flow_error(flow_state, output_format)
   ```

3. **Resource Management**
   ```python
   # Let Kodosumi handle Ray in production
   initialize_ray(is_kodosumi)
   try:
       # Flow code
   finally:
       shutdown_ray(is_kodosumi)
   ```

## Additional Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [Ray Documentation](https://docs.ray.io/)
- [Kodosumi Documentation](https://docs.kodosumi.com/) 
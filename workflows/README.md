# Creating Your Own Workflow

This directory contains all CrewAI workflows. Each workflow is a separate project that can be independently developed and deployed.

## Directory Structure

```
workflows/
├── common/              # Shared utilities for all workflows
│   ├── __init__.py
│   ├── formatters.py   # Output formatting utilities
│   ├── processors.py   # Parallel processing utilities
│   └── utils.py        # General utilities
└── your_workflow/      # Your workflow directory
    ├── __init__.py
    ├── main.py
    ├── serve.py
    ├── crews/
    │   └── your_crew/
    │       ├── __init__.py
    │       └── your_crew.py
    └── README.md
```

## Creating a New Workflow

1. Create a new directory for your workflow:
   ```bash
   mkdir workflows/my_workflow
   ```

2. Inside your workflow directory, create this structure:
   ```
   my_workflow/
   ├── __init__.py        # Empty file for Python package
   ├── main.py            # Your flow implementation
   ├── serve.py           # FastAPI service endpoints
   ├── crews/             # Your crews
   │   └── my_crew/       # A specific crew
   │       ├── __init__.py
   │       └── my_crew.py
   └── README.md          # Document your workflow
   ```

3. Look at `crewai_flow` as an example implementation.

## Using Common Utilities

The `common` directory contains shared utilities that you can use in your workflow:

1. **Formatters** (`common.formatters`):
   ```python
   from workflows.common.formatters import format_output
   
   # Format your output as markdown or JSON
   formatted_result = format_output(insights, output_format="markdown")
   ```

2. **Processors** (`common.processors`):
   ```python
   from workflows.common.processors import process_with_ray_or_locally
   
   # Process items in parallel (using Ray if available)
   results = process_with_ray_or_locally(items, process_func)
   ```

3. **Utils** (`common.utils`):
   ```python
   from workflows.common.utils import initialize_ray
   
   # Initialize Ray for parallel processing
   initialize_ray()
   ```

## Implementation Guide

### 1. Create Your Crew

In `crews/my_crew/my_crew.py`:
```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from workflows.common.formatters import format_output

class MyOutput(BaseModel):
    result: str = Field(..., description="The result")

@CrewBase
class MyCrew:
    def __init__(self):
        super().__init__()
        # Initialize your crew
    
    @agent
    def my_agent(self) -> Agent:
        return Agent(
            name="My Agent",
            role="Specific Role",
            goal="Clear Goal",
            backstory="Relevant Backstory"
        )
    
    @task
    def my_task(self) -> Task:
        return Task(
            agent=self.my_agent(),
            output_pydantic=MyOutput
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential
        )
```

### 2. Implement Your Flow

In `main.py`:
```python
from crewai.project import Flow, flow, state
from pydantic import BaseModel
from workflows.common.processors import process_with_ray_or_locally
from workflows.common.utils import initialize_ray

class MyState(BaseModel):
    result: str = ""

@Flow
class MyFlow:
    def __init__(self):
        super().__init__()
        self.state = MyState()
        initialize_ray()  # Initialize Ray if needed
    
    @flow
    def run(self):
        # Implement your flow logic
        pass
```

### 3. Create API Endpoints

In `serve.py`:
```python
from fastapi import FastAPI
from .main import MyFlow

app = FastAPI()

@app.post("/my_workflow")
async def run_workflow():
    flow = MyFlow()
    return await flow.run()
```

## Best Practices

1. **Crew Design**:
   - Give agents clear roles and goals
   - Define structured outputs with Pydantic
   - Keep tasks focused and modular

2. **Flow Management**:
   - Use state for data flow
   - Handle errors gracefully
   - Log important events

3. **API Design**:
   - Validate inputs
   - Return clear responses
   - Document endpoints

4. **Testing**:
   - Test crews independently
   - Test full flow execution
   - Test API endpoints

## Example

The `crewai_flow` directory contains a complete example showing:
- Crew implementation with agents and tasks
- Flow state management
- API endpoints
- Error handling
- Testing patterns

Study it to understand the patterns, then adapt them for your use case. 
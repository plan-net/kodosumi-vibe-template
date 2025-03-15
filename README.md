# CrewAI Flow Template with Ray and Kodosumi

This template provides a starting point for creating CrewAI flows that leverage Ray for distributed processing and Kodosumi for serving. It's designed to be simple yet functional, allowing you to quickly set up new CrewAI flows for different use cases.

## Structure

```
template/
├── pyproject.toml            # Project configuration and dependencies
├── config.yaml               # Kodosumi configuration file
├── requirements.txt          # Legacy Python dependencies (for compatibility)
├── .env.example              # Example environment variables
├── .cursor.json              # Cursor editor configuration
├── .cursorignore             # Files to ignore in Cursor
├── install.sh                # Installation script for Linux/macOS
├── install.bat               # Installation script for Windows
├── tests/                    # Test directory
│   ├── __init__.py
│   └── test_basic.py
└── workflows/
    └── crewai_flow/
        ├── crews/
        │   └── first_crew/
        │       ├── __init__.py
        │       └── first_crew.py
        ├── templates/
        │   ├── _base.html
        │   └── form.html
        ├── tools/
        │   ├── __init__.py
        │   └── example_tool.py
        ├── __init__.py
        ├── main.py
        └── serve.py
```

## Components

- **pyproject.toml**: Modern Python project configuration with dependencies, build settings, and development tools.
- **config.yaml**: Kodosumi configuration file for deploying the flow.
- **main.py**: The main flow definition using CrewAI's Flow class with Ray integration for distributed processing.
- **serve.py**: A FastAPI-based web service for the flow, using Ray Serve for deployment.
- **crews/**: Directory containing crew definitions.
- **templates/**: HTML templates for the web interface.
- **tools/**: Directory for custom tools used by the crews.
- **tests/**: Directory containing tests for the project.
- **.cursor.json**: Configuration for the Cursor editor with custom snippets and settings.
- **.cursorignore**: Specifies files and directories to be ignored by Cursor.
- **install.sh**: Installation script for Linux/macOS.
- **install.bat**: Installation script for Windows.

## How to Use

1. **Clone the Template**: Copy the template directory to create a new project.
2. **Configure Project**: Update the `pyproject.toml` file with your project details and dependencies.
3. **Configure Kodosumi**: Update the `config.yaml` file with your API keys and other settings.
4. **Rename Components**: Rename the `crewai_flow` directory and update imports accordingly.
5. **Define Your Flow**: Modify `main.py` to define your flow steps and state.
6. **Create Crews**: Add your crew definitions in the `crews/` directory.
7. **Update the Web Interface**: Modify the HTML templates and `serve.py` to match your flow's parameters.

## Installation

### Using Installation Scripts (Recommended)

#### Linux/macOS

```bash
# Make the script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

#### Windows

```bash
# Run the installation script
install.bat
```

These scripts will:
1. Create a virtual environment
2. Install the project in development mode
3. Install development dependencies
4. Install Kodosumi from GitHub (dev branch)
5. Create a .env file from .env.example if it doesn't exist

### Using pip (Manual)

```bash
# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install Kodosumi from GitHub (dev branch)
pip install git+https://github.com/masumi-network/kodosumi.git@dev
```

### Using requirements.txt (Legacy)

```bash
pip install -r requirements.txt
```

### Manual Kodosumi Installation

If you need more control over the Kodosumi installation:

```bash
# Clone the Kodosumi repository
git clone https://github.com/masumi-network/kodosumi.git

# Change to the Kodosumi directory
cd kodosumi

# Checkout the dev branch
git checkout dev

# Install in development mode
pip install -e .

# Return to your project directory
cd ..
```

## Running the Flow

### Local Execution

To run the flow locally:

```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run with default parameters
python -m workflows.crewai_flow.main

# Run with custom parameters
python -m workflows.crewai_flow.main input_param1=value1 input_param2=value2
```

When running locally, the flow will:
1. Initialize a local Ray instance or connect to an existing Ray cluster (if RAY_ADDRESS is set)
2. Execute the flow with the provided parameters
3. Shut down Ray when finished

### Kodosumi Deployment

To deploy the flow with Kodosumi:

```bash
# Ensure Kodosumi is installed from GitHub
pip install git+https://github.com/masumi-network/kodosumi.git@dev

# Deploy the flow
kodosumi deploy
```

When deployed with Kodosumi:
1. Kodosumi handles Ray initialization and management
2. The flow is accessible via the configured route prefix (e.g., `/crewai_flow`)
3. The web interface allows users to input parameters and execute the flow

## Ray Integration and Scaling

This template demonstrates several patterns for distributed processing with Ray:

### 1. Remote Execution of CrewAI Crews

```python
# Run a CrewAI crew on a Ray worker
result_ref = ray.remote(FirstCrew().crew().kickoff).remote(
    inputs={"param1": "value1", "param2": "value2"}
)
result = ray.get(result_ref)
```

### 2. Parallel Processing of Multiple Items

```python
# Define a remote function
@ray.remote
def process_item(item):
    # Process the item
    return {"processed_item": item, "status": "processed"}

# Process multiple items in parallel
items = ["item1", "item2", "item3", "item4", "item5"]
process_tasks = [process_item.remote(item) for item in items]
processed_results = ray.get(process_tasks)
```

### 3. Resource-Specific Tasks

```python
# Request specific resources for a task
@ray.remote(num_cpus=1)
def complex_processing_task(data, config):
    # Perform complex processing
    return {"result": f"Processed {data} with {config}"}
```

### 4. Task Dependencies and Aggregation

```python
# Create processing tasks
processing_refs = [complex_processing_task.remote(data, config) 
                  for data, config in zip(data_items, configs)]

# Wait for processing tasks to complete
processing_results = ray.get(processing_refs)

# Create an aggregation task that depends on the processing results
aggregation_ref = aggregation_task.remote(processing_results)
aggregation_result = ray.get(aggregation_ref)
```

### Scaling Considerations

- **Worker Resources**: Use the `num_cpus`, `num_gpus`, and `resources` parameters to specify resource requirements for tasks.
- **Task Dependencies**: Create complex workflows by passing references between tasks.
- **Cluster Configuration**: Configure your Ray cluster based on your workload requirements.
- **Monitoring**: Use the Ray dashboard to monitor task execution and resource utilization.

## Kodosumi Configuration

The `config.yaml` file contains the configuration for Kodosumi:

- **proxy_location**: Specifies where the proxy should run.
- **http_options**: HTTP server configuration.
- **grpc_options**: gRPC server configuration.
- **logging_config**: Logging configuration.
- **applications**: List of applications to deploy.
  - **name**: Application name.
  - **route_prefix**: URL prefix for the application.
  - **import_path**: Path to the application's entry point.
  - **runtime_env**: Environment configuration for the application.
    - **env_vars**: Environment variables.
    - **pip**: Python dependencies.

## Example

The template includes a comprehensive example with multiple steps:

1. **Step 1**: Executes a CrewAI crew task using Ray remote execution.
2. **Step 2**: Demonstrates parallel processing of multiple items using Ray.
3. **Step 3**: Shows advanced parallel processing patterns, including:
   - Resource-specific tasks
   - Task dependencies
   - Result aggregation
4. **Step 4**: Aggregates results from previous steps and executes a final CrewAI crew task.

## Requirements

- Python 3.8+
- CrewAI
- Ray
- FastAPI
- Kodosumi

## License

[Your License]

## Development Tools

### Cursor Editor Integration

This template includes configuration for the [Cursor](https://cursor.sh/) editor, which provides AI-powered coding assistance:

- `.cursor.json`: Configuration file for Cursor with:
  - Code formatting with Black and isort
  - Linting with Ruff and mypy
  - Custom snippets for Ray and CrewAI
  - AI assistant settings optimized for this project
  - **AI preferences** that guide the assistant to always use Ray and Kodosumi

- `.cursorignore`: Specifies files and directories to be ignored by Cursor

#### AI Assistant Preferences

The Cursor AI assistant is configured with preferences that guide it to:

- Always use Ray for distributed processing instead of threading or multiprocessing
- Always use CrewAI for agent-based workflows
- Always use Kodosumi for serving and deployment
- Always use exa.ai for web search in CrewAI applications
- Follow best practices for Ray's remote functions and actor model
- Implement CrewAI crews for complex AI agent tasks
- Use Kodosumi's deployment patterns for serving

#### Custom Snippets

The following custom snippets are available in Python files:

- `rayremote`: Create a Ray remote function
- `rayremoteclass`: Create a Ray remote class
- `rayinit`: Initialize Ray or connect to an existing cluster
- `crewaiagent`: Create a CrewAI Agent
- `crewaitask`: Create a CrewAI Task
- `kodosumiapp`: Create a Kodosumi service with FastAPI
- `exasearch`: Create an Exa.ai web search tool for CrewAI

### Code Quality Tools

The template is configured with several code quality tools:

- **Black**: Code formatter
- **isort**: Import sorter
- **Ruff**: Fast Python linter
- **mypy**: Static type checker

These tools are configured in `pyproject.toml` and can be run manually or automatically through Cursor. 
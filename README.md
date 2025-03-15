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
├── .cursorrules              # Cursor AI assistant configuration
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
- **.cursorrules**: Configuration for the Cursor AI assistant with rules and guidelines.
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

### Important Note About Kodosumi

**Kodosumi is not available on PyPI** and must be installed directly from GitHub:

```bash
pip install git+https://github.com/masumi-network/kodosumi.git@dev
```

The installation scripts handle this automatically, but if you're installing manually, you'll need to run this command separately.

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

# Start a local Ray cluster (if not already running)
ray start --head

# Run with default parameters
python -m workflows.crewai_flow.main

# Run with custom parameters
python -m workflows.crewai_flow.main dataset_name=customer_feedback output_format=json
```

When running locally, the flow will:
1. Connect to the local Ray cluster or initialize a new one if needed
2. Execute the flow with the provided parameters
3. Shut down Ray when finished (if it was initialized by the flow)

### Kodosumi Deployment

To deploy the flow with Kodosumi, follow these steps:

```bash
# 1. Ensure Kodosumi is installed from GitHub
pip install git+https://github.com/masumi-network/kodosumi.git@dev

# 2. Start a local Ray cluster (if not already running)
ray start --head

# 3. Start Kodosumi spooler
python -m kodosumi.cli spool

# 4. Update config.yaml with your workflow configuration
# See the example config.yaml in this repository

# 5. Deploy with Ray Serve
serve deploy ./config.yaml

# 6. Start Kodosumi services
python -m kodosumi.cli serve

# 7. Access the service at http://localhost:3370
```

When deployed with Kodosumi:
1. Ray is used for distributed processing
2. The Kodosumi spooler handles background tasks
3. The flow is accessible via the configured route prefix (e.g., `/crewai_flow`)
4. The web interface allows users to input parameters and execute the flow

## Output Format Options

This template supports two output formats for all flows:

### Markdown Format (Default)

The Markdown format is designed for human readability and includes:
- Formatted headers for sections
- Bulleted lists for insights and recommendations
- Emphasis on important information
- Timestamp and metadata

This format is ideal for:
- Displaying results in the Kodosumi UI
- Generating reports for human consumption
- Documentation and sharing results

### JSON Format

The JSON format is designed for machine readability and agent-to-agent interactions:
- Structured data in a standard format
- Easy to parse and process programmatically
- Contains all the same information as the Markdown format

This format is ideal for:
- AI agent-to-agent interactions
- Programmatic processing of results
- Integration with other systems and APIs

### Specifying the Output Format

You can specify the output format in several ways:

#### In the Web Interface

Select the output format from the dropdown menu in the web interface.

#### In Local Execution

```bash
# Run with JSON output format
python -m workflows.crewai_flow.main output_format=json

# Run with Markdown output format (default)
python -m workflows.crewai_flow.main output_format=markdown
```

#### In Programmatic Usage

```python
from workflows.crewai_flow.main import kickoff
import asyncio

# Request JSON format
result = asyncio.run(kickoff({"output_format": "json"}))

# Request Markdown format
result = asyncio.run(kickoff({"output_format": "markdown"}))
```

#### In API Requests

```bash
# Request JSON format
curl -X POST "http://localhost:8001/crewai_flow/" -d "output_format=json"

# Request Markdown format
curl -X POST "http://localhost:8001/crewai_flow/" -d "output_format=markdown"
```

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

```yaml
# Example config.yaml for Kodosumi deployment

proxy_location: EveryNode
http_options:
  host: 127.0.0.1
  port: 8001
grpc_options:
  port: 9001
  grpc_servicer_functions: []
logging_config:
  encoding: TEXT
  log_level: DEBUG
  logs_dir: null
  enable_access_log: true
applications:
- name: crewai_flow
  route_prefix: /crewai_flow
  import_path: workflows.crewai_flow.serve:fast_app
  runtime_env:
    env_vars:
      PYTHONPATH: .
      OPENAI_API_KEY: your_openai_api_key_here
      EXA_API_KEY: your_exa_api_key_here
      OTEL_SDK_DISABLED: "true"
    pip:
    - crewai==0.86.*
    - crewai_tools==0.17.*
```

### Configuration Options

- **proxy_location**: Specifies where the proxy should run (usually `EveryNode`).
- **http_options**: HTTP server configuration.
  - **host**: The host to bind to (usually `127.0.0.1` for local development).
  - **port**: The port to bind to (default is `8001`).
- **grpc_options**: gRPC server configuration.
  - **port**: The port for gRPC (default is `9001`).
- **logging_config**: Logging configuration.
  - **encoding**: Log encoding format (usually `TEXT`).
  - **log_level**: Log level (e.g., `DEBUG`, `INFO`).
  - **enable_access_log**: Whether to enable access logs.
- **applications**: List of applications to deploy.
  - **name**: Application name (used for identification).
  - **route_prefix**: URL prefix for the application (e.g., `/crewai_flow`).
  - **import_path**: Python import path to the application (must end with `:fast_app`).
  - **runtime_env**: Environment configuration for the application.
    - **env_vars**: Environment variables to set.
      - **PYTHONPATH**: Path to add to Python's module search path.
      - **OPENAI_API_KEY**: Your OpenAI API key.
      - **EXA_API_KEY**: Your Exa.ai API key (if using web search).
      - **OTEL_SDK_DISABLED**: Disable OpenTelemetry SDK (usually set to `"true"`).
    - **pip**: Additional pip packages to install in the runtime environment.

### Multiple Applications

You can deploy multiple applications in the same config.yaml file:

```yaml
applications:
- name: crewai_flow
  route_prefix: /crewai_flow
  import_path: workflows.crewai_flow.serve:fast_app
  runtime_env:
    # ... configuration for crewai_flow ...

- name: another_flow
  route_prefix: /another_flow
  import_path: workflows.another_flow.serve:fast_app
  runtime_env:
    # ... configuration for another_flow ...
```

Each application will be accessible at its own route prefix.

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

- `.cursorrules`: Configuration file for Cursor's AI assistant with:
  - Rules for handling output formats
  - Deployment workflow guidance
  - Framework preferences and patterns
  - Context files for better AI understanding

- `.cursorignore`: Specifies files and directories to be ignored by Cursor

#### Cursor Configuration Files

The template uses two separate configuration files for Cursor:

1. **`.cursor.json`**: Controls editor behavior like formatting, linting, and snippets.
   - This file is used by the Cursor editor itself
   - Contains settings for code formatters, linters, and snippets
   - Does not contain AI guidance

2. **`.cursorrules`**: Guides the AI assistant's behavior.
   - This file is used by the Cursor AI assistant
   - Contains rules, patterns, and guidelines for AI recommendations
   - Includes our output format rules and deployment workflow

#### Custom Snippets

The following custom snippets are available in Python files:

- `rayremote`: Create a Ray remote function
- `rayremoteclass`: Create a Ray remote class
- `rayinit`: Initialize Ray or connect to an existing cluster
- `crewaiflow`: Create a CrewAI Flow with output format support
- `crewaiagent`: Create a CrewAI Agent
- `crewaitask`: Create a CrewAI Task
- `kodosumiapp`: Create a Kodosumi service with ServeAPI
- `outputformat`: Handle output format in a Kodosumi service
- `kodomsumitest`: Commands for deploying and testing with Kodosumi
- `localtestmain`: Create a main block for local testing with Ray
- `exasearch`: Create an Exa.ai web search tool for CrewAI
- `rayserveconfig`: Create a Ray Serve config.yaml file

### Code Quality Tools

The template is configured with several code quality tools:

- **Black**: Code formatter
- **isort**: Import sorter
- **Ruff**: Fast Python linter
- **mypy**: Static type checker

These tools are configured in `pyproject.toml` and can be run manually or automatically through Cursor.

## Development and Testing Workflow

This template follows a specific development and testing workflow to ensure that flows work correctly in both local and Kodosumi environments:

### 1. Local Development with Ray

Start by developing and testing your flow locally with Ray:

```bash
# Start a local Ray cluster
ray start --head

# Run the flow directly
python -m workflows.crewai_flow.main
```

This allows you to quickly iterate on your flow without deploying to Kodosumi.

### 2. Local Kodosumi Testing

Once your flow works locally, test it with a local Kodosumi deployment:

```bash
# Ensure Ray is running
ray status

# Start Kodosumi spooler
python -m kodosumi.cli spool

# Deploy with Ray Serve
serve deploy ./config.yaml

# Start Kodosumi services
python -m kodosumi.cli serve
```

Access your flow at http://localhost:3370 and test it through the Kodosumi UI.

### 3. Production Deployment

After testing locally, you can deploy to a production Kodosumi environment:

```bash
# Update production config.yaml with appropriate settings
# Deploy to production Ray Serve instance
serve deploy ./production_config.yaml
```

### Testing Both Output Formats

At each stage, test both output formats to ensure they work correctly:

```bash
# Test markdown output (default)
python -m workflows.crewai_flow.main output_format=markdown

# Test JSON output
python -m workflows.crewai_flow.main output_format=json
```

In the Kodosumi UI, use the output format dropdown to test both formats.

### Error Handling

Ensure your flow includes proper error handling for:

- Ray cluster connection failures
- Invalid input parameters
- API key issues
- Output format validation

This will make your flow more robust in both local and Kodosumi environments. 
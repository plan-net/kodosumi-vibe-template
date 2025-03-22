# Kodosumi Vibe Template

A template for building AI workflows with CrewAI and Kodosumi.

## Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/plan-net/kodosumi-vibe-template.git
   cd kodosumi-vibe-template
   ```

2. **Run Installation Script**
   ```bash
   # On Unix/macOS
   chmod +x install.sh
   ./install.sh

   # On Windows
   install.bat
   ```

   This will:
   - Create and activate a virtual environment
   - Install all dependencies
   - Set up the initial configuration
   - Create a .env file for your environment variables

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other settings
   ```

4. **Run Example Flow**
   ```bash
   # Run the example flow directly
   python -m workflows.example.main

   # Or run with test data
   python -m workflows.example.main --dataset example_data
   ```

   For Kodosumi deployment, see the [Deployment Guide](docs/deployment.md).

## Features

- 🤖 AI-powered workflows with CrewAI
- 🚀 Easy deployment with Kodosumi
- 📊 Web interface for workflow management
- 🔧 Extensible and customizable
- 📈 Distributed computing with Ray

## Ray Examples

The repository includes example scripts that demonstrate how to use Ray for distributed computing in the Kodosumi framework:

### Available Examples

- **Basic Remote Functions**: Simple Ray tasks and remote execution
- **Parallel Processing**: The pattern used in workflow's `process_insights_in_parallel` method
- **Actor Model**: Stateful processing with specialized worker instances

### Running Examples

```bash
# Run all examples
python examples/ray/run_all_examples.py

# Run specific examples
python examples/ray/run_all_examples.py basic     # Just basic remote functions
python examples/ray/run_all_examples.py parallel  # Parallel processing
python examples/ray/run_all_examples.py actor     # Actor model
```

These examples serve as learning resources and documentation of recommended Ray patterns. For more details, see the [examples/ray/README.md](examples/ray/README.md) file.

## Recommended MCP Servers

- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github) - For repository management, file operations, and GitHub features
- [Model Context Protocol](https://github.com/modelcontextprotocol/servers) - Main MCP servers collection

## Development with Cursor

This template includes specialized Cursor rules that provide AI-assisted development following test-driven development best practices.

### Key Principles

- Test-driven development with pytest
- Step-by-step feature development
- Comprehensive testing at multiple levels:
  - Single crew tests
  - Main flow tests
  - Service application tests
- Bug fixes include test adjustments

### Available Rules

- **General**: Test-driven development practices and overall guidelines
- **Installation**: Environment setup and dependency management
- **Crews**: Guidelines for developing individual CrewAI crews
- **Flow**: Best practices for implementing CrewAI flows
- **HTML**: Standards for creating web interfaces
- **Testing**: Test execution and validation
- **Kodosumi**: Integration with Kodosumi services
- **Frameworks**: Preferred frameworks and their usage
- **Workflows**: Guidelines for creating new workflow packages

### Using Cursor Rules

1. Open the project in Cursor
2. Access context-aware assistance based on file type
3. Follow test-driven development workflow:
   - Write tests first
   - Implement features against tests
   - Validate with test suite
   - Update documentation

## Documentation

### Getting Started
- [Installation Guide](docs/installation.md)
- [Deployment Guide](docs/deployment.md)

### Development
- [Development Guide](docs/development/guide.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

### Reference
- [CrewAI Flow Components](docs/reference/crewai_flow.md)
- [Common Utilities](docs/reference/common_utilities.md)
- [Ray Documentation](docs/ray/overview.md)

## Project Structure

```
workflows/
├── common/              # Shared utilities
│   ├── formatters.py    # Output formatting utilities
│   ├── processors.py    # Data processing utilities
│   ├── static/          # Shared static files (CSS, JS, images)
│   └── utils.py         # General utilities  
├── example/            # Example CrewAI flow
│   ├── agents/         # Agent definitions
│   ├── crews/          # Crew definitions
│   ├── tasks/          # Task definitions
│   ├── tools/          # Tool definitions
│   ├── templates/      # Web interface
│   ├── static/         # Workflow-specific static files
│   ├── main.py         # Flow implementation
│   └── serve.py        # Kodosumi service
└── another_flow/       # Your custom flow
```

## Creating a Workflow

1. Create a new directory in `workflows/`
   ```bash
   mkdir -p workflows/my_workflow/{agents,crews,tasks,tools,templates}
   touch workflows/my_workflow/{__init__.py,main.py,serve.py}
   ```

2. Create corresponding test directory
   ```bash
   mkdir -p tests/workflows/my_workflow
   touch tests/workflows/my_workflow/{__init__.py,test_basic.py}
   ```

3. Define your flow state and steps in `main.py`
   ```python
   from crewai.flow import Flow, listen, start
   
   class MyWorkflowState(BaseModel):
       # Your flow state here
       pass
   
   class MyWorkflow(Flow[MyWorkflowState]):
       # Your flow implementation here
       pass
   ```

4. Create a Kodosumi service in `serve.py`
   ```python
   from kodosumi.serve import Launch, ServeAPI
   
   app = ServeAPI()
   
   @deployment
   @ingress(app)
   class MyWorkflowService:
       # Your service implementation here
       pass
   ```

5. Add your workflow to `config.yaml`
   ```yaml
   applications:
   - name: my_workflow
     route_prefix: /my_workflow
     import_path: workflows.my_workflow.serve:fast_app
     runtime_env:
       env_vars:
         PYTHONPATH: .
         OPENAI_API_KEY: ${OPENAI_API_KEY}
   ```

Follow the structure of the example workflow in `workflows/example/` for best practices. See the [Development Guide](docs/development/guide.md) for detailed instructions.

## Deployment

1. Configure your workflow in `config.yaml`
2. Start Kodosumi services:
   ```bash
   python -m kodosumi.cli spool
   serve deploy config.yaml
   python -m kodosumi.cli serve --register http://localhost:8001/-/routes
   ```

See the [Deployment Guide](docs/deployment.md) for more details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
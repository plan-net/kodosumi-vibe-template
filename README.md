# CrewAI Flow Template

A template for building AI workflows with CrewAI and Kodosumi.

## Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/kodosumi/crewai-flow-template.git
   cd crewai-flow-template
   ```

2. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

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

## Development with Cursor

This template includes specialized Cursor rules that provide AI-assisted development:

### Available Rules

- **Crews**: Guidelines for developing individual CrewAI crews
- **Flow**: Best practices for implementing CrewAI flows
- **Frameworks**: Preferred frameworks and their usage
- **HTML**: Standards for creating web interfaces
- **Installation**: Environment setup and dependency management
- **Kodosumi**: Integration with Kodosumi services
- **Testing**: Test-driven development practices

### Using Cursor Rules

1. Open the project in Cursor
2. Access context-aware assistance based on file type
3. Get AI suggestions for:
   - Creating agents and tasks
   - Implementing flows
   - Writing tests
   - Debugging issues
   - Deploying services

### Key Benefits

- Test-driven development guidance
- Framework-specific best practices
- Error handling patterns
- Resource management tips
- Integration examples

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

## Project Structure

```
workflows/
├── common/              # Shared utilities
├── example/            # Example CrewAI flow
│   ├── agents/         # Agent definitions
│   ├── crews/          # Crew definitions
│   ├── tasks/          # Task definitions
│   ├── tools/          # Tool definitions
│   ├── templates/      # Web interface
│   ├── main.py         # Flow implementation
│   └── serve.py        # Kodosumi service
└── another_flow/       # Your custom flow
```

## Creating a Workflow

1. Create a new directory in `workflows/`
2. Define your flow state and steps in `main.py`
3. Create a Kodosumi service in `serve.py`
4. Add your workflow to `config.yaml`

See the [Development Guide](docs/development/guide.md) for detailed instructions.

## Deployment

1. Configure your workflow in `config.yaml`
2. Start Kodosumi services:
   ```bash
   python -m kodosumi.cli spool
   serve deploy config.yaml
   python -m kodosumi.cli serve
   ```

See the [Deployment Guide](docs/deployment.md) for more details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
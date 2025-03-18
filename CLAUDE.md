# Development Guidelines for Claude

## Build & Test Commands
- Install dependencies: `pip install -e ".[dev]"`
- Install Kodosumi: `pip install git+https://github.com/masumi-network/kodosumi.git@dev`
- Run all tests: `pytest`
- Run specific test: `pytest tests/path/to/test_file.py::TestClass::test_function`
- Test with coverage: `pytest --cov=workflows`
- Lint code: `ruff check .`
- Format code: `black . && isort .`
- Type check: `mypy workflows tests`

## Code Style Guidelines
- Python version: 3.12.2
- Line length: 88 characters (Black/PEP8)
- Use type hints and Pydantic models for data validation
- Test-driven development: write tests first, then implement features
- CrewAI crews in dedicated modules under `crews/` directory
- Use YAML for agent and task configurations
- Organize imports with isort (profile=black)
- Use descriptive function and variable names
- Group related tests in classes with `Test` prefix
- Mock LLM calls in tests to avoid API costs

## Workflow Structure
- Mirror project structure in test directory
- New workflows require tests, HTML templates, and serve.py setup
- Update config.yaml when adding new workflows
- Use Ray for parallel processing when appropriate
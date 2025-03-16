# Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues when working with the Kodosumi Vibe Template and Kodosumi.

## Installation Issues

### Python Version Mismatch

**Problem**: Error about Python version requirements.

**Solution**:
1. Check your Python version:
   ```bash
   python --version
   ```
2. Install Python 3.12.2:
   - macOS: `brew install python@3.12`
   - Linux: `sudo apt install python3.12`
   - Windows: Download from python.org

3. Create new virtual environment:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

### Kodosumi Installation Fails

**Problem**: Error installing Kodosumi package.

**Solution**:
1. Check GitHub access:
   ```bash
   git clone https://github.com/kodosumi/kodosumi.git
   ```

2. Install in development mode:
   ```bash
   cd kodosumi
   pip install -e .
   ```

3. Check dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Ray Installation Issues

**Problem**: Ray fails to install or initialize.

**Solution**:
1. Install Ray separately:
   ```bash
   pip install "ray[default]"
   ```

2. Check system requirements:
   - Memory: At least 4GB RAM
   - Disk: 1GB free space
   - Ports: 8265, 8000-8999 available

3. Test Ray installation:
   ```bash
   python -c "import ray; ray.init()"
   ```

## Environment Setup

### Missing Environment Variables

**Problem**: `EnvironmentError: Missing required environment variables`

**Solution**:
1. Copy example environment file:
   ```bash
   cp .env.example .env
   ```

2. Set required variables:
   ```bash
   export OPENAI_API_KEY=your_key_here
   export RAY_ADDRESS=auto
   ```

3. Verify variables:
   ```bash
   python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
   ```

### OpenAI API Issues

**Problem**: OpenAI API errors or rate limits.

**Solution**:
1. Verify API key:
   ```python
   import openai
   openai.api_key = "your_key_here"
   openai.Model.list()  # Should return available models
   ```

2. Check rate limits:
   - Review OpenAI dashboard
   - Implement retries
   - Use API key rotation

3. Test with minimal example:
   ```python
   response = openai.ChatCompletion.create(
       model="gpt-4",
       messages=[{"role": "user", "content": "Hello"}]
   )
   ```

## Workflow Execution

### Ray Connection Errors

**Problem**: Cannot connect to Ray cluster.

**Solution**:
1. Check Ray status:
   ```bash
   ray status
   ```

2. Start Ray if needed:
   ```bash
   ray start --head
   ```

3. Verify connection:
   ```python
   from workflows.common.utils import test_ray_connectivity
   assert test_ray_connectivity()
   ```

### Task Execution Failures

**Problem**: Tasks fail or timeout.

**Solution**:
1. Check logs:
   ```bash
   tail -f /tmp/ray/session_*/logs/worker-*.log
   ```

2. Monitor Ray dashboard:
   - Open http://localhost:8265
   - Check resource usage
   - Review error messages

3. Increase timeouts:
   ```python
   ray.init(
       _system_config={
           "task_timeout_seconds": 300
       }
   )
   ```

### Agent Communication Issues

**Problem**: Agents fail to communicate or return unexpected results.

**Solution**:
1. Enable verbose mode:
   ```python
   agent = Agent(
       role="Researcher",
       verbose=True
   )
   ```

2. Check agent configuration:
   - Verify tools are available
   - Review agent goals
   - Check task descriptions

3. Test individual components:
   ```python
   # Test tool
   result = tool.run("test input")
   print(f"Tool output: {result}")
   
   # Test agent
   response = agent.run("test task")
   print(f"Agent response: {response}")
   ```

## Deployment Issues

### Service Not Starting

**Problem**: Kodosumi services fail to start.

**Solution**:
1. Check port availability:
   ```bash
   lsof -i :8001
   lsof -i :3370
   ```

2. Verify configuration:
   ```bash
   serve status
   python -m kodosumi.cli status
   ```

3. Start services in order:
   ```bash
   ray start --head
   python -m kodosumi.cli spool
   serve deploy config.yaml
   python -m kodosumi.cli serve
   ```

### Configuration Errors

**Problem**: Invalid configuration or missing settings.

**Solution**:
1. Validate config file:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. Check required fields:
   - proxy_location
   - http_options
   - applications

3. Test configuration:
   ```bash
   serve run config.yaml --dry-run
   ```

## Performance Issues

### Memory Usage

**Problem**: High memory usage or OOM errors.

**Solution**:
1. Monitor memory:
   ```bash
   top -pid $(pgrep -f "ray")
   ```

2. Adjust Ray resources:
   ```python
   ray.init(
       object_store_memory=2 * 1024 * 1024 * 1024,  # 2GB
       _memory=4 * 1024 * 1024 * 1024  # 4GB
   )
   ```

3. Profile code:
   ```python
   import cProfile
   cProfile.run('workflow.run()')
   ```

### Slow Execution

**Problem**: Workflows take too long to complete.

**Solution**:
1. Enable Ray dashboard:
   ```bash
   ray start --head --dashboard-host=0.0.0.0
   ```

2. Profile tasks:
   ```python
   @ray.remote
   def task():
       import time
       start = time.time()
       # ... task code ...
       print(f"Task took {time.time() - start} seconds")
   ```

3. Optimize resource usage:
   - Adjust batch sizes
   - Implement caching
   - Use parallel execution

## Testing Issues

### Test Failures

**Problem**: Unit or integration tests failing.

**Solution**:
1. Run tests with details:
   ```bash
   python -m pytest tests/ -v --tb=short
   ```

2. Debug specific test:
   ```bash
   python -m pytest tests/test_file.py::test_name -s
   ```

3. Check test environment:
   ```bash
   python -m pytest --setup-show tests/
   ```

### Coverage Issues

**Problem**: Low test coverage or missing tests.

**Solution**:
1. Run coverage report:
   ```bash
   coverage run -m pytest
   coverage report
   ```

2. Generate HTML report:
   ```bash
   coverage html
   # View htmlcov/index.html
   ```

3. Add missing tests:
   ```python
   def test_edge_case():
       # Test edge cases
       pass
   
   def test_error_handling():
       # Test error conditions
       pass
   ```

## Common Error Messages

### "ModuleNotFoundError"

**Problem**: Cannot import module.

**Solution**:
1. Check PYTHONPATH:
   ```bash
   echo $PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. Verify installation:
   ```bash
   pip list | grep module_name
   pip install -e .
   ```

3. Check imports:
   ```python
   import sys
   print(sys.path)
   ```

### "RuntimeError: Ray not initialized"

**Problem**: Ray cluster not running.

**Solution**:
1. Initialize Ray:
   ```python
   import ray
   ray.init(address="auto")
   ```

2. Check cluster:
   ```bash
   ray status
   ```

3. Restart cluster:
   ```bash
   ray stop
   ray start --head
   ```

## Getting Help

1. **Check Logs**:
   - Ray logs: `/tmp/ray/session_*/logs/`
   - Kodosumi logs: Check stdout/stderr
   - Application logs: As configured

2. **Debug Tools**:
   - Ray dashboard
   - Python debugger
   - Logging statements

3. **Support Resources**:
   - [CrewAI Documentation](https://docs.crewai.com/)
   - [Ray Documentation](https://docs.ray.io/)
   - [Kodosumi Documentation](https://docs.kodosumi.com/)
   - GitHub Issues 
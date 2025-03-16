# Kodosumi Deployment Guide

## Overview

This guide explains how to deploy your CrewAI flows using Kodosumi, which provides:
- Web interface for your flows
- API endpoints for programmatic access
- Background task processing
- Resource management with Ray

## Configuration

### Basic Configuration

The `config.yaml` file contains your Kodosumi deployment configuration:

```yaml
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
      OTEL_SDK_DISABLED: "true"
    pip:
    - crewai==0.105.0
```

### Configuration Options

- **proxy_location**: Where the proxy should run (usually `EveryNode`)
- **http_options**: HTTP server configuration
  - **host**: Bind address (use `127.0.0.1` for local, `0.0.0.0` for public)
  - **port**: HTTP port (default: 8001)
- **grpc_options**: gRPC server settings
- **logging_config**: Logging settings
- **applications**: List of flows to deploy

### Multiple Applications

Deploy multiple flows in one configuration:

```yaml
applications:
- name: crewai_flow
  route_prefix: /crewai_flow
  import_path: workflows.crewai_flow.serve:fast_app
  # ... configuration for crewai_flow ...

- name: another_flow
  route_prefix: /another_flow
  import_path: workflows.another_flow.serve:fast_app
  # ... configuration for another_flow ...
```

## Deployment Steps

### 1. Local Deployment

```bash
# Start Ray cluster (if not running)
ray start --head

# Start Kodosumi spooler
python -m kodosumi.cli spool

# Deploy with Ray Serve
serve deploy ./config.yaml

# Start Kodosumi services
python -m kodosumi.cli serve

# Access at http://localhost:3370
```

### 2. Production Deployment

1. **Prepare Configuration**
   - Create `production_config.yaml`
   - Set appropriate host/ports
   - Configure SSL if needed
   - Set production API keys

2. **Deploy**
   ```bash
   # Deploy to production Ray cluster
   serve deploy ./production_config.yaml
   ```

3. **Monitor**
   - Check Ray dashboard
   - Monitor logs
   - Set up health checks

## Web Interface

Your flows will be available at:
- Local: `http://localhost:3370/crewai_flow`
- Production: `https://your-domain.com/crewai_flow`

### Features
- Parameter input forms
- Output format selection
- Task status monitoring
- Result display

## API Access

### REST API

```bash
# Get flow status
curl http://localhost:8001/crewai_flow/status

# Run flow with parameters
curl -X POST http://localhost:8001/crewai_flow/ \
  -H "Content-Type: application/json" \
  -d '{"dataset_name": "customer_feedback", "output_format": "json"}'
```

### Python Client

```python
import requests

# Run flow
response = requests.post(
    "http://localhost:8001/crewai_flow/",
    json={
        "dataset_name": "customer_feedback",
        "output_format": "json"
    }
)
result = response.json()
```

## Monitoring and Maintenance

### Health Checks

Monitor your deployment with:
```bash
# Check Ray cluster
ray status

# Check Kodosumi services
python -m kodosumi.cli status

# Check application health
curl http://localhost:8001/health
```

### Logs

Access logs in several ways:
1. Kodosumi service logs
2. Ray dashboard logs
3. Application-specific logs

### Updates

To update your deployment:
1. Stop the service
2. Deploy new version
3. Start the service
4. Verify functionality

## Troubleshooting

### Common Issues

1. **Service Not Starting**
   - Check Ray cluster status
   - Verify port availability
   - Check log files

2. **Flow Errors**
   - Check API keys
   - Verify Ray resources
   - Check application logs

3. **Performance Issues**
   - Monitor Ray dashboard
   - Check resource utilization
   - Consider scaling resources

For more details, see our [troubleshooting guide](troubleshooting.md). 
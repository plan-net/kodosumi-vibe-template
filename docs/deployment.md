# Deployment Guide

This guide explains how to deploy your CrewAI flows using Kodosumi, which provides:
- Web interface for your flows
- API endpoints for programmatic access
- Background task processing
- Resource management with Ray

## Ray Testing Before Deployment

Before deploying your workflows to Kodosumi, it's important to test them locally with Ray. The repository includes Ray example scripts that demonstrate key patterns used in Kodosumi:

```bash
# Run all Ray examples
python examples/ray/run_all_examples.py
```

These examples help you understand:
- How Ray remote functions work
- How parallel processing is implemented
- How to maintain state with Ray Actors

Testing with Ray locally ensures your workflows will run properly when deployed. See [examples/ray/README.md](../examples/ray/README.md) for more information.

## Configuration

Create a `config.yaml` file in your project root:

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
- name: example
  route_prefix: /example
  import_path: workflows.example.serve:fast_app
  runtime_env:
    env_vars:
      PYTHONPATH: .
      OPENAI_API_KEY: ${OPENAI_API_KEY}
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
- name: example
  route_prefix: /example
  import_path: workflows.example.serve:fast_app
  # ... configuration for example ...

- name: another_flow
  route_prefix: /another_flow
  import_path: workflows.another_flow.serve:fast_app
  # ... configuration for another_flow ...
```

## Deployment Steps

1. **Start Ray**
   ```bash
   ray start --head
   ```

2. **Start Kodosumi Spooler**
   ```bash
   python -m kodosumi.cli spool
   ```

3. **Deploy Your Flow**
   ```bash
   serve deploy config.yaml
   ```

4. **Start Kodosumi Server**
   ```bash
   python -m kodosumi.cli serve --register http://localhost:8001/-/routes
   ```

   The `--register` parameter is required to properly connect the Kodosumi web interface with your Ray Serve application routes.

## Monitoring

Check the status of your deployment:
```bash
serve status
```

View logs:
```bash
serve logs example
```

## API Access

Check status:
```bash
curl http://localhost:8001/example/status
```

Run flow:
```bash
curl -X POST http://localhost:8001/example/ \
  -H "Content-Type: application/json" \
  -d '{"datasets": ["example_data"]}'
```

Python client:
```python
import requests

response = requests.post(
    "http://localhost:8001/example/",
    json={"datasets": ["example_data"]}
)
print(response.json())
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
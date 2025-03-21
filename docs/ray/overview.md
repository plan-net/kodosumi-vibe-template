# Ray in Kodosumi

Ray provides the distributed computing foundation for Kodosumi workflows, enabling parallel processing, state management, and scalable agent execution.

## Core Concepts

### Remote Functions

Remote functions are the basic building blocks of Ray applications:

```python
import ray

@ray.remote
def process_data(data):
    # Process data on a worker node
    return processed_result
```

When called with `.remote()`, execution happens on a worker node:

```python
result_ref = process_data.remote(some_data)
result = ray.get(result_ref)  # Retrieve the result
```

### Parallel Processing

For batch operations, submit multiple tasks concurrently:

```python
# Submit multiple tasks in parallel
refs = [process_data.remote(item) for item in data_items]
# Get all results
results = ray.get(refs)
```

This pattern is used in the `process_insights_in_parallel` method in workflows.

### Actors

Actors provide stateful computation:

```python
@ray.remote
class Worker:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.processed_count = 0
        
    def process(self, data):
        self.processed_count += 1
        return f"Worker {self.worker_id} processed: {data}"
        
    def get_stats(self):
        return {"worker_id": self.worker_id, "processed": self.processed_count}
```

Create and use actors:

```python
# Create actor instances
workers = [Worker.remote(i) for i in range(3)]

# Distribute tasks to actors
task_refs = [worker.process.remote(f"task-{i}") for i, worker in enumerate(workers)]

# Get all results
results = ray.get(task_refs)

# Get stats from each worker
stats = ray.get([worker.get_stats.remote() for worker in workers])
```

## Integration in Kodosumi Workflows

### Initialization and Cleanup

The template handles Ray initialization:

```python
from workflows.common.utils import initialize_ray, shutdown_ray

# Check if running in Kodosumi
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"

# Initialize Ray (Kodosumi handles this in production)
initialize_ray(is_kodosumi)

try:
    # Your workflow code here
    # ...
finally:
    # Shutdown Ray (Kodosumi handles this in production)
    shutdown_ray(is_kodosumi)
```

### Workflow Patterns

#### Parallel Insight Processing

The parallel processing pattern in `process_insights_in_parallel` distributes insight processing:

```python
@ray.remote
def process_insight(insight, model_name=None):
    # Process a single insight
    # ...
    return processed_insight

def process_insights_in_parallel(self):
    # ...
    refs = [process_insight.remote(insight) for insight in insights]
    results = ray.get(refs)
    # ...
```

#### Crew Execution

CrewAI agents can be executed in parallel using Ray:

```python
@ray.remote
def execute_agent_task(agent, task):
    return agent.execute(task)

# Execute tasks in parallel
refs = [execute_agent_task.remote(agent, task) 
        for agent, task in agent_task_pairs]
results = ray.get(refs)
```

## Example Scripts

The repository includes example scripts in `examples/ray/` that demonstrate Ray patterns:

### Basic Ray (`ray_test.py`)

Demonstrates:
- Ray initialization
- Remote function execution
- Basic parallelism

### Parallel Processing (`ray_parallel_test.py`)

Demonstrates:
- Concurrent task submission
- Performance comparison (serial vs. parallel)
- Result prioritization

### Actor Model (`ray_actor_model.py`)

Demonstrates:
- Stateful processing
- Specialized workers
- Context-aware routing

### Running Examples

```bash
# Run all examples
python examples/ray/run_all_examples.py

# Run specific examples
python examples/ray/run_all_examples.py basic     # Just the basic example
python examples/ray/run_all_examples.py parallel  # Parallel processing
python examples/ray/run_all_examples.py actor     # Actor model
```

## Best Practices

### Resource Management

Specify resource requirements for complex operations:

```python
@ray.remote(num_cpus=2, num_gpus=0.5)
def resource_intensive_task(data):
    # ...
```

### Error Handling

Handle failures with proper error handling:

```python
try:
    results = ray.get(refs)
except Exception as e:
    # Handle the error
    logging.error(f"Error during parallel processing: {e}")
```

### Monitoring

Monitor Ray clusters using the Ray dashboard:

```bash
# Start Ray with dashboard
ray start --head --dashboard-host=0.0.0.0
```

Access the dashboard at `http://localhost:8265`.

## Local Testing vs Production

For local development, Ray runs in a single machine with multiple processes:

```python
# For local development
ray.init()
```

In Kodosumi, Ray is configured for distributed execution across the cluster:

```python
# Kodosumi handles this in production
ray.init(address="auto")
```

Use the example scripts to test and validate Ray functionality before deployment. 
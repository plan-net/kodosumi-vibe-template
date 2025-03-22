# Ray Testing Workflow

This workflow provides a Kodosumi application to test various Ray features and patterns in a controlled environment. It's designed to help debug issues with Ray actors and better understand Ray's behavior in different scenarios.

## Features

- Run different Ray tests with a simple web interface
- See detailed markdown output of test execution
- Compare performance between parallel and sequential processing
- Test Ray's actor model for stateful processing

## Available Tests

1. **Basic Test**: Simple Ray tasks and remote functions
2. **Parallel Test**: Process data in parallel with Ray workers
3. **Actor Test**: Stateful processing with Ray actors

## Purpose

This workflow serves as a diagnostic tool for identifying issues with Ray in the Kodosumi environment, particularly focused on:

- Actor lifecycle and potential crashes
- Async execution patterns
- Performance characteristics
- State management

## Usage

1. Select your desired test from the dropdown menu
2. Click "Run Test" to execute
3. View the real-time execution via markdown updates
4. Analyze the final results to understand Ray's behavior

## Development

This workflow is designed to be extended with additional tests to debug specific Ray features or issues as needed.

To add a new test:
1. Add a new test function to `ray_tests.py`
2. Update the `test_functions` dictionary in `main.py` to include the new test
3. Add a new option in the form selection in `serve.py` 